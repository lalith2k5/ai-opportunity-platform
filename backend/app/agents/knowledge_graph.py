import networkx as nx
from app.database import SessionLocal
from app import models
from app.logger import logger


# Type specificity ranking — higher number = more specific.
# Used to decide when a generic node (Keyword, Document) should be
# promoted to a specific type (Technology, Article, ResearchPaper).
_TYPE_RANK = {
    "unknown": 0,
    "Keyword": 1,
    "Document": 2,
    "Article": 3,
    "ResearchPaper": 3,
    "Repository": 3,
    "Industry": 3,
    "Author": 3,
    "Technology": 3,
    "Problem": 3,
    "RDLab": 3,
    "ResearchGap": 3,
    "StartupOpportunity": 3,
}


def _is_more_specific(new_type: str, old_type: str) -> bool:
    return _TYPE_RANK.get(new_type, 0) > _TYPE_RANK.get(old_type, 0)


class KnowledgeGraphAgent:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_entity(self, entity_type: str, name: str, metadata: dict = None):
        if not name:
            return
        name = str(name).strip()[:500]
        if not name:
            return
        if self.graph.has_node(name):
            self.graph.nodes[name]["metadata"].update(metadata or {})
            old_type = self.graph.nodes[name].get("type", "unknown")
            if _is_more_specific(entity_type, old_type):
                self.graph.nodes[name]["type"] = entity_type
        else:
            self.graph.add_node(name, type=entity_type, metadata=metadata or {})

    def add_relationship(self, source: str, relation: str, target: str):
        if not source or not target:
            return
        source = str(source).strip()[:500]
        target = str(target).strip()[:500]
        if not source or not target or source == target:
            return
        if self.graph.has_edge(source, target):
            self.graph[source][target]["weight"] = self.graph[source][target].get("weight", 1) + 1
        else:
            self.graph.add_edge(source, target, relation=relation, weight=1)

    def build_from_documents(self, documents: list):
        """Document + Keyword layer (keeps legacy behavior)."""
        for doc in documents:
            source = doc.get("source", "unknown")
            title = doc.get("title", "")
            if not title:
                continue
            self.add_entity("Document", title, {"source": source})
            for keyword in (doc.get("keywords") or [])[:5]:
                self.add_entity("Keyword", keyword)
                self.add_relationship(title, "has_keyword", keyword)
        return {"nodes": self.graph.number_of_nodes(), "edges": self.graph.number_of_edges()}

    def build_semantic_graph(self, raw, clusters, gaps, opportunities, global_topics=None):
        """Build the full semantic chain across entity types."""
        global_topics = global_topics or []

        # 1. Technology nodes (topics + opportunity/cluster keywords)
        for topic in global_topics:
            label = topic.get("label") or ", ".join(topic.get("keywords", [])[:2])
            if not label:
                continue
            self.add_entity("Technology", label, {
                "keywords": topic.get("keywords", []),
                "topic_id": topic.get("topic_id"),
            })

        # 2. Problem nodes (from clusters)
        cluster_titles = []
        for c in clusters:
            clean = (c.get("title") or "").replace("Problem Cluster:", "").strip()
            if not clean:
                continue
            cluster_titles.append(clean)
            self.add_entity("Problem", clean, {
                "demand_score": c.get("demand_score", 0),
                "source_count": c.get("source_count", 0),
                "keywords": c.get("keywords", []),
            })
            for kw in (c.get("keywords") or [])[:5]:
                self.add_entity("Technology", kw, {})
                self.add_relationship(clean, "related_to", kw)

        # 3. ResearchPaper nodes (arXiv)
        paper_titles = set()
        for paper in raw.get("arxiv", []):
            title = (paper.get("title") or "").strip()
            if not title or len(title) < 5:
                continue
            paper_titles.add(title)
            self.add_entity("ResearchPaper", title, {
                "url": paper.get("url", ""),
                "source": "arxiv",
            })
            for author in (paper.get("authors") or [])[:3]:
                if not author:
                    continue
                self.add_entity("Author", author, {})
                self.add_relationship(title, "authored_by", author)
            for kw in (paper.get("keywords") or [])[:3]:
                self.add_entity("Technology", kw, {})
                self.add_relationship(title, "studies", kw)

        # 4. Repository nodes (GitHub) → link to problems
        for repo in raw.get("github", []):
            name = (repo.get("name") or repo.get("full_name") or "").strip()
            if not name:
                continue
            self.add_entity("Repository", name, {
                "url": repo.get("html_url", ""),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", ""),
            })
            lang = repo.get("language")
            if lang:
                self.add_entity("Technology", lang, {})
                self.add_relationship(name, "written_in", lang)
            repo_text = (name + " " + (repo.get("description") or "")).lower()
            for c in clusters:
                clean = (c.get("title") or "").replace("Problem Cluster:", "").strip()
                if not clean:
                    continue
                for kw in (c.get("keywords") or [])[:5]:
                    if kw.lower() in repo_text:
                        self.add_relationship(name, "solves", clean)
                        break

        # 5. Industry nodes (News sources)
        for article in raw.get("news", []):
            src = article.get("source") or "News"
            self.add_entity("Industry", src, {"type": "news_source"})
            title = (article.get("title") or "").strip()
            if title:
                self.add_entity("Article", title, {
                    "url": article.get("url", ""),
                    "source": src,
                })
                self.add_relationship(src, "published", title)

        # 5b. R&D Lab nodes (from rd_cells source) → link to their published articles
        for post in raw.get("rd_cells", []):
            lab = (post.get("lab") or "Unknown Lab").strip()
            title = (post.get("title") or "").strip()
            if not lab or not title:
                continue
            self.add_entity("RDLab", lab, {"type": "research_organization"})
            self.add_entity("Article", title, {
                "url": post.get("url", ""),
                "source": "rd_cells",
                "lab": lab,
            })
            self.add_relationship(lab, "published", title)
            # Link lab to keywords found in the post
            post_text = (title + " " + (post.get("summary") or "")).lower()
            for cluster in clusters:
                for kw in (cluster.get("keywords") or [])[:5]:
                    if kw.lower() in post_text:
                        self.add_relationship(lab, "researches", kw)
                        break

        # 6. Research Gap nodes → link to papers + problems
        for gap in gaps:
            gap_title = (gap.get("title") or "").strip()
            if not gap_title:
                continue
            self.add_entity("ResearchGap", gap_title, {
                "gap_score": gap.get("gap_score", 0),
            })
            ev = gap.get("evidence", {})
            for kw in (ev.get("keywords") or [])[:5]:
                self.add_relationship(gap_title, "addresses", kw)
            for fws in (ev.get("future_work_snippets") or [])[:3]:
                paper = (fws.get("paper") or "").strip()
                if paper and paper in paper_titles:
                    self.add_relationship(gap_title, "highlighted_in", paper)

        # 7. StartupOpportunity nodes → link to Problem, Gap, Industry
        for opp in opportunities:
            opp_title = (opp.get("title") or "").strip()
            if not opp_title:
                continue
            self.add_entity("StartupOpportunity", opp_title, {
                "score": opp.get("opportunity_score", 0),
                "feasibility": opp.get("feasibility_score", 0),
                "market_readiness": opp.get("market_readiness_score", 0),
            })
            cluster = opp.get("_cluster_title")
            if cluster:
                self.add_relationship(opp_title, "addresses", cluster)
            gap_title = opp.get("_gap_title")
            if gap_title:
                self.add_relationship(opp_title, "informed_by", gap_title)
            news_items = raw.get("news", [])
            if news_items:
                src = news_items[0].get("source") or ""
                if src:
                    self.add_relationship(opp_title, "targets_industry", src)

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }

    def persist(self):
        db = SessionLocal()
        try:
            existing_nodes = {n.name for n in db.query(models.KnowledgeGraphNode.name).all()}
            existing_edges = {
                (e.source, e.target, e.relation)
                for e in db.query(models.KnowledgeGraphEdge).all()
            }

            new_nodes = 0
            for node, attrs in self.graph.nodes(data=True):
                if node in existing_nodes:
                    existing = db.query(models.KnowledgeGraphNode).filter_by(name=node).first()
                    new_type = attrs.get("type", "unknown")
                    if existing and _is_more_specific(new_type, existing.entity_type or "unknown"):
                        existing.entity_type = new_type
                    continue
                db.add(models.KnowledgeGraphNode(
                    name=node,
                    entity_type=attrs.get("type", "unknown"),
                    metadata_json=attrs.get("metadata", {}),
                ))
                new_nodes += 1

            new_edges = 0
            for src, tgt, attrs in self.graph.edges(data=True):
                key = (src, tgt, attrs.get("relation", ""))
                if key in existing_edges:
                    continue
                db.add(models.KnowledgeGraphEdge(
                    source=src,
                    target=tgt,
                    relation=attrs.get("relation", "related_to"),
                ))
                new_edges += 1

            db.commit()
            logger.info(f"KG persisted: +{new_nodes} nodes, +{new_edges} edges "
                        f"(graph: {self.graph.number_of_nodes()}/{self.graph.number_of_edges()})")
            return {"new_nodes": new_nodes, "new_edges": new_edges}
        except Exception as e:
            db.rollback()
            logger.error(f"KG persist error: {e}")
            return {"new_nodes": 0, "new_edges": 0}
        finally:
            db.close()
