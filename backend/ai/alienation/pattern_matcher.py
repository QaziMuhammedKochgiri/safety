"""
Pattern Matcher for Parental Alienation Detection
NLP-based pattern matching for identifying alienation tactics in messages.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from enum import Enum
from datetime import datetime
import re
import hashlib
from collections import defaultdict

from .tactics_database import AlienationTacticDB, ManipulationTactic, TacticCategory


class PatternType(str, Enum):
    """Types of patterns detected."""
    KEYWORD_MATCH = "keyword_match"
    PHRASE_MATCH = "phrase_match"
    SEMANTIC_MATCH = "semantic_match"
    CONTEXTUAL_MATCH = "contextual_match"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    TEMPORAL_PATTERN = "temporal_pattern"


class MatchConfidence(str, Enum):
    """Confidence levels for matches."""
    LOW = "low"  # 0.0 - 0.4
    MEDIUM = "medium"  # 0.4 - 0.7
    HIGH = "high"  # 0.7 - 0.9
    VERY_HIGH = "very_high"  # 0.9 - 1.0


@dataclass
class PatternMatch:
    """A detected pattern match."""
    match_id: str
    tactic_id: str
    tactic_name: str
    category: TacticCategory
    pattern_type: PatternType
    confidence: float
    confidence_level: MatchConfidence
    matched_text: str
    context_before: str
    context_after: str
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    sender: Optional[str] = None
    keywords_found: List[str] = field(default_factory=list)
    indicators_matched: List[str] = field(default_factory=list)
    counter_indicators: List[str] = field(default_factory=list)
    severity_score: int = 0
    explanation: str = ""


@dataclass
class MessageAnalysis:
    """Analysis result for a single message."""
    message_id: str
    content: str
    sender: str
    timestamp: datetime
    matches: List[PatternMatch]
    overall_risk_score: float
    primary_tactic: Optional[str] = None
    language_detected: str = "en"


class PatternMatcher:
    """NLP-based pattern matcher for alienation detection."""

    def __init__(self, db: Optional[AlienationTacticDB] = None):
        self.db = db or AlienationTacticDB()
        self._compile_patterns()
        self._build_keyword_index()

    def _compile_patterns(self):
        """Compile regex patterns for all tactics."""
        self.compiled_patterns: Dict[str, Dict[str, List[re.Pattern]]] = {}

        for tactic_id, tactic in self.db.tactics.items():
            self.compiled_patterns[tactic_id] = {}

            for lang, keywords in tactic.keywords.items():
                patterns = []
                for keyword in keywords:
                    # Create flexible pattern that matches variations
                    escaped = re.escape(keyword)
                    # Allow for flexible whitespace and punctuation
                    flexible = escaped.replace(r'\ ', r'\s+')
                    pattern = re.compile(flexible, re.IGNORECASE | re.UNICODE)
                    patterns.append(pattern)

                self.compiled_patterns[tactic_id][lang] = patterns

    def _build_keyword_index(self):
        """Build inverted index for fast keyword lookup."""
        self.keyword_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

        for tactic_id, tactic in self.db.tactics.items():
            for lang, keywords in tactic.keywords.items():
                for keyword in keywords:
                    # Normalize keyword
                    normalized = keyword.lower().strip()
                    self.keyword_index[normalized].append((tactic_id, lang))

    def detect_language(self, text: str) -> str:
        """Simple language detection based on character patterns."""
        # Turkish-specific characters
        turkish_chars = set('çğıöşüÇĞİÖŞÜ')
        # German-specific characters
        german_chars = set('äöüßÄÖÜ')

        text_chars = set(text)

        if text_chars & turkish_chars:
            return "tr"
        elif text_chars & german_chars:
            return "de"
        else:
            return "en"

    def analyze_message(
        self,
        content: str,
        message_id: Optional[str] = None,
        sender: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        language: Optional[str] = None
    ) -> MessageAnalysis:
        """Analyze a single message for alienation patterns."""
        if not language:
            language = self.detect_language(content)

        matches = []
        content_lower = content.lower()

        # Phase 1: Keyword matching
        keyword_matches = self._find_keyword_matches(content, content_lower, language)
        matches.extend(keyword_matches)

        # Phase 2: Phrase matching
        phrase_matches = self._find_phrase_matches(content, language)
        matches.extend(phrase_matches)

        # Phase 3: Contextual analysis
        contextual_matches = self._analyze_context(content, language, keyword_matches)
        matches.extend(contextual_matches)

        # Remove duplicates and merge overlapping matches
        matches = self._deduplicate_matches(matches)

        # Calculate overall risk score
        risk_score = self._calculate_risk_score(matches)

        # Determine primary tactic
        primary_tactic = None
        if matches:
            # Get tactic with highest combined score
            tactic_scores = defaultdict(float)
            for match in matches:
                tactic_scores[match.tactic_id] += match.confidence * match.severity_score
            primary_tactic = max(tactic_scores, key=tactic_scores.get)

        return MessageAnalysis(
            message_id=message_id or self._generate_id(content),
            content=content,
            sender=sender or "unknown",
            timestamp=timestamp or datetime.utcnow(),
            matches=matches,
            overall_risk_score=risk_score,
            primary_tactic=primary_tactic,
            language_detected=language
        )

    def _find_keyword_matches(
        self,
        content: str,
        content_lower: str,
        language: str
    ) -> List[PatternMatch]:
        """Find keyword matches in content."""
        matches = []

        for tactic_id, lang_patterns in self.compiled_patterns.items():
            patterns = lang_patterns.get(language, lang_patterns.get("en", []))
            tactic = self.db.get_tactic(tactic_id)

            for pattern in patterns:
                for match in pattern.finditer(content_lower):
                    # Get context
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context_before = content[start:match.start()]
                    context_after = content[match.end():end]
                    matched_text = content[match.start():match.end()]

                    # Calculate confidence based on match quality
                    confidence = self._calculate_keyword_confidence(
                        matched_text, tactic, content
                    )

                    pattern_match = PatternMatch(
                        match_id=self._generate_id(f"{tactic_id}_{match.start()}"),
                        tactic_id=tactic_id,
                        tactic_name=tactic.name,
                        category=tactic.category,
                        pattern_type=PatternType.KEYWORD_MATCH,
                        confidence=confidence,
                        confidence_level=self._get_confidence_level(confidence),
                        matched_text=matched_text,
                        context_before=context_before,
                        context_after=context_after,
                        keywords_found=[matched_text],
                        severity_score=tactic.severity_base,
                        explanation=f"Keyword '{matched_text}' matches tactic '{tactic.name}'"
                    )
                    matches.append(pattern_match)

        return matches

    def _find_phrase_matches(
        self,
        content: str,
        language: str
    ) -> List[PatternMatch]:
        """Find phrase matches using example phrases."""
        matches = []
        content_lower = content.lower()

        for tactic_id, tactic in self.db.tactics.items():
            phrases = tactic.example_phrases.get(language, tactic.example_phrases.get("en", []))

            for phrase in phrases:
                phrase_lower = phrase.lower()
                # Use fuzzy matching for phrases
                similarity = self._calculate_phrase_similarity(content_lower, phrase_lower)

                if similarity > 0.6:  # Threshold for phrase match
                    # Find approximate position
                    pos = self._find_approximate_position(content_lower, phrase_lower)

                    pattern_match = PatternMatch(
                        match_id=self._generate_id(f"{tactic_id}_phrase_{phrase[:20]}"),
                        tactic_id=tactic_id,
                        tactic_name=tactic.name,
                        category=tactic.category,
                        pattern_type=PatternType.PHRASE_MATCH,
                        confidence=similarity,
                        confidence_level=self._get_confidence_level(similarity),
                        matched_text=phrase,
                        context_before=content[:pos] if pos > 0 else "",
                        context_after=content[pos:pos+100] if pos >= 0 else content[:100],
                        severity_score=tactic.severity_base,
                        explanation=f"Message resembles alienation phrase: '{phrase}'"
                    )
                    matches.append(pattern_match)

        return matches

    def _analyze_context(
        self,
        content: str,
        language: str,
        existing_matches: List[PatternMatch]
    ) -> List[PatternMatch]:
        """Analyze contextual patterns that indicate alienation."""
        matches = []

        # Check for specific contextual patterns
        contextual_patterns = [
            # Pattern for "us vs them" mentality
            {
                "pattern": r"(it'?s?\s+just\s+(?:you\s+and\s+me|us)|we'?re?\s+(?:all\s+)?alone|against\s+us)",
                "tactic_id": "WEP003",
                "type": PatternType.CONTEXTUAL_MATCH,
                "explanation": "Us vs them mentality detected"
            },
            # Pattern for forced choice
            {
                "pattern": r"(who\s+do\s+you\s+(?:love|prefer)|choose\s+(?:me|between)|whose\s+side)",
                "tactic_id": "EMO002",
                "type": PatternType.CONTEXTUAL_MATCH,
                "explanation": "Forced loyalty choice detected"
            },
            # Pattern for fear instillation
            {
                "pattern": r"(be\s+careful|dangerous|might\s+hurt|not\s+safe|scared\s+for\s+you)",
                "tactic_id": "EMO003",
                "type": PatternType.CONTEXTUAL_MATCH,
                "explanation": "Fear-inducing language detected"
            },
            # Pattern for guilt induction
            {
                "pattern": r"(so\s+lonely|miss\s+you\s+so\s+much|all\s+alone|abandoned|don'?t\s+forget\s+me)",
                "tactic_id": "EMO001",
                "type": PatternType.CONTEXTUAL_MATCH,
                "explanation": "Guilt-inducing language detected"
            },
            # Pattern for using child as messenger
            {
                "pattern": r"(tell\s+(?:your|him|her)\s+(?:father|mother|dad|mom)|give\s+(?:him|her)\s+this\s+message)",
                "tactic_id": "WEP001",
                "type": PatternType.CONTEXTUAL_MATCH,
                "explanation": "Child being used as messenger"
            },
            # Pattern for interrogation
            {
                "pattern": r"(what\s+did\s+(?:he|she|they)\s+(?:do|say|buy)|who\s+was\s+(?:there|with)|anyone\s+new)",
                "tactic_id": "WEP002",
                "type": PatternType.CONTEXTUAL_MATCH,
                "explanation": "Interrogation pattern detected"
            }
        ]

        content_lower = content.lower()

        for ctx_pattern in contextual_patterns:
            regex = re.compile(ctx_pattern["pattern"], re.IGNORECASE)
            for match in regex.finditer(content_lower):
                tactic = self.db.get_tactic(ctx_pattern["tactic_id"])
                if not tactic:
                    continue

                pattern_match = PatternMatch(
                    match_id=self._generate_id(f"ctx_{ctx_pattern['tactic_id']}_{match.start()}"),
                    tactic_id=ctx_pattern["tactic_id"],
                    tactic_name=tactic.name,
                    category=tactic.category,
                    pattern_type=ctx_pattern["type"],
                    confidence=0.75,  # Base confidence for contextual matches
                    confidence_level=MatchConfidence.HIGH,
                    matched_text=content[match.start():match.end()],
                    context_before=content[max(0, match.start()-30):match.start()],
                    context_after=content[match.end():min(len(content), match.end()+30)],
                    severity_score=tactic.severity_base,
                    explanation=ctx_pattern["explanation"]
                )
                matches.append(pattern_match)

        return matches

    def _calculate_keyword_confidence(
        self,
        matched_text: str,
        tactic: ManipulationTactic,
        full_content: str
    ) -> float:
        """Calculate confidence score for keyword match."""
        base_confidence = 0.5

        # Boost for longer matches (more specific)
        word_count = len(matched_text.split())
        if word_count >= 3:
            base_confidence += 0.2
        elif word_count >= 2:
            base_confidence += 0.1

        # Boost if multiple keywords from same tactic found
        all_keywords = []
        for keywords in tactic.keywords.values():
            all_keywords.extend(keywords)

        content_lower = full_content.lower()
        keywords_found = sum(1 for kw in all_keywords if kw.lower() in content_lower)
        if keywords_found >= 3:
            base_confidence += 0.2
        elif keywords_found >= 2:
            base_confidence += 0.1

        # Check for counter-indicators that reduce confidence
        for counter in tactic.counter_indicators:
            if counter.lower() in content_lower:
                base_confidence -= 0.15

        return min(0.95, max(0.1, base_confidence))

    def _calculate_phrase_similarity(self, text: str, phrase: str) -> float:
        """Calculate similarity between text and phrase using n-grams."""
        def get_ngrams(s: str, n: int = 3) -> Set[str]:
            s = s.lower().strip()
            return set(s[i:i+n] for i in range(len(s) - n + 1))

        if len(phrase) < 3 or len(text) < 3:
            return 0.0

        phrase_ngrams = get_ngrams(phrase)
        text_ngrams = get_ngrams(text)

        if not phrase_ngrams:
            return 0.0

        intersection = phrase_ngrams & text_ngrams
        return len(intersection) / len(phrase_ngrams)

    def _find_approximate_position(self, text: str, phrase: str) -> int:
        """Find approximate position of phrase in text."""
        # Try direct search first
        pos = text.find(phrase)
        if pos >= 0:
            return pos

        # Try finding first few words
        words = phrase.split()[:3]
        if words:
            search_term = ' '.join(words)
            pos = text.find(search_term)
            if pos >= 0:
                return pos

        return -1

    def _get_confidence_level(self, confidence: float) -> MatchConfidence:
        """Convert numeric confidence to level."""
        if confidence >= 0.9:
            return MatchConfidence.VERY_HIGH
        elif confidence >= 0.7:
            return MatchConfidence.HIGH
        elif confidence >= 0.4:
            return MatchConfidence.MEDIUM
        else:
            return MatchConfidence.LOW

    def _deduplicate_matches(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Remove duplicate matches, keeping highest confidence."""
        seen = {}
        for match in matches:
            key = (match.tactic_id, match.matched_text[:50])
            if key not in seen or match.confidence > seen[key].confidence:
                seen[key] = match
        return list(seen.values())

    def _calculate_risk_score(self, matches: List[PatternMatch]) -> float:
        """Calculate overall risk score from matches."""
        if not matches:
            return 0.0

        # Weight by confidence and severity
        weighted_scores = []
        for match in matches:
            weighted = match.confidence * match.severity_score
            weighted_scores.append(weighted)

        # Normalize to 0-10 scale
        total = sum(weighted_scores)
        # Cap at reasonable maximum (5 high-confidence severe matches)
        max_expected = 5 * 0.9 * 10
        normalized = min(10.0, (total / max_expected) * 10)

        return round(normalized, 2)

    def _generate_id(self, seed: str) -> str:
        """Generate unique ID from seed."""
        return hashlib.md5(seed.encode()).hexdigest()[:12]

    def analyze_conversation(
        self,
        messages: List[Dict[str, Any]],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a full conversation for alienation patterns."""
        analyses = []
        all_matches = []
        tactic_frequency = defaultdict(int)
        severity_over_time = []

        for msg in messages:
            analysis = self.analyze_message(
                content=msg.get("content", msg.get("body", "")),
                message_id=msg.get("id"),
                sender=msg.get("sender"),
                timestamp=msg.get("timestamp"),
                language=language
            )
            analyses.append(analysis)
            all_matches.extend(analysis.matches)

            for match in analysis.matches:
                tactic_frequency[match.tactic_id] += 1

            if analysis.matches:
                severity_over_time.append({
                    "timestamp": analysis.timestamp.isoformat() if analysis.timestamp else None,
                    "risk_score": analysis.overall_risk_score,
                    "match_count": len(analysis.matches)
                })

        # Calculate conversation-level statistics
        total_messages = len(messages)
        messages_with_matches = sum(1 for a in analyses if a.matches)
        overall_risk = sum(a.overall_risk_score for a in analyses) / total_messages if total_messages else 0

        # Identify primary tactics
        primary_tactics = sorted(
            tactic_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Category breakdown
        category_counts = defaultdict(int)
        for match in all_matches:
            category_counts[match.category.value] += 1

        return {
            "total_messages": total_messages,
            "messages_with_matches": messages_with_matches,
            "detection_rate": messages_with_matches / total_messages if total_messages else 0,
            "overall_risk_score": round(overall_risk, 2),
            "total_matches": len(all_matches),
            "primary_tactics": [
                {
                    "tactic_id": tid,
                    "tactic_name": self.db.get_tactic(tid).name if self.db.get_tactic(tid) else tid,
                    "frequency": freq
                }
                for tid, freq in primary_tactics
            ],
            "category_breakdown": dict(category_counts),
            "severity_timeline": severity_over_time,
            "analyses": analyses
        }

    def get_high_risk_matches(
        self,
        messages: List[Dict[str, Any]],
        min_confidence: float = 0.7,
        min_severity: int = 7
    ) -> List[PatternMatch]:
        """Get only high-risk matches from messages."""
        high_risk = []

        for msg in messages:
            analysis = self.analyze_message(
                content=msg.get("content", msg.get("body", "")),
                message_id=msg.get("id"),
                sender=msg.get("sender"),
                timestamp=msg.get("timestamp")
            )

            for match in analysis.matches:
                if match.confidence >= min_confidence and match.severity_score >= min_severity:
                    high_risk.append(match)

        return high_risk

    def generate_evidence_report(
        self,
        matches: List[PatternMatch],
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """Generate evidence report from matches."""
        evidence = []

        for match in sorted(matches, key=lambda m: (m.severity_score, m.confidence), reverse=True):
            tactic = self.db.get_tactic(match.tactic_id)

            entry = {
                "tactic": match.tactic_name,
                "category": match.category.value,
                "severity": match.severity_score,
                "confidence": f"{match.confidence:.0%}",
                "matched_text": match.matched_text,
                "explanation": match.explanation
            }

            if include_context:
                entry["context"] = f"...{match.context_before}[{match.matched_text}]{match.context_after}..."

            if tactic:
                entry["indicators"] = tactic.indicators[:3]  # Top 3 indicators

            evidence.append(entry)

        return evidence
