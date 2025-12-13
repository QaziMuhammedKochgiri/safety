"""
Contact Network Graph API Router

Provides endpoints for building and querying contact network graphs
from forensic communication data.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import get_current_admin
from ..database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..forensics.visualization import (
    ContactNetworkGraph,
    NetworkNode,
    NetworkEdge,
    build_contact_network,
    detect_clusters
)
from ..forensics.visualization.contact_network import NodeType, Platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/network", tags=["network-graph"])


# Pydantic models for API

class NetworkGraphRequest(BaseModel):
    """Request model for building a network graph"""
    case_id: str
    primary_contact: Optional[str] = None
    n_clusters: int = Field(default=3, ge=1, le=10)
    include_calls: bool = True
    min_messages: int = Field(default=1, ge=0)


class NetworkNodeResponse(BaseModel):
    """Response model for a network node"""
    id: str
    label: str
    type: str
    platforms: List[str]
    totalMessages: int
    sentMessages: int
    receivedMessages: int
    totalCalls: int
    callDuration: int
    riskScore: float
    clusterId: Optional[int]
    centrality: float


class NetworkEdgeResponse(BaseModel):
    """Response model for a network edge"""
    id: str
    source: str
    target: str
    platform: str
    messageCount: int
    callCount: int
    weight: float


class ClusterResponse(BaseModel):
    """Response model for a cluster"""
    id: int
    label: str
    nodeCount: int
    color: str


class NetworkStatsResponse(BaseModel):
    """Response model for network statistics"""
    totalNodes: int
    totalEdges: int
    totalMessages: int
    totalCalls: int
    avgMessagesPerContact: float
    clusters: int
    platformDistribution: dict


class SuspiciousPatternResponse(BaseModel):
    """Response model for suspicious patterns"""
    type: str
    node_id: str
    label: str
    description: str


@router.get("/{case_id}")
async def get_network_graph(
    case_id: str,
    n_clusters: int = Query(default=3, ge=1, le=10),
    min_messages: int = Query(default=1, ge=0),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the contact network graph for a case.

    Returns Cytoscape.js compatible JSON for visualization.
    """
    try:
        # Get case data
        case = await db.cases.find_one({"_id": case_id})
        if not case:
            case = await db.cases.find_one({"case_id": case_id})

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Get forensic data
        messages = []
        calls = []
        contacts = []

        # Get messages from forensic_results
        forensic_results = await db.forensic_results.find(
            {"case_id": case_id}
        ).to_list(length=None)

        for result in forensic_results:
            if "messages" in result:
                messages.extend(result.get("messages", []))
            if "calls" in result:
                calls.extend(result.get("calls", []))
            if "contacts" in result:
                contacts.extend(result.get("contacts", []))

        # Get from collected_data collection
        collected_data = await db.collected_data.find(
            {"case_id": case_id}
        ).to_list(length=None)

        for data in collected_data:
            if data.get("data_type") == "whatsapp":
                wa_messages = data.get("data", {}).get("messages", [])
                for msg in wa_messages:
                    messages.append({
                        "sender": msg.get("sender") or msg.get("from"),
                        "receiver": msg.get("receiver") or msg.get("to"),
                        "platform": "whatsapp",
                        "timestamp": msg.get("timestamp"),
                        "is_outgoing": msg.get("is_outgoing", True)
                    })
            elif data.get("data_type") == "sms":
                sms_messages = data.get("data", {}).get("messages", [])
                for msg in sms_messages:
                    messages.append({
                        "sender": msg.get("sender") or msg.get("from"),
                        "receiver": msg.get("receiver") or msg.get("to"),
                        "platform": "sms",
                        "timestamp": msg.get("timestamp"),
                        "is_outgoing": msg.get("is_outgoing", True)
                    })
            elif data.get("data_type") == "calls":
                call_data = data.get("data", {}).get("calls", [])
                calls.extend(call_data)
            elif data.get("data_type") == "contacts":
                contact_data = data.get("data", {}).get("contacts", [])
                contacts.extend(contact_data)

        # Get primary contact (client phone)
        client_id = case.get("client_id")
        primary_contact = None
        if client_id:
            client = await db.clients.find_one({"_id": client_id})
            if client:
                primary_contact = client.get("phone")

        # Build network graph
        graph = build_contact_network(
            case_id=case_id,
            messages=messages,
            calls=calls,
            contacts=contacts,
            primary_contact=primary_contact
        )

        # Filter by minimum messages
        if min_messages > 1:
            nodes_to_remove = [
                node_id for node_id, node in graph.nodes.items()
                if node.total_messages < min_messages
            ]
            for node_id in nodes_to_remove:
                del graph.nodes[node_id]
                # Remove edges connected to this node
                edges_to_remove = [
                    edge_id for edge_id, edge in graph.edges.items()
                    if edge.source == node_id or edge.target == node_id
                ]
                for edge_id in edges_to_remove:
                    del graph.edges[edge_id]

        # Detect clusters
        if len(graph.nodes) >= n_clusters:
            detect_clusters(graph, n_clusters)

        # Log access
        await db.audit_logs.insert_one({
            "action": "network_graph_view",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
                "clusters": len(graph.clusters)
            }
        })

        return graph.to_cytoscape_json()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building network graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}/stats")
async def get_network_stats(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> NetworkStatsResponse:
    """
    Get statistics for a case's contact network.
    """
    try:
        # Use the same logic as get_network_graph but return stats only
        result = await get_network_graph(
            case_id=case_id,
            current_user=current_user,
            db=db
        )

        metadata = result.get("metadata", {})
        nodes = result.get("elements", {}).get("nodes", [])

        # Calculate platform distribution
        platform_dist = {}
        for node in nodes:
            for platform in node.get("data", {}).get("platforms", []):
                platform_dist[platform] = platform_dist.get(platform, 0) + 1

        total_messages = sum(
            n.get("data", {}).get("totalMessages", 0)
            for n in nodes
        ) // 2  # Divide by 2 as messages counted twice

        total_calls = sum(
            n.get("data", {}).get("totalCalls", 0)
            for n in nodes
        ) // 2

        return NetworkStatsResponse(
            totalNodes=metadata.get("totalNodes", 0),
            totalEdges=metadata.get("totalEdges", 0),
            totalMessages=total_messages,
            totalCalls=total_calls,
            avgMessagesPerContact=round(
                total_messages / max(1, metadata.get("totalNodes", 1)), 1
            ),
            clusters=len(metadata.get("clusters", [])),
            platformDistribution=platform_dist
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting network stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}/suspicious")
async def get_suspicious_patterns(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[SuspiciousPatternResponse]:
    """
    Detect and return suspicious communication patterns.
    """
    try:
        # Build graph first
        graph_data = await get_network_graph(
            case_id=case_id,
            current_user=current_user,
            db=db
        )

        # We need to rebuild the graph to access methods
        # This is a simplified check based on the returned data
        patterns = []
        nodes = graph_data.get("elements", {}).get("nodes", [])

        for node in nodes:
            data = node.get("data", {})
            total_messages = data.get("totalMessages", 0)
            sent = data.get("sentMessages", 0)
            received = data.get("receivedMessages", 0)

            if total_messages > 20:
                total = sent + received
                if total > 0:
                    sent_ratio = sent / total

                    # One-way outgoing
                    if sent_ratio > 0.9:
                        patterns.append(SuspiciousPatternResponse(
                            type="one_way_outgoing",
                            node_id=data.get("id"),
                            label=data.get("label"),
                            description=f"Tek yönlü iletişim (giden): %{round(sent_ratio * 100, 1)}"
                        ))
                    # One-way incoming
                    elif sent_ratio < 0.1:
                        patterns.append(SuspiciousPatternResponse(
                            type="one_way_incoming",
                            node_id=data.get("id"),
                            label=data.get("label"),
                            description=f"Tek yönlü iletişim (gelen): %{round((1 - sent_ratio) * 100, 1)}"
                        ))

            # High risk score
            if data.get("riskScore", 0) > 0.7:
                patterns.append(SuspiciousPatternResponse(
                    type="high_risk",
                    node_id=data.get("id"),
                    label=data.get("label"),
                    description=f"Yüksek risk skoru: {round(data.get('riskScore', 0) * 100)}%"
                ))

        return patterns

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting suspicious patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}/clusters")
async def get_clusters(
    case_id: str,
    n_clusters: int = Query(default=3, ge=1, le=10),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[ClusterResponse]:
    """
    Get cluster information for a case's network.
    """
    try:
        graph_data = await get_network_graph(
            case_id=case_id,
            n_clusters=n_clusters,
            current_user=current_user,
            db=db
        )

        clusters = graph_data.get("metadata", {}).get("clusters", [])
        return [
            ClusterResponse(
                id=c.get("id"),
                label=c.get("label"),
                nodeCount=c.get("nodeCount"),
                color=c.get("color")
            )
            for c in clusters
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}/node/{node_id}")
async def get_node_details(
    case_id: str,
    node_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get detailed information about a specific node.
    """
    try:
        graph_data = await get_network_graph(
            case_id=case_id,
            current_user=current_user,
            db=db
        )

        nodes = graph_data.get("elements", {}).get("nodes", [])
        edges = graph_data.get("elements", {}).get("edges", [])

        # Find the node
        target_node = None
        for node in nodes:
            if node.get("data", {}).get("id") == node_id:
                target_node = node.get("data")
                break

        if not target_node:
            raise HTTPException(status_code=404, detail="Node not found")

        # Find connected edges and nodes
        connected_edges = []
        connected_node_ids = set()

        for edge in edges:
            edge_data = edge.get("data", {})
            if edge_data.get("source") == node_id:
                connected_edges.append(edge_data)
                connected_node_ids.add(edge_data.get("target"))
            elif edge_data.get("target") == node_id:
                connected_edges.append(edge_data)
                connected_node_ids.add(edge_data.get("source"))

        connected_nodes = [
            n.get("data") for n in nodes
            if n.get("data", {}).get("id") in connected_node_ids
        ]

        return {
            "node": target_node,
            "connectedNodes": connected_nodes,
            "edges": connected_edges,
            "totalConnections": len(connected_edges)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
