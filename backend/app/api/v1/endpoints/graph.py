"""ECCRP Module 13 - Knowledge Graph Endpoint."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User, KnowledgeGraphNode, KnowledgeGraphEdge
from app.core.security import get_current_active_user

router = APIRouter()


@router.get("/nodes")
async def list_graph_nodes(
    node_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List knowledge graph nodes (Articles, Sections, Rules, Judgments, Requirements)."""
    query = select(KnowledgeGraphNode)
    if node_type:
        query = query.where(KnowledgeGraphNode.node_type == node_type)
    if search:
        query = query.where(KnowledgeGraphNode.label.ilike(f"%{search}%"))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    nodes = result.scalars().all()
    return {
        "nodes": [
            {
                "id": str(n.id),
                "neo4j_id": n.neo4j_node_id,
                "type": n.node_type,
                "label": n.label,
                "properties": n.properties,
            }
            for n in nodes
        ]
    }


@router.get("/edges")
async def list_graph_edges(
    from_node_id: Optional[UUID] = Query(None),
    relationship_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List knowledge graph edges."""
    query = select(KnowledgeGraphEdge)
    if from_node_id:
        query = query.where(KnowledgeGraphEdge.from_node_id == from_node_id)
    if relationship_type:
        query = query.where(KnowledgeGraphEdge.relationship_type == relationship_type)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    edges = result.scalars().all()
    return {
        "edges": [
            {
                "id": str(e.id),
                "from_node": str(e.from_node_id),
                "to_node": str(e.to_node_id),
                "relationship": e.relationship_type,
                "weight": e.weight,
            }
            for e in edges
        ]
    }


@router.get("/subgraph/{node_id}")
async def get_subgraph(
    node_id: UUID,
    depth: int = Query(2, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a subgraph centered on a node (for visualization)."""
    # Get the central node
    node_result = await db.execute(
        select(KnowledgeGraphNode).where(KnowledgeGraphNode.id == node_id)
    )
    center = node_result.scalar_one_or_none()
    if not center:
        raise HTTPException(status_code=404, detail="Node not found")

    # Get connected edges
    edge_result = await db.execute(
        select(KnowledgeGraphEdge).where(
            (KnowledgeGraphEdge.from_node_id == node_id) |
            (KnowledgeGraphEdge.to_node_id == node_id)
        ).limit(50)
    )
    edges = edge_result.scalars().all()

    # Collect neighbor node IDs
    neighbor_ids = set()
    for e in edges:
        if e.from_node_id != node_id:
            neighbor_ids.add(e.from_node_id)
        if e.to_node_id != node_id:
            neighbor_ids.add(e.to_node_id)

    # Get neighbor nodes
    nodes = [center]
    if neighbor_ids:
        neighbor_result = await db.execute(
            select(KnowledgeGraphNode).where(
                KnowledgeGraphNode.id.in_(list(neighbor_ids))
            )
        )
        nodes.extend(neighbor_result.scalars().all())

    return {
        "center_node": {"id": str(center.id), "type": center.node_type, "label": center.label},
        "nodes": [{"id": str(n.id), "type": n.node_type, "label": n.label} for n in nodes],
        "edges": [
            {
                "from": str(e.from_node_id),
                "to": str(e.to_node_id),
                "relationship": e.relationship_type,
            }
            for e in edges
        ],
    }


@router.get("/visualization/full")
async def get_full_graph_data(
    limit: int = Query(200, ge=10, le=500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get graph data for full visualization (D3.js / Cytoscape format)."""
    node_result = await db.execute(select(KnowledgeGraphNode).limit(limit))
    all_nodes = node_result.scalars().all()

    node_ids = {n.id for n in all_nodes}
    edge_result = await db.execute(
        select(KnowledgeGraphEdge).where(
            KnowledgeGraphEdge.from_node_id.in_(node_ids),
            KnowledgeGraphEdge.to_node_id.in_(node_ids),
        ).limit(limit * 2)
    )
    all_edges = edge_result.scalars().all()

    return {
        "nodes": [
            {
                "id": str(n.id),
                "label": n.label,
                "type": n.node_type,
                "group": n.node_type,
            }
            for n in all_nodes
        ],
        "links": [
            {
                "source": str(e.from_node_id),
                "target": str(e.to_node_id),
                "type": e.relationship_type,
                "value": e.weight,
            }
            for e in all_edges
        ],
    }
