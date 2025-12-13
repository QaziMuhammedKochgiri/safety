"""
Relevance Scorer
AI-based relevance scoring for court evidence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import re
import hashlib


class RelevanceFactor(str, Enum):
    """Factors affecting relevance score."""
    LEGAL_ISSUE_MATCH = "legal_issue_match"
    KEYWORD_PRESENCE = "keyword_presence"
    TEMPORAL_PROXIMITY = "temporal_proximity"
    PARTICIPANT_RELEVANCE = "participant_relevance"
    CATEGORY_MATCH = "category_match"
    EVIDENCE_TYPE_MATCH = "evidence_type_match"
    AUTHENTICATION_STATUS = "authentication_status"
    CORROBORATION = "corroboration"
    PATTERN_DETECTION = "pattern_detection"
    SEVERITY_INDICATOR = "severity_indicator"
    EXPERT_NATURE = "expert_nature"
    OFFICIAL_STATUS = "official_status"
    MEDIA_RICHNESS = "media_richness"
    CHAIN_OF_CUSTODY = "chain_of_custody"


@dataclass
class RelevanceScore:
    """Detailed relevance score for evidence."""
    item_id: str
    overall_score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    factor_scores: Dict[RelevanceFactor, float]
    factor_explanations: Dict[RelevanceFactor, str]
    matched_keywords: List[str]
    matched_patterns: List[str]
    legal_issues_covered: List[str]
    scoring_timestamp: datetime
    scoring_context: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ScoringContext:
    """Context for scoring evidence."""
    case_id: str
    target_issues: List[str]
    key_participants: List[str]
    key_dates: List[datetime]
    key_locations: List[str]
    existing_evidence_ids: List[str]
    court_format: str = "german"
    prioritize_recent: bool = True
    prioritize_corroborated: bool = True
    custom_keywords: List[str] = field(default_factory=list)
    custom_patterns: List[str] = field(default_factory=list)


# Keyword databases by legal issue
ISSUE_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "parental_alienation": {
        "high_impact": [
            "alienation", "brainwash", "poison", "manipulate",
            "turn against", "don't love", "hate your", "bad parent",
            "not your real", "chose sides", "loyalty conflict"
        ],
        "medium_impact": [
            "badmouth", "criticize", "undermine", "interfere",
            "won't let see", "refuses contact", "blocks calls",
            "deletes messages", "changes schedule"
        ],
        "low_impact": [
            "disagree", "conflict", "argument", "different rules",
            "other house", "their way"
        ]
    },
    "domestic_violence": {
        "high_impact": [
            "hit", "punch", "slap", "choke", "strangle",
            "threaten to kill", "weapon", "knife", "gun",
            "hospital", "emergency room", "bruise", "injury"
        ],
        "medium_impact": [
            "push", "shove", "grab", "throw", "break",
            "scared", "afraid", "intimidate", "control",
            "isolate", "stalk", "follow"
        ],
        "low_impact": [
            "yell", "scream", "angry", "argument", "fight"
        ]
    },
    "child_abuse": {
        "high_impact": [
            "abuse", "molest", "sexual", "inappropriate touch",
            "hit child", "beat", "burn", "bruise on child",
            "child afraid", "child crying"
        ],
        "medium_impact": [
            "discipline", "punishment", "spanking", "belt",
            "locked in room", "withheld food", "excessive"
        ],
        "low_impact": [
            "strict", "harsh", "yelled at child"
        ]
    },
    "child_neglect": {
        "high_impact": [
            "left alone", "unsupervised", "no food", "hungry",
            "dirty", "unwashed", "missed school", "no medical",
            "abandoned", "dangerous situation"
        ],
        "medium_impact": [
            "late pickup", "forgot appointment", "no lunch",
            "wrong clothes", "no supervision"
        ],
        "low_impact": [
            "busy", "distracted", "not paying attention"
        ]
    },
    "substance_abuse": {
        "high_impact": [
            "drunk", "high", "intoxicated", "passed out",
            "drugs", "cocaine", "heroin", "meth", "pills",
            "overdose", "rehab", "arrest for DUI"
        ],
        "medium_impact": [
            "drinking", "alcohol", "beer", "wine", "smells like",
            "marijuana", "weed", "impaired"
        ],
        "low_impact": [
            "party", "drinking socially"
        ]
    }
}

# Pattern templates for NLP matching
EVIDENCE_PATTERNS: Dict[str, List[Dict[str, Any]]] = {
    "threat_pattern": [
        {"regex": r"(i('ll|will)?\s+(kill|hurt|destroy|ruin))", "severity": 0.9},
        {"regex": r"(you('ll)?\s+never\s+see\s+(him|her|them|the\s+kids?))", "severity": 0.8},
        {"regex": r"(watch\s+(what|your)\s+(happens|back|step))", "severity": 0.7},
        {"regex": r"(you('ll)?\s+(be\s+sorry|regret))", "severity": 0.6}
    ],
    "alienation_pattern": [
        {"regex": r"(your\s+(mom|dad|mother|father)\s+(doesn't|does\s+not)\s+(love|care|want))", "severity": 0.9},
        {"regex": r"((he|she)\s+(is|was)\s+(never|not)\s+there\s+for\s+you)", "severity": 0.8},
        {"regex": r"(don't\s+tell\s+(your\s+)?(mom|dad|mother|father))", "severity": 0.7},
        {"regex": r"(we\s+don't\s+need\s+(him|her))", "severity": 0.7},
        {"regex": r"(chose|choose)\s+(me|us)\s+(over|instead))", "severity": 0.8}
    ],
    "abuse_pattern": [
        {"regex": r"(hit|slap|punch|kick|hurt)\s+(me|him|her|the\s+child)", "severity": 0.9},
        {"regex": r"(bruise|mark|injury)\s+(on|from)", "severity": 0.8},
        {"regex": r"(scared|afraid)\s+of\s+(him|her|daddy|mommy)", "severity": 0.7},
        {"regex": r"(touched|touch)\s+(me|inappropriately|wrong)", "severity": 0.95}
    ],
    "neglect_pattern": [
        {"regex": r"(left|alone|unsupervised)\s+(for\s+)?\d+\s*(hours?|minutes?)", "severity": 0.8},
        {"regex": r"(no\s+(food|lunch|dinner|breakfast))", "severity": 0.7},
        {"regex": r"(didn't|did\s+not)\s+(pick\s+up|show\s+up|come)", "severity": 0.6},
        {"regex": r"(missed|miss)\s+(school|doctor|appointment)", "severity": 0.5}
    ],
    "interference_pattern": [
        {"regex": r"(won't|will\s+not|refuse)\s+(let|allow)\s+(you\s+)?(see|call|contact)", "severity": 0.8},
        {"regex": r"(blocked|block)\s+(your\s+)?(number|calls|messages)", "severity": 0.7},
        {"regex": r"(changed|change)\s+(the\s+)?(schedule|plans|time)", "severity": 0.5},
        {"regex": r"(can't|cannot)\s+reach\s+(the\s+)?(kids?|children?)", "severity": 0.7}
    ]
}


class RelevanceScorer:
    """AI-based relevance scoring for evidence."""

    def __init__(self):
        self.scoring_cache: Dict[str, RelevanceScore] = {}
        self.compiled_patterns: Dict[str, List[Tuple]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for pattern_type, patterns in EVIDENCE_PATTERNS.items():
            self.compiled_patterns[pattern_type] = [
                (re.compile(p["regex"], re.IGNORECASE), p["severity"])
                for p in patterns
            ]

    def score_evidence(
        self,
        item_id: str,
        content: str,
        metadata: Dict[str, Any],
        context: ScoringContext
    ) -> RelevanceScore:
        """Calculate comprehensive relevance score for evidence."""
        factor_scores: Dict[RelevanceFactor, float] = {}
        factor_explanations: Dict[RelevanceFactor, str] = {}
        matched_keywords: List[str] = []
        matched_patterns: List[str] = []
        legal_issues_covered: List[str] = []
        recommendations: List[str] = []

        content_lower = content.lower() if content else ""

        # Score each factor
        # 1. Legal Issue Match
        issue_score, issue_keywords, covered_issues = self._score_legal_issues(
            content_lower, context.target_issues
        )
        factor_scores[RelevanceFactor.LEGAL_ISSUE_MATCH] = issue_score
        factor_explanations[RelevanceFactor.LEGAL_ISSUE_MATCH] = (
            f"Matched {len(covered_issues)} legal issues"
            if covered_issues else "No direct issue match"
        )
        matched_keywords.extend(issue_keywords)
        legal_issues_covered.extend(covered_issues)

        # 2. Keyword Presence
        keyword_score, custom_matches = self._score_keywords(
            content_lower, context.custom_keywords
        )
        factor_scores[RelevanceFactor.KEYWORD_PRESENCE] = keyword_score
        factor_explanations[RelevanceFactor.KEYWORD_PRESENCE] = (
            f"Found {len(custom_matches)} custom keywords"
            if custom_matches else "No custom keyword matches"
        )
        matched_keywords.extend(custom_matches)

        # 3. Pattern Detection
        pattern_score, patterns_found = self._score_patterns(content_lower)
        factor_scores[RelevanceFactor.PATTERN_DETECTION] = pattern_score
        factor_explanations[RelevanceFactor.PATTERN_DETECTION] = (
            f"Detected {len(patterns_found)} concerning patterns"
            if patterns_found else "No concerning patterns"
        )
        matched_patterns.extend(patterns_found)

        # 4. Temporal Proximity
        temporal_score = self._score_temporal_proximity(
            metadata.get("date_created"),
            context.key_dates
        )
        factor_scores[RelevanceFactor.TEMPORAL_PROXIMITY] = temporal_score
        factor_explanations[RelevanceFactor.TEMPORAL_PROXIMITY] = (
            "Close to key dates" if temporal_score > 0.5 else "Not near key dates"
        )

        # 5. Participant Relevance
        participant_score = self._score_participants(
            metadata.get("participants", []),
            context.key_participants
        )
        factor_scores[RelevanceFactor.PARTICIPANT_RELEVANCE] = participant_score
        factor_explanations[RelevanceFactor.PARTICIPANT_RELEVANCE] = (
            "Involves key participants" if participant_score > 0.5
            else "No key participants"
        )

        # 6. Category Match
        category = metadata.get("category", "")
        category_score = self._score_category(category, context.target_issues)
        factor_scores[RelevanceFactor.CATEGORY_MATCH] = category_score
        factor_explanations[RelevanceFactor.CATEGORY_MATCH] = (
            f"Category '{category}' is highly relevant"
            if category_score > 0.7 else f"Category '{category}' has moderate relevance"
        )

        # 7. Authentication Status
        auth_score = 1.0 if metadata.get("is_authenticated") else 0.3
        factor_scores[RelevanceFactor.AUTHENTICATION_STATUS] = auth_score
        factor_explanations[RelevanceFactor.AUTHENTICATION_STATUS] = (
            "Evidence is authenticated" if auth_score == 1.0
            else "Evidence not authenticated"
        )

        if auth_score < 1.0:
            recommendations.append("Consider authenticating this evidence")

        # 8. Corroboration
        corroboration_score = self._score_corroboration(
            item_id, metadata, context.existing_evidence_ids
        )
        factor_scores[RelevanceFactor.CORROBORATION] = corroboration_score
        factor_explanations[RelevanceFactor.CORROBORATION] = (
            "Corroborated by other evidence"
            if corroboration_score > 0.5 else "Standalone evidence"
        )

        # 9. Severity Indicator
        severity_score = self._calculate_severity(matched_patterns, matched_keywords)
        factor_scores[RelevanceFactor.SEVERITY_INDICATOR] = severity_score
        factor_explanations[RelevanceFactor.SEVERITY_INDICATOR] = (
            f"High severity content detected ({severity_score:.2f})"
            if severity_score > 0.7 else f"Moderate severity ({severity_score:.2f})"
        )

        # 10. Expert/Official Status
        if metadata.get("category") == "expert":
            factor_scores[RelevanceFactor.EXPERT_NATURE] = 0.9
            factor_explanations[RelevanceFactor.EXPERT_NATURE] = "Expert report"
        else:
            factor_scores[RelevanceFactor.EXPERT_NATURE] = 0.0
            factor_explanations[RelevanceFactor.EXPERT_NATURE] = "Not expert evidence"

        if metadata.get("category") == "official":
            factor_scores[RelevanceFactor.OFFICIAL_STATUS] = 0.9
            factor_explanations[RelevanceFactor.OFFICIAL_STATUS] = "Official document"
        else:
            factor_scores[RelevanceFactor.OFFICIAL_STATUS] = 0.0
            factor_explanations[RelevanceFactor.OFFICIAL_STATUS] = "Not official"

        # 11. Media Richness
        media_score = self._score_media_richness(metadata)
        factor_scores[RelevanceFactor.MEDIA_RICHNESS] = media_score
        factor_explanations[RelevanceFactor.MEDIA_RICHNESS] = (
            "Rich media evidence" if media_score > 0.5 else "Text-only evidence"
        )

        # 12. Chain of Custody
        custody_score = self._score_chain_of_custody(metadata.get("chain_of_custody", []))
        factor_scores[RelevanceFactor.CHAIN_OF_CUSTODY] = custody_score
        factor_explanations[RelevanceFactor.CHAIN_OF_CUSTODY] = (
            "Complete chain of custody" if custody_score > 0.8
            else "Incomplete chain of custody"
        )

        if custody_score < 0.8:
            recommendations.append("Document chain of custody more thoroughly")

        # Calculate overall score with weights
        overall_score = self._calculate_overall_score(factor_scores)

        # Calculate confidence
        confidence = self._calculate_confidence(factor_scores, content_lower)

        # Generate additional recommendations
        recommendations.extend(
            self._generate_recommendations(
                factor_scores, legal_issues_covered, context
            )
        )

        score = RelevanceScore(
            item_id=item_id,
            overall_score=overall_score,
            confidence=confidence,
            factor_scores=factor_scores,
            factor_explanations=factor_explanations,
            matched_keywords=list(set(matched_keywords)),
            matched_patterns=list(set(matched_patterns)),
            legal_issues_covered=legal_issues_covered,
            scoring_timestamp=datetime.utcnow(),
            scoring_context=context.case_id,
            recommendations=recommendations
        )

        self.scoring_cache[item_id] = score
        return score

    def _score_legal_issues(
        self,
        content: str,
        target_issues: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Score content against legal issues."""
        total_score = 0.0
        matched_keywords = []
        covered_issues = []

        for issue in target_issues:
            issue_keywords = ISSUE_KEYWORDS.get(issue, {})

            # High impact keywords
            high_matches = [
                kw for kw in issue_keywords.get("high_impact", [])
                if kw.lower() in content
            ]
            if high_matches:
                total_score += 0.4
                matched_keywords.extend(high_matches)
                if issue not in covered_issues:
                    covered_issues.append(issue)

            # Medium impact keywords
            medium_matches = [
                kw for kw in issue_keywords.get("medium_impact", [])
                if kw.lower() in content
            ]
            if medium_matches:
                total_score += 0.2
                matched_keywords.extend(medium_matches)
                if issue not in covered_issues:
                    covered_issues.append(issue)

            # Low impact keywords
            low_matches = [
                kw for kw in issue_keywords.get("low_impact", [])
                if kw.lower() in content
            ]
            if low_matches:
                total_score += 0.1
                matched_keywords.extend(low_matches)

        return min(total_score, 1.0), matched_keywords, covered_issues

    def _score_keywords(
        self,
        content: str,
        custom_keywords: List[str]
    ) -> Tuple[float, List[str]]:
        """Score content against custom keywords."""
        if not custom_keywords:
            return 0.0, []

        matches = [kw for kw in custom_keywords if kw.lower() in content]
        score = min(len(matches) * 0.2, 1.0)
        return score, matches

    def _score_patterns(self, content: str) -> Tuple[float, List[str]]:
        """Score content against concerning patterns."""
        max_severity = 0.0
        patterns_found = []

        for pattern_type, patterns in self.compiled_patterns.items():
            for regex, severity in patterns:
                if regex.search(content):
                    max_severity = max(max_severity, severity)
                    patterns_found.append(pattern_type)
                    break  # One match per pattern type

        return max_severity, list(set(patterns_found))

    def _score_temporal_proximity(
        self,
        evidence_date: Optional[datetime],
        key_dates: List[datetime]
    ) -> float:
        """Score based on proximity to key dates."""
        if not evidence_date or not key_dates:
            return 0.0

        if isinstance(evidence_date, str):
            try:
                evidence_date = datetime.fromisoformat(evidence_date)
            except:
                return 0.0

        min_distance = float('inf')
        for key_date in key_dates:
            distance = abs((evidence_date - key_date).days)
            min_distance = min(min_distance, distance)

        # Score inversely proportional to distance
        if min_distance <= 1:
            return 1.0
        elif min_distance <= 7:
            return 0.9
        elif min_distance <= 30:
            return 0.7
        elif min_distance <= 90:
            return 0.5
        elif min_distance <= 365:
            return 0.3
        else:
            return 0.1

    def _score_participants(
        self,
        evidence_participants: List[str],
        key_participants: List[str]
    ) -> float:
        """Score based on participant relevance."""
        if not evidence_participants or not key_participants:
            return 0.0

        evidence_set = set(p.lower() for p in evidence_participants)
        key_set = set(p.lower() for p in key_participants)

        overlap = evidence_set & key_set
        if not overlap:
            return 0.0

        # More key participants = higher score
        return min(len(overlap) * 0.3, 1.0)

    def _score_category(
        self,
        category: str,
        target_issues: List[str]
    ) -> float:
        """Score category relevance to legal issues."""
        category_relevance = {
            "parental_alienation": {
                "communication": 0.9,
                "expert": 0.9,
                "witness": 0.7,
                "document": 0.5
            },
            "domestic_violence": {
                "medical": 0.9,
                "photograph": 0.9,
                "official": 0.9,
                "witness": 0.7
            },
            "child_abuse": {
                "medical": 0.9,
                "expert": 0.9,
                "official": 0.8,
                "photograph": 0.8
            },
            "custody": {
                "document": 0.9,
                "expert": 0.8,
                "educational": 0.7,
                "communication": 0.6
            }
        }

        max_score = 0.0
        for issue in target_issues:
            issue_relevance = category_relevance.get(issue, {})
            score = issue_relevance.get(category, 0.3)
            max_score = max(max_score, score)

        return max_score

    def _score_corroboration(
        self,
        item_id: str,
        metadata: Dict[str, Any],
        existing_evidence_ids: List[str]
    ) -> float:
        """Score based on corroborating evidence."""
        corroborating = metadata.get("corroborating_evidence", [])
        if not corroborating:
            return 0.2

        # Check how many corroborating items are in the existing pool
        valid_corroboration = [
            c for c in corroborating if c in existing_evidence_ids
        ]

        if len(valid_corroboration) >= 3:
            return 1.0
        elif len(valid_corroboration) >= 2:
            return 0.8
        elif len(valid_corroboration) >= 1:
            return 0.6
        else:
            return 0.2

    def _calculate_severity(
        self,
        patterns: List[str],
        keywords: List[str]
    ) -> float:
        """Calculate severity based on matched patterns and keywords."""
        severity = 0.0

        # Pattern-based severity
        severe_patterns = ["threat_pattern", "abuse_pattern"]
        if any(p in severe_patterns for p in patterns):
            severity += 0.5

        moderate_patterns = ["alienation_pattern", "neglect_pattern"]
        if any(p in moderate_patterns for p in patterns):
            severity += 0.3

        # Keyword-based severity
        severe_keywords = [
            "kill", "hurt", "abuse", "molest", "threaten",
            "hit", "punch", "drunk", "drugs"
        ]
        if any(kw in severe_keywords for kw in keywords):
            severity += 0.3

        return min(severity, 1.0)

    def _score_media_richness(self, metadata: Dict[str, Any]) -> float:
        """Score based on media type richness."""
        evidence_type = metadata.get("evidence_type", "")

        rich_types = ["video_recording", "audio_recording", "screenshot"]
        if evidence_type in rich_types:
            return 0.9

        moderate_types = ["photograph", "voice_message"]
        if evidence_type in moderate_types:
            return 0.6

        return 0.3  # Text-based

    def _score_chain_of_custody(
        self,
        chain: List[Dict[str, Any]]
    ) -> float:
        """Score chain of custody completeness."""
        if not chain:
            return 0.0

        # Check for required elements
        required_events = ["collected", "stored", "verified"]
        found_events = [e.get("event_type") for e in chain]

        coverage = len(set(found_events) & set(required_events)) / len(required_events)
        return coverage

    def _calculate_overall_score(
        self,
        factor_scores: Dict[RelevanceFactor, float]
    ) -> float:
        """Calculate weighted overall score."""
        weights = {
            RelevanceFactor.LEGAL_ISSUE_MATCH: 0.20,
            RelevanceFactor.KEYWORD_PRESENCE: 0.10,
            RelevanceFactor.PATTERN_DETECTION: 0.15,
            RelevanceFactor.TEMPORAL_PROXIMITY: 0.08,
            RelevanceFactor.PARTICIPANT_RELEVANCE: 0.08,
            RelevanceFactor.CATEGORY_MATCH: 0.10,
            RelevanceFactor.AUTHENTICATION_STATUS: 0.08,
            RelevanceFactor.CORROBORATION: 0.05,
            RelevanceFactor.SEVERITY_INDICATOR: 0.08,
            RelevanceFactor.EXPERT_NATURE: 0.03,
            RelevanceFactor.OFFICIAL_STATUS: 0.03,
            RelevanceFactor.MEDIA_RICHNESS: 0.01,
            RelevanceFactor.CHAIN_OF_CUSTODY: 0.01
        }

        total = 0.0
        for factor, score in factor_scores.items():
            weight = weights.get(factor, 0.05)
            total += score * weight

        return min(total, 1.0)

    def _calculate_confidence(
        self,
        factor_scores: Dict[RelevanceFactor, float],
        content: str
    ) -> float:
        """Calculate confidence in the score."""
        # More content = more confidence
        content_factor = min(len(content) / 500, 1.0) if content else 0.0

        # More non-zero factors = more confidence
        active_factors = sum(1 for s in factor_scores.values() if s > 0)
        factor_coverage = active_factors / len(factor_scores)

        # Higher scores in key factors = more confidence
        key_factors = [
            RelevanceFactor.LEGAL_ISSUE_MATCH,
            RelevanceFactor.PATTERN_DETECTION,
            RelevanceFactor.AUTHENTICATION_STATUS
        ]
        key_score = sum(factor_scores.get(f, 0) for f in key_factors) / len(key_factors)

        confidence = (content_factor * 0.3) + (factor_coverage * 0.3) + (key_score * 0.4)
        return min(confidence, 1.0)

    def _generate_recommendations(
        self,
        factor_scores: Dict[RelevanceFactor, float],
        legal_issues_covered: List[str],
        context: ScoringContext
    ) -> List[str]:
        """Generate recommendations to improve evidence."""
        recommendations = []

        # Check uncovered issues
        uncovered = set(context.target_issues) - set(legal_issues_covered)
        if uncovered:
            recommendations.append(
                f"Evidence doesn't directly address: {', '.join(uncovered)}"
            )

        # Authentication recommendation
        if factor_scores.get(RelevanceFactor.AUTHENTICATION_STATUS, 0) < 0.5:
            recommendations.append(
                "Authenticate evidence with digital signature or notarization"
            )

        # Corroboration recommendation
        if factor_scores.get(RelevanceFactor.CORROBORATION, 0) < 0.5:
            recommendations.append(
                "Seek corroborating evidence from independent sources"
            )

        return recommendations

    def batch_score(
        self,
        items: List[Dict[str, Any]],
        context: ScoringContext
    ) -> List[RelevanceScore]:
        """Score multiple evidence items."""
        scores = []
        for item in items:
            score = self.score_evidence(
                item_id=item.get("item_id", ""),
                content=item.get("content", ""),
                metadata=item.get("metadata", {}),
                context=context
            )
            scores.append(score)

        return sorted(scores, key=lambda s: s.overall_score, reverse=True)

    def get_cached_score(self, item_id: str) -> Optional[RelevanceScore]:
        """Get cached score for an item."""
        return self.scoring_cache.get(item_id)

    def clear_cache(self):
        """Clear the scoring cache."""
        self.scoring_cache.clear()

    def get_scoring_statistics(self) -> Dict[str, Any]:
        """Get statistics about scored items."""
        if not self.scoring_cache:
            return {"total_scored": 0}

        scores = list(self.scoring_cache.values())

        return {
            "total_scored": len(scores),
            "average_score": sum(s.overall_score for s in scores) / len(scores),
            "average_confidence": sum(s.confidence for s in scores) / len(scores),
            "high_relevance_count": sum(1 for s in scores if s.overall_score >= 0.7),
            "medium_relevance_count": sum(1 for s in scores if 0.4 <= s.overall_score < 0.7),
            "low_relevance_count": sum(1 for s in scores if s.overall_score < 0.4)
        }
