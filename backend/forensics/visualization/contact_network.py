"""
Contact Network Graph Engine for SafeChild

Builds interactive network graphs from forensic communication data:
- Node extraction from all contacts across platforms
- Edge calculation based on message counts
- K-means clustering for community detection
- Centrality analysis for key actors

Uses Cytoscape.js compatible JSON format for frontend visualization.
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict
import hashlib
import math

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Communication platform types"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    IMESSAGE = "imessage"
    TELEGRAM = "telegram"
    SIGNAL = "signal"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    CALL = "call"
    UNKNOWN = "unknown"


class NodeType(Enum):
    """Node types in the network"""
    PRIMARY = "primary"     # Case subject (client)
    CONTACT = "contact"     # Regular contact
    FAMILY = "family"       # Family member
    FLAGGED = "flagged"     # Flagged/suspicious contact
    UNKNOWN = "unknown"     # Unknown contact


@dataclass
class NetworkNode:
    """
    Represents a contact in the network graph.
    Compatible with Cytoscape.js node format.
    """
    id: str                            # Unique identifier (hashed phone/email)
    label: str                         # Display name
    node_type: NodeType = NodeType.CONTACT
    platforms: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)
    email_addresses: List[str] = field(default_factory=list)
    total_messages: int = 0
    sent_messages: int = 0
    received_messages: int = 0
    total_calls: int = 0
    call_duration_seconds: int = 0
    first_contact: Optional[datetime] = None
    last_contact: Optional[datetime] = None
    risk_score: float = 0.0
    cluster_id: Optional[int] = None
    centrality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_cytoscape(self) -> Dict[str, Any]:
        """Convert to Cytoscape.js node format"""
        return {
            "data": {
                "id": self.id,
                "label": self.label,
                "type": self.node_type.value,
                "platforms": self.platforms,
                "totalMessages": self.total_messages,
                "sentMessages": self.sent_messages,
                "receivedMessages": self.received_messages,
                "totalCalls": self.total_calls,
                "callDuration": self.call_duration_seconds,
                "firstContact": self.first_contact.isoformat() if self.first_contact else None,
                "lastContact": self.last_contact.isoformat() if self.last_contact else None,
                "riskScore": self.risk_score,
                "clusterId": self.cluster_id,
                "centrality": self.centrality_score,
                "size": self._calculate_node_size(),
                "color": self._get_node_color()
            }
        }

    def _calculate_node_size(self) -> int:
        """Calculate node size based on communication volume"""
        base_size = 20
        # Size scales with total messages (logarithmic)
        if self.total_messages > 0:
            size = base_size + int(math.log(self.total_messages + 1) * 10)
        else:
            size = base_size
        return min(size, 100)  # Cap at 100

    def _get_node_color(self) -> str:
        """Get node color based on type and risk"""
        colors = {
            NodeType.PRIMARY: "#4CAF50",    # Green
            NodeType.FAMILY: "#2196F3",     # Blue
            NodeType.FLAGGED: "#F44336",    # Red
            NodeType.CONTACT: "#9E9E9E",    # Gray
            NodeType.UNKNOWN: "#757575"     # Dark gray
        }

        # Override with risk-based color
        if self.risk_score > 0.7:
            return "#F44336"  # Red
        elif self.risk_score > 0.4:
            return "#FF9800"  # Orange

        return colors.get(self.node_type, "#9E9E9E")


@dataclass
class NetworkEdge:
    """
    Represents a communication link between two contacts.
    Compatible with Cytoscape.js edge format.
    """
    id: str                            # Unique edge identifier
    source: str                        # Source node ID
    target: str                        # Target node ID
    platform: Platform = Platform.UNKNOWN
    message_count: int = 0
    call_count: int = 0
    call_duration_seconds: int = 0
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    bidirectional: bool = True
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_cytoscape(self) -> Dict[str, Any]:
        """Convert to Cytoscape.js edge format"""
        return {
            "data": {
                "id": self.id,
                "source": self.source,
                "target": self.target,
                "platform": self.platform.value,
                "messageCount": self.message_count,
                "callCount": self.call_count,
                "callDuration": self.call_duration_seconds,
                "firstInteraction": self.first_interaction.isoformat() if self.first_interaction else None,
                "lastInteraction": self.last_interaction.isoformat() if self.last_interaction else None,
                "weight": self.weight,
                "width": self._calculate_edge_width(),
                "color": self._get_edge_color()
            }
        }

    def _calculate_edge_width(self) -> int:
        """Calculate edge width based on interaction volume"""
        base_width = 1
        total = self.message_count + (self.call_count * 5)  # Calls weighted more
        if total > 0:
            width = base_width + int(math.log(total + 1) * 2)
        else:
            width = base_width
        return min(width, 10)  # Cap at 10

    def _get_edge_color(self) -> str:
        """Get edge color based on platform"""
        colors = {
            Platform.WHATSAPP: "#25D366",
            Platform.SMS: "#2196F3",
            Platform.IMESSAGE: "#007AFF",
            Platform.TELEGRAM: "#0088CC",
            Platform.SIGNAL: "#3A76F0",
            Platform.FACEBOOK: "#1877F2",
            Platform.INSTAGRAM: "#E4405F",
            Platform.EMAIL: "#D44638",
            Platform.CALL: "#4CAF50",
            Platform.UNKNOWN: "#9E9E9E"
        }
        return colors.get(self.platform, "#9E9E9E")


@dataclass
class ClusterResult:
    """Result of cluster analysis"""
    cluster_id: int
    node_ids: List[str]
    centroid_node_id: Optional[str] = None
    label: Optional[str] = None
    avg_messages: float = 0.0
    total_messages: int = 0
    color: str = "#9E9E9E"


class ContactNetworkGraph:
    """
    Main class for building and analyzing contact network graphs.
    """

    # Cluster colors
    CLUSTER_COLORS = [
        "#4CAF50", "#2196F3", "#FF9800", "#9C27B0",
        "#F44336", "#00BCD4", "#CDDC39", "#795548",
        "#E91E63", "#3F51B5", "#009688", "#FFC107"
    ]

    def __init__(self, case_id: str, primary_contact_id: Optional[str] = None):
        self.case_id = case_id
        self.primary_contact_id = primary_contact_id
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: Dict[str, NetworkEdge] = {}
        self.clusters: List[ClusterResult] = []
        self._edge_index: Dict[Tuple[str, str], str] = {}  # (source, target) -> edge_id

    def add_contact(
        self,
        identifier: str,
        name: str,
        platform: str = "unknown",
        phone: Optional[str] = None,
        email: Optional[str] = None,
        node_type: NodeType = NodeType.CONTACT,
        metadata: Optional[Dict] = None
    ) -> NetworkNode:
        """
        Add or update a contact node in the network.
        """
        node_id = self._generate_node_id(identifier)

        if node_id in self.nodes:
            # Update existing node
            node = self.nodes[node_id]
            if platform not in node.platforms:
                node.platforms.append(platform)
            if phone and phone not in node.phone_numbers:
                node.phone_numbers.append(phone)
            if email and email not in node.email_addresses:
                node.email_addresses.append(email)
            if metadata:
                node.metadata.update(metadata)
        else:
            # Create new node
            node = NetworkNode(
                id=node_id,
                label=name or identifier,
                node_type=node_type,
                platforms=[platform] if platform else [],
                phone_numbers=[phone] if phone else [],
                email_addresses=[email] if email else [],
                metadata=metadata or {}
            )
            self.nodes[node_id] = node

        return node

    def add_message(
        self,
        sender_id: str,
        receiver_id: str,
        platform: str,
        timestamp: Optional[datetime] = None,
        is_outgoing: bool = True,
        metadata: Optional[Dict] = None
    ) -> NetworkEdge:
        """
        Add a message interaction between two contacts.
        Updates edge weights and node statistics.
        """
        source_node_id = self._generate_node_id(sender_id)
        target_node_id = self._generate_node_id(receiver_id)

        # Ensure nodes exist
        if source_node_id not in self.nodes:
            self.add_contact(sender_id, sender_id, platform)
        if target_node_id not in self.nodes:
            self.add_contact(receiver_id, receiver_id, platform)

        # Get or create edge
        edge = self._get_or_create_edge(
            source_node_id,
            target_node_id,
            Platform(platform) if platform in Platform._value2member_map_ else Platform.UNKNOWN
        )

        # Update edge
        edge.message_count += 1
        if timestamp:
            if not edge.first_interaction or timestamp < edge.first_interaction:
                edge.first_interaction = timestamp
            if not edge.last_interaction or timestamp > edge.last_interaction:
                edge.last_interaction = timestamp

        # Update node statistics
        source_node = self.nodes[source_node_id]
        target_node = self.nodes[target_node_id]

        source_node.total_messages += 1
        target_node.total_messages += 1

        if is_outgoing:
            source_node.sent_messages += 1
            target_node.received_messages += 1
        else:
            source_node.received_messages += 1
            target_node.sent_messages += 1

        # Update contact timestamps
        if timestamp:
            for node in [source_node, target_node]:
                if not node.first_contact or timestamp < node.first_contact:
                    node.first_contact = timestamp
                if not node.last_contact or timestamp > node.last_contact:
                    node.last_contact = timestamp

        # Recalculate edge weight
        edge.weight = self._calculate_edge_weight(edge)

        return edge

    def add_call(
        self,
        caller_id: str,
        receiver_id: str,
        duration_seconds: int,
        timestamp: Optional[datetime] = None,
        is_outgoing: bool = True,
        metadata: Optional[Dict] = None
    ) -> NetworkEdge:
        """
        Add a call interaction between two contacts.
        """
        source_node_id = self._generate_node_id(caller_id)
        target_node_id = self._generate_node_id(receiver_id)

        # Ensure nodes exist
        if source_node_id not in self.nodes:
            self.add_contact(caller_id, caller_id, "call")
        if target_node_id not in self.nodes:
            self.add_contact(receiver_id, receiver_id, "call")

        # Get or create edge
        edge = self._get_or_create_edge(source_node_id, target_node_id, Platform.CALL)

        # Update edge
        edge.call_count += 1
        edge.call_duration_seconds += duration_seconds
        if timestamp:
            if not edge.first_interaction or timestamp < edge.first_interaction:
                edge.first_interaction = timestamp
            if not edge.last_interaction or timestamp > edge.last_interaction:
                edge.last_interaction = timestamp

        # Update node statistics
        source_node = self.nodes[source_node_id]
        target_node = self.nodes[target_node_id]

        source_node.total_calls += 1
        target_node.total_calls += 1
        source_node.call_duration_seconds += duration_seconds
        target_node.call_duration_seconds += duration_seconds

        # Update contact timestamps
        if timestamp:
            for node in [source_node, target_node]:
                if not node.first_contact or timestamp < node.first_contact:
                    node.first_contact = timestamp
                if not node.last_contact or timestamp > node.last_contact:
                    node.last_contact = timestamp

        # Recalculate edge weight
        edge.weight = self._calculate_edge_weight(edge)

        return edge

    def calculate_centrality(self) -> Dict[str, float]:
        """
        Calculate degree centrality for all nodes.
        Higher centrality = more connected in the network.
        """
        if not self.nodes:
            return {}

        centrality_scores = {}
        max_possible = len(self.nodes) - 1

        if max_possible == 0:
            for node_id in self.nodes:
                self.nodes[node_id].centrality_score = 1.0
                centrality_scores[node_id] = 1.0
            return centrality_scores

        # Count edges for each node
        degree_count = defaultdict(int)
        for edge in self.edges.values():
            degree_count[edge.source] += 1
            degree_count[edge.target] += 1

        # Calculate normalized centrality
        for node_id, node in self.nodes.items():
            degree = degree_count.get(node_id, 0)
            centrality = degree / max_possible
            node.centrality_score = centrality
            centrality_scores[node_id] = centrality

        return centrality_scores

    def detect_clusters(self, n_clusters: int = 3) -> List[ClusterResult]:
        """
        Detect clusters using simplified K-means on communication patterns.

        Features used:
        - Total messages
        - Sent/received ratio
        - Call count
        - Centrality score
        """
        if len(self.nodes) < n_clusters:
            n_clusters = max(1, len(self.nodes))

        # Calculate centrality first
        self.calculate_centrality()

        # Build feature vectors
        node_ids = list(self.nodes.keys())
        features = []

        for node_id in node_ids:
            node = self.nodes[node_id]
            # Feature vector: [messages, sent_ratio, calls, centrality]
            total = node.total_messages or 1
            sent_ratio = node.sent_messages / total
            features.append([
                math.log(node.total_messages + 1),
                sent_ratio,
                math.log(node.total_calls + 1),
                node.centrality_score
            ])

        # Simple K-means implementation
        clusters = self._kmeans(features, n_clusters)

        # Build cluster results
        self.clusters = []
        for cluster_id in range(n_clusters):
            cluster_node_ids = [node_ids[i] for i, c in enumerate(clusters) if c == cluster_id]

            if not cluster_node_ids:
                continue

            # Find centroid (highest centrality)
            centroid_id = max(
                cluster_node_ids,
                key=lambda nid: self.nodes[nid].centrality_score
            )

            # Calculate cluster stats
            total_msgs = sum(self.nodes[nid].total_messages for nid in cluster_node_ids)
            avg_msgs = total_msgs / len(cluster_node_ids)

            # Assign cluster to nodes
            for nid in cluster_node_ids:
                self.nodes[nid].cluster_id = cluster_id

            result = ClusterResult(
                cluster_id=cluster_id,
                node_ids=cluster_node_ids,
                centroid_node_id=centroid_id,
                label=f"Cluster {cluster_id + 1}",
                avg_messages=avg_msgs,
                total_messages=total_msgs,
                color=self.CLUSTER_COLORS[cluster_id % len(self.CLUSTER_COLORS)]
            )
            self.clusters.append(result)

        return self.clusters

    def get_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect suspicious communication patterns.
        """
        patterns = []

        # Pattern 1: Sudden communication spike
        for node_id, node in self.nodes.items():
            if node.total_messages > 100 and node.first_contact and node.last_contact:
                days = (node.last_contact - node.first_contact).days or 1
                msg_per_day = node.total_messages / days
                if msg_per_day > 50:
                    patterns.append({
                        "type": "high_frequency",
                        "node_id": node_id,
                        "label": node.label,
                        "messages_per_day": round(msg_per_day, 1),
                        "description": f"Yüksek mesaj frekansı: {round(msg_per_day, 1)} mesaj/gün"
                    })

        # Pattern 2: One-way communication
        for node_id, node in self.nodes.items():
            if node.total_messages > 20:
                total = node.sent_messages + node.received_messages
                if total > 0:
                    sent_ratio = node.sent_messages / total
                    if sent_ratio > 0.9:
                        patterns.append({
                            "type": "one_way_outgoing",
                            "node_id": node_id,
                            "label": node.label,
                            "sent_ratio": round(sent_ratio * 100, 1),
                            "description": f"Tek yönlü iletişim (giden): %{round(sent_ratio * 100, 1)}"
                        })
                    elif sent_ratio < 0.1:
                        patterns.append({
                            "type": "one_way_incoming",
                            "node_id": node_id,
                            "label": node.label,
                            "received_ratio": round((1 - sent_ratio) * 100, 1),
                            "description": f"Tek yönlü iletişim (gelen): %{round((1 - sent_ratio) * 100, 1)}"
                        })

        # Pattern 3: Late night communication
        # TODO: Implement when we have message timestamps with time component

        return patterns

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """
        Export the entire network in Cytoscape.js compatible JSON format.
        """
        return {
            "elements": {
                "nodes": [node.to_cytoscape() for node in self.nodes.values()],
                "edges": [edge.to_cytoscape() for edge in self.edges.values()]
            },
            "metadata": {
                "caseId": self.case_id,
                "totalNodes": len(self.nodes),
                "totalEdges": len(self.edges),
                "clusters": [
                    {
                        "id": c.cluster_id,
                        "label": c.label,
                        "nodeCount": len(c.node_ids),
                        "color": c.color
                    }
                    for c in self.clusters
                ],
                "generatedAt": datetime.now().isoformat()
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for the network.
        """
        if not self.nodes:
            return {
                "totalNodes": 0,
                "totalEdges": 0,
                "totalMessages": 0,
                "totalCalls": 0
            }

        total_messages = sum(n.total_messages for n in self.nodes.values()) // 2  # Divide by 2 (counted twice)
        total_calls = sum(n.total_calls for n in self.nodes.values()) // 2

        # Find most active contacts
        top_contacts = sorted(
            self.nodes.values(),
            key=lambda n: n.total_messages,
            reverse=True
        )[:10]

        return {
            "totalNodes": len(self.nodes),
            "totalEdges": len(self.edges),
            "totalMessages": total_messages,
            "totalCalls": total_calls,
            "avgMessagesPerContact": round(total_messages / len(self.nodes), 1) if self.nodes else 0,
            "topContacts": [
                {
                    "id": c.id,
                    "label": c.label,
                    "messages": c.total_messages,
                    "platforms": c.platforms
                }
                for c in top_contacts
            ],
            "platformDistribution": self._get_platform_distribution(),
            "clusters": len(self.clusters)
        }

    # Private methods

    def _generate_node_id(self, identifier: str) -> str:
        """Generate a consistent node ID from an identifier"""
        # Normalize phone numbers
        if identifier:
            normalized = ''.join(c for c in str(identifier) if c.isalnum() or c == '@')
            return hashlib.md5(normalized.lower().encode()).hexdigest()[:12]
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:12]

    def _get_or_create_edge(
        self,
        source_id: str,
        target_id: str,
        platform: Platform
    ) -> NetworkEdge:
        """Get existing edge or create new one"""
        # Ensure consistent edge direction
        if source_id > target_id:
            source_id, target_id = target_id, source_id

        edge_key = (source_id, target_id)

        if edge_key in self._edge_index:
            return self.edges[self._edge_index[edge_key]]

        # Create new edge
        edge_id = f"e_{source_id}_{target_id}"
        edge = NetworkEdge(
            id=edge_id,
            source=source_id,
            target=target_id,
            platform=platform
        )

        self.edges[edge_id] = edge
        self._edge_index[edge_key] = edge_id

        return edge

    def _calculate_edge_weight(self, edge: NetworkEdge) -> float:
        """Calculate edge weight based on interactions"""
        # Messages: base weight
        # Calls: 5x weight (more significant)
        # Duration: 0.01x weight per second
        weight = (
            edge.message_count +
            (edge.call_count * 5) +
            (edge.call_duration_seconds * 0.01)
        )
        return max(1.0, weight)

    def _get_platform_distribution(self) -> Dict[str, int]:
        """Get message count per platform"""
        distribution = defaultdict(int)
        for edge in self.edges.values():
            distribution[edge.platform.value] += edge.message_count
        return dict(distribution)

    def _kmeans(self, features: List[List[float]], k: int, max_iter: int = 100) -> List[int]:
        """
        Simple K-means clustering implementation.
        Returns cluster assignment for each feature vector.
        """
        import random

        if not features or k <= 0:
            return [0] * len(features)

        n = len(features)
        dim = len(features[0])

        # Initialize centroids randomly
        centroid_indices = random.sample(range(n), min(k, n))
        centroids = [features[i][:] for i in centroid_indices]

        assignments = [0] * n

        for _ in range(max_iter):
            # Assign points to nearest centroid
            new_assignments = []
            for point in features:
                min_dist = float('inf')
                best_cluster = 0
                for cluster_id, centroid in enumerate(centroids):
                    dist = sum((a - b) ** 2 for a, b in zip(point, centroid))
                    if dist < min_dist:
                        min_dist = dist
                        best_cluster = cluster_id
                new_assignments.append(best_cluster)

            # Check convergence
            if new_assignments == assignments:
                break
            assignments = new_assignments

            # Update centroids
            for cluster_id in range(k):
                cluster_points = [features[i] for i, c in enumerate(assignments) if c == cluster_id]
                if cluster_points:
                    centroids[cluster_id] = [
                        sum(p[d] for p in cluster_points) / len(cluster_points)
                        for d in range(dim)
                    ]

        return assignments


# Convenience functions

def build_contact_network(
    case_id: str,
    messages: List[Dict[str, Any]],
    calls: Optional[List[Dict[str, Any]]] = None,
    contacts: Optional[List[Dict[str, Any]]] = None,
    primary_contact: Optional[str] = None
) -> ContactNetworkGraph:
    """
    Build a contact network from raw forensic data.

    Args:
        case_id: Case identifier
        messages: List of message dicts with sender, receiver, platform, timestamp
        calls: Optional list of call dicts with caller, receiver, duration, timestamp
        contacts: Optional list of contact dicts with identifier, name, phone, email
        primary_contact: Optional primary contact identifier (case subject)

    Returns:
        ContactNetworkGraph ready for visualization
    """
    graph = ContactNetworkGraph(case_id, primary_contact)

    # Add known contacts first
    if contacts:
        for contact in contacts:
            graph.add_contact(
                identifier=contact.get("identifier") or contact.get("phone") or contact.get("email"),
                name=contact.get("name", "Unknown"),
                platform=contact.get("platform", "unknown"),
                phone=contact.get("phone"),
                email=contact.get("email"),
                node_type=NodeType.FAMILY if contact.get("is_family") else NodeType.CONTACT
            )

    # Add primary contact
    if primary_contact:
        graph.add_contact(
            identifier=primary_contact,
            name="Primary (Client)",
            node_type=NodeType.PRIMARY
        )

    # Process messages
    for msg in messages:
        sender = msg.get("sender") or msg.get("from")
        receiver = msg.get("receiver") or msg.get("to")
        if sender and receiver:
            graph.add_message(
                sender_id=sender,
                receiver_id=receiver,
                platform=msg.get("platform", "unknown"),
                timestamp=msg.get("timestamp"),
                is_outgoing=msg.get("is_outgoing", True)
            )

    # Process calls
    if calls:
        for call in calls:
            caller = call.get("caller") or call.get("from")
            receiver = call.get("receiver") or call.get("to")
            if caller and receiver:
                graph.add_call(
                    caller_id=caller,
                    receiver_id=receiver,
                    duration_seconds=call.get("duration", 0),
                    timestamp=call.get("timestamp"),
                    is_outgoing=call.get("is_outgoing", True)
                )

    # Calculate centrality
    graph.calculate_centrality()

    # Detect clusters
    n_clusters = min(5, max(2, len(graph.nodes) // 5))
    graph.detect_clusters(n_clusters)

    return graph


def calculate_centrality(graph: ContactNetworkGraph) -> Dict[str, float]:
    """Calculate centrality scores for a network graph"""
    return graph.calculate_centrality()


def detect_clusters(graph: ContactNetworkGraph, n_clusters: int = 3) -> List[ClusterResult]:
    """Detect clusters in a network graph"""
    return graph.detect_clusters(n_clusters)
