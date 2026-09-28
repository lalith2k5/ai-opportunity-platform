import networkx as nx
from app.database import SessionLocal
from app import models
from app.logger import logger
from app.kg_schema import normalize_relation, CANONICAL_RELATIONS


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


# ---- Phase 10.4: canonical source display names (SRS 31) ----
_SOURCE_CANONICAL = {
    "github":           "GitHub",
    "github_issues":    "GitHub",
    "arxiv":            "arXiv",
    "news":             "News",
    "reddit":           "Reddit",
    "rd_cells":         "R&D Labs",
    "patents":          "PatentsView",
    "challenge_portal": "SBIR/Challenge.gov",
    "sbir":             "SBIR",
    "challenge_gov":    "Challenge.gov",
    "nasa":             "NASA",
    "nsf":              "NSF",
    "nist":             "NIST",
    "darpa":            "DARPA",
    "nih":              "NIH",
    "energy_gov":       "DOE",
    "cdc":              "CDC",
}


def _canonical_source(raw: str) -> str:
    if not raw:
        return ""
    key = str(raw).strip().lower()
    if key in _SOURCE_CANONICAL:
        return _SOURCE_CANONICAL[key]
    return str(raw).strip().replace("_", " ").title()


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
        # Normalize legacy lowercase names to canonical uppercase (SRS §31).
        relation = normalize_relation(relation)
        if self.graph.has_edge(source, target):
            self.graph[source][target]["weight"] = self.graph[source][target].get("weight", 1) + 1
        else:
            self.graph.add_edge(source, target, relation=relation, weight=1)

    # Map spaCy NER labels -> KG entity types. Only useful categories kept.
    _NER_LABEL_MAP = {
        "PERSON":  "Author",
        "ORG":     "Industry",
        "PRODUCT": "Technology",
    }

    # Generic single words spaCy sometimes mislabels as entities.
    _NER_STOPLIST = {
        "api", "cli", "sdk", "ui", "ux", "http", "https", "json",
        "html", "css", "sql", "url", "uri", "xml", "csv",
        "library", "libraries", "framework", "frameworks",
        "platform", "platforms", "tutorials", "tutorial",
        "guide", "guides", "docs", "documentation",
        "project", "projects", "code", "codes", "tool", "tools",
        "quantum", "learning", "computing", "intelligence",
        "data", "cloud", "open", "source", "free", "new",
        "modern", "moderns", "honors", "honor", "internship",
        "curriculum", "summerschool", "summer", "school",
        "technology", "technologies", "science", "sciences",
        "medicine", "medical", "healthcare", "statistics",
        "artificial", "machine", "deep", "data", "big",
        "online", "offline", "minima", "maxima", "pipeline",
        "showcase", "graduate", "course", "courses", "class",
        "paper", "papers", "survey", "surveys", "review", "reviews",
        "the", "a", "an", "of", "for", "and", "or", "in", "on", "with",
        "software", "hardware", "kernel", "kernels", "framework",
        "center", "centre", "college", "director", "showcase",
        "email", "blurb", "figure", "figures", "photo", "image",
        "images", "congratulations", "thanks", "author", "authors",
        "researcher", "researchers", "student", "students",
        "university", "universities", "institute", "institutes",
        "department", "departments", "newsletter", "brief",
    }

    def _link_nlp_entities(self, doc_title: str, entities: list):
        """Turn NLP-extracted named entities into KG nodes/edges.

        Entities have already been shape-validated in NLPAgent.extract_entities.
        This layer only enforces a few KG-specific guards:
          - skip entities equal to the doc title
          - skip entities contained in the doc title (title fragments)
          - dedupe within this doc
        """
        if not entities:
            return
        tl = (doc_title or "").lower()
        seen = set()
        for ent in entities:
            text = str(ent.get("text") or "").strip()
            label = str(ent.get("label") or "").strip().upper()
            if not text:
                continue
            mapped = self._NER_LABEL_MAP.get(label)
            if not mapped:
                continue
            key = text.lower()
            if key in seen:
                continue
            # Skip self-mention or title fragment
            if tl:
                if key == tl or key in tl or tl in key:
                    continue
            seen.add(key)
            self.add_entity(mapped, text, {"from_ner": True, "ner_label": label})
            self.add_relationship(doc_title, "mentions", text)


    def build_from_documents(self, documents: list):
        """Document + Keyword + NER + Topic layer."""
        for doc in documents:
            source = doc.get("source", "unknown")
            title = doc.get("title", "")
            if not title:
                continue
            self.add_entity("Document", title, {"source": source})
            for keyword in (doc.get("keywords") or [])[:5]:
                self.add_entity("Keyword", keyword)
                self.add_relationship(title, "has_keyword", keyword)
            # NER entities from the NLP pipeline -> KG nodes + "mentions" edges
            self._link_nlp_entities(title, doc.get("entities") or [])
            # Primary topic (assigned by orchestrator from global NMF model)
            primary_topic = doc.get("primary_topic")
            if primary_topic:
                self.add_entity("Technology", primary_topic, {"from_topic": True})
                self.add_relationship(title, "belongs_to_topic", primary_topic)
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

    def build_enriched_graph(self):
        """Add canonical SRS §31 edges derived from Phase 2/3/4 tables.

        Reads problem_profiles, problem_technologies, problem_papers, and
        opportunity_evidence and emits edges that the in-memory pipeline
        couldn't build (those tables are only populated after the earlier
        KG layers have already been persisted). Merges into the existing
        self.graph — call persist() after this to flush to DB.
        """
        db = SessionLocal()
        try:
            # ---------------- ProblemProfile backbone ----------------
            profiles = db.query(models.ProblemProfile).all()
            if not profiles:
                return {"new_nodes": 0, "new_edges": 0}

            profile_by_id = {p.id: p for p in profiles}
            org_by_id = {o.id: o for o in db.query(models.Organization).all()}

            # Problem nodes (from ProblemProfile titles)
            for p in profiles:
                title = (p.problem_title or "").strip()
                if not title:
                    continue
                self.add_entity("Problem", title, {
                    "canonical_hash": p.canonical_hash,
                    "industry_domain": p.industry_domain,
                    "source": p.source,
                })

                # Problem —REPORTED_BY-> Organization
                # Prefer the linked Organization row (canonical name + metadata);
                # fall back to the raw string if no FK is set yet.
                org_name = ""
                org_meta = {}
                if p.organization_id:
                    org_row = org_by_id.get(p.organization_id)
                    if org_row:
                        org_name = org_row.name
                        org_meta = {
                            "canonical_name": org_row.canonical_name,
                            "industry_domain": org_row.industry_domain,
                            "source": org_row.source,
                        }
                if not org_name:
                    org_name = (p.organization or "").strip()
                if org_name and org_name.lower() != "unknown":
                    self.add_entity("Organization", org_name, org_meta)
                    self.add_relationship(title, "REPORTED_BY", org_name)

                # Problem —FOUND_IN-> Source (SRS 31, canonical name)
                src_raw = (p.source or "").strip()
                if src_raw and src_raw.lower() != "unknown":
                    src_name = _canonical_source(src_raw)
                    self.add_entity("Source", src_name, {
                        "type": "source",
                        "raw_source": src_raw,
                    })
                    self.add_relationship(title, "FOUND_IN", src_name)

            # ---------------- Problem —RELATED_TO-> Technology ----------------
            tech_rows = db.query(models.ProblemTechnology).all()
            for t in tech_rows:
                parent = profile_by_id.get(t.problem_profile_id)
                if not parent or not parent.problem_title:
                    continue
                tname = (t.technology_name or "").strip()
                if not tname:
                    continue
                self.add_entity("Technology", tname, {
                    "stage": t.stage,
                    "confidence": t.confidence,
                })
                self.add_relationship(parent.problem_title, "RELATED_TO", tname)

            # ---------------- Problem —STUDIED_BY-> ResearchPaper ----------------
            paper_rows = db.query(models.ProblemPaper).all()
            paper_nodes = []      # (title, limitations, arxiv_id)
            for p in paper_rows:
                parent = profile_by_id.get(p.problem_profile_id)
                if not parent or not parent.problem_title:
                    continue
                ptitle = (p.title or "").strip()
                if not ptitle:
                    continue
                self.add_entity("ResearchPaper", ptitle, {
                    "arxiv_id": p.arxiv_id,
                    "url": p.url,
                    "relevance_score": p.relevance_score,
                })
                self.add_relationship(parent.problem_title, "STUDIED_BY", ptitle)
                paper_nodes.append((ptitle, p.limitations or []))

            # ---------------- ResearchPaper —HAS_LIMITATION-> Limitation ----------------
            for ptitle, lims in paper_nodes:
                for lim in lims:
                    s = str(lim or "").strip()[:300]
                    if not s:
                        continue
                    self.add_entity("Limitation", s, {})
                    self.add_relationship(ptitle, "HAS_LIMITATION", s)

            # ---------------- Opportunity —SUPPORTED_BY-> Evidence ----------------
            ev_rows = db.query(models.OpportunityEvidence).all()
            opp_by_id = {o.id: o for o in db.query(models.Opportunity).all()}
            for e in ev_rows:
                opp = opp_by_id.get(e.opportunity_id)
                if not opp or not opp.title:
                    continue
                ev_label = (e.title or e.url or "").strip()[:300]
                if not ev_label:
                    continue
                self.add_entity("Evidence", ev_label, {
                    "source": e.source,
                    "url": e.url,
                    "relevance_score": e.relevance_score,
                })
                self.add_relationship(opp.title, "SUPPORTED_BY", ev_label)

            # ---------------- Opportunity —USES-> Technology ----------------
            # Approximation: match opportunity's problem_cluster keywords to
            # each profile's keywords, then attach that profile's technologies.
            clusters = {c.id: c for c in db.query(models.ProblemCluster).all()}
            for opp in opp_by_id.values():
                cluster = clusters.get(opp.problem_cluster_id)
                if not cluster or not cluster.keywords:
                    continue
                opp_kws = {str(k).lower() for k in cluster.keywords[:10] if k}
                if not opp_kws:
                    continue
                # Find profiles whose keywords overlap strongly
                for p in profiles:
                    p_kws = {str(k).lower() for k in (p.keywords or [])[:10] if k}
                    if not p_kws:
                        continue
                    overlap = len(opp_kws & p_kws)
                    if overlap < 1:
                        continue
                    for t in tech_rows:
                        if t.problem_profile_id != p.id:
                            continue
                        tname = (t.technology_name or "").strip()
                        if tname:
                            self.add_relationship(opp.title, "USES", tname)

            # ---------------- Technology —HAS_TREND-> Trend ----------------
            trends = db.query(models.Trend).all()
            for tech in db.query(models.ProblemTechnology).all():
                tname = (tech.technology_name or "").strip()
                if not tname:
                    continue
                tlow = tname.lower()
                for tr in trends:
                    trn = (tr.name or "").strip()
                    if not trn:
                        continue
                    # exact (case-insensitive) OR tech name is substring of trend name
                    if tlow == trn.lower() or tlow in trn.lower() or trn.lower() in tlow:
                        self.add_entity("Trend", trn, {"trend_score": tr.trend_score})
                        self.add_relationship(tname, "HAS_TREND", trn)

            # ---------------- Problem —HAS_POTENTIAL_GAP-> ResearchGap ----------------
            gaps = db.query(models.ResearchGap).all()
            for gap in gaps:
                g_title = (gap.title or "").strip()
                if not g_title:
                    continue
                ev = gap.evidence or {}
                g_kws = {str(k).lower() for k in (ev.get("keywords") or [])[:8] if k}
                if not g_kws:
                    continue
                for p in profiles:
                    p_kws = {str(k).lower() for k in (p.keywords or [])[:8] if k}
                    if not p_kws:
                        continue
                    overlap = len(g_kws & p_kws)
                    if overlap < 1:
                        continue
                    self.add_relationship(p.problem_title, "HAS_POTENTIAL_GAP", g_title)

            return {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
            }
        except Exception as e:
            logger.error(f"build_enriched_graph error: {e}")
            return {"new_nodes": 0, "new_edges": 0}
        finally:
            db.close()

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
