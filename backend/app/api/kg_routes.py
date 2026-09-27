from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/kg", tags=["knowledge-graph"])


@router.get("/stats")
def kg_stats(db: Session = Depends(get_db)):
    return {
        "nodes": db.query(models.KnowledgeGraphNode).count(),
        "edges": db.query(models.KnowledgeGraphEdge).count(),
    }


@router.get("/nodes")
def list_nodes(
    entity_type: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(models.KnowledgeGraphNode)
    if entity_type:
        q = q.filter(models.KnowledgeGraphNode.entity_type == entity_type)
    rows = q.limit(limit).all()
    return [
        {"id": n.id, "name": n.name, "type": n.entity_type, "metadata": n.metadata_json}
        for n in rows
    ]


@router.get("/nodes/{name}/neighbors")
def node_neighbors(name: str, db: Session = Depends(get_db)):
    outgoing = db.query(models.KnowledgeGraphEdge).filter(
        models.KnowledgeGraphEdge.source == name
    ).all()
    incoming = db.query(models.KnowledgeGraphEdge).filter(
        models.KnowledgeGraphEdge.target == name
    ).all()
    return {
        "node": name,
        "outgoing": [{"target": e.target, "relation": e.relation} for e in outgoing],
        "incoming": [{"source": e.source, "relation": e.relation} for e in incoming],
    }


@router.get("/edges")
def list_edges(relation: str = None, limit: int = 200, db: Session = Depends(get_db)):
    q = db.query(models.KnowledgeGraphEdge)
    if relation:
        q = q.filter(models.KnowledgeGraphEdge.relation == relation)
    rows = q.limit(limit).all()
    return [{"source": e.source, "target": e.target, "relation": e.relation} for e in rows]


@router.get("/search")
def kg_search(q: str, db: Session = Depends(get_db)):
    nodes = db.query(models.KnowledgeGraphNode).filter(
        models.KnowledgeGraphNode.name.ilike(f"%{q}%")
    ).limit(20).all()
    return [{"name": n.name, "type": n.entity_type} for n in nodes]
