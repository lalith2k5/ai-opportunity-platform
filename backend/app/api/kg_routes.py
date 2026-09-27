from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/kg", tags=["knowledge-graph"])


@router.get("/stats")
def kg_stats(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return {
        "nodes": db.query(models.KnowledgeGraphNode).count(),
        "edges": db.query(models.KnowledgeGraphEdge).count(),
    }


@router.get("/nodes")
def list_nodes(
    entity_type: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
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
def node_neighbors(
    name: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
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
def list_edges(
    relation: str = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = db.query(models.KnowledgeGraphEdge)
    if relation:
        q = q.filter(models.KnowledgeGraphEdge.relation == relation)
    rows = q.limit(limit).all()
    return [{"source": e.source, "target": e.target, "relation": e.relation} for e in rows]


@router.get("/search")
def kg_search(
    q: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    nodes = db.query(models.KnowledgeGraphNode).filter(
        models.KnowledgeGraphNode.name.ilike(f"%{q}%")
    ).limit(20).all()
    return [{"name": n.name, "type": n.entity_type} for n in nodes]

@router.get("/entity-types")
def entity_types(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """List distinct entity types with counts, for graph visualization."""
    from sqlalchemy import func
    rows = db.query(
        models.KnowledgeGraphNode.entity_type,
        func.count(models.KnowledgeGraphNode.id),
    ).group_by(models.KnowledgeGraphNode.entity_type).all()
    return [{"type": r[0] or "unknown", "count": r[1]} for r in rows]


@router.get("/semantic-chain/{name}")
def semantic_chain(
    name: str,
    depth: int = 2,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Return the semantic neighborhood around a node (BFS up to `depth`)."""
    visited = set()
    queue = [(name, 0)]
    nodes_out = []
    edges_out = []

    while queue:
        current, d = queue.pop(0)
        if current in visited or d > depth:
            continue
        visited.add(current)

        node = db.query(models.KnowledgeGraphNode).filter_by(name=current).first()
        if node:
            nodes_out.append({
                "name": node.name,
                "type": node.entity_type,
                "metadata": node.metadata_json,
            })

        outgoing = db.query(models.KnowledgeGraphEdge).filter_by(source=current).limit(20).all()
        incoming = db.query(models.KnowledgeGraphEdge).filter_by(target=current).limit(20).all()

        for e in outgoing:
            edges_out.append({"source": e.source, "target": e.target, "relation": e.relation})
            if d < depth:
                queue.append((e.target, d + 1))
        for e in incoming:
            edges_out.append({"source": e.source, "target": e.target, "relation": e.relation})
            if d < depth:
                queue.append((e.source, d + 1))

    return {"root": name, "nodes": nodes_out, "edges": edges_out}
