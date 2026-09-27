import networkx as nx
from app.database import SessionLocal
from app import models
from app.logger import logger


class KnowledgeGraphAgent:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_entity(self, entity_type: str, name: str, metadata: dict = None):
        self.graph.add_node(name, type=entity_type, metadata=metadata or {})

    def add_relationship(self, source: str, relation: str, target: str):
        self.graph.add_edge(source, target, relation=relation)

    def build_from_documents(self, documents: list):
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

    def persist(self):
        """Save nodes and edges to PostgreSQL (dedup by name/relation)."""
        db = SessionLocal()
        try:
            existing_nodes = {
                n.name for n in db.query(models.KnowledgeGraphNode.name).all()
            }
            existing_edges = {
                (e.source, e.target, e.relation)
                for e in db.query(models.KnowledgeGraphEdge).all()
            }

            new_nodes = 0
            for node, attrs in self.graph.nodes(data=True):
                if node in existing_nodes:
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
            logger.info(f"KG persisted: {new_nodes} new nodes, {new_edges} new edges")
            return {"new_nodes": new_nodes, "new_edges": new_edges}
        except Exception as e:
            db.rollback()
            logger.error(f"KG persist error: {e}")
            return {"new_nodes": 0, "new_edges": 0}
        finally:
            db.close()
