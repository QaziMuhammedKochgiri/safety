"""
AI-Powered Forensic Analyzer
Uses Claude API to analyze communications for child custody cases
Detects: threats, manipulation, abuse, parental alienation, and more
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)

class AIForensicAnalyzer:
    """
    AI-powered analysis for forensic evidence in child custody cases.

    Features:
    - Message content analysis (threats, manipulation, abuse detection)
    - Behavioral pattern detection
    - Risk scoring
    - Evidence prioritization
    - Multi-language support (DE, EN, TR)
    """

    RISK_CATEGORIES = {
        "threats": "Direct or implied threats to child or parent",
        "manipulation": "Psychological manipulation or gaslighting",
        "parental_alienation": "Attempts to alienate child from other parent",
        "neglect_indicators": "Signs of child neglect",
        "abuse_indicators": "Signs of physical, emotional, or sexual abuse",
        "substance_abuse": "References to drug or alcohol abuse",
        "financial_coercion": "Financial manipulation or threats",
        "custody_interference": "Attempts to interfere with custody arrangements",
        "inappropriate_content": "Inappropriate content shared with/about child",
        "documentation_value": "High evidentiary value for court"
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI analyzer with Anthropic API key"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No Anthropic API key found. AI analysis will be limited.")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

        self.model = "claude-sonnet-4-20250514"
        self.analysis_cache = {}

    async def analyze_messages(
        self,
        messages: List[Dict],
        context: Dict,
        language: str = "de"
    ) -> Dict:
        """
        Analyze a batch of messages for forensic relevance.

        Args:
            messages: List of message dictionaries
            context: Case context (client info, custody details)
            language: Output language (de, en, tr)

        Returns:
            Comprehensive analysis results
        """
        if not self.client:
            return self._fallback_analysis(messages)

        if not messages:
            return {
                "success": True,
                "total_analyzed": 0,
                "flagged_messages": [],
                "risk_summary": {},
                "overall_risk_score": 0,
                "recommendations": []
            }

        # Process in batches of 50 messages
        batch_size = 50
        all_flagged = []
        risk_scores = {cat: 0 for cat in self.RISK_CATEGORIES}

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batch_result = await self._analyze_batch(batch, context, language)

            if batch_result.get("flagged_messages"):
                all_flagged.extend(batch_result["flagged_messages"])

            # Accumulate risk scores
            for cat, score in batch_result.get("risk_scores", {}).items():
                if cat in risk_scores:
                    risk_scores[cat] = max(risk_scores[cat], score)

        # Calculate overall risk score
        overall_risk = self._calculate_overall_risk(risk_scores)

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            all_flagged, risk_scores, language
        )

        return {
            "success": True,
            "total_analyzed": len(messages),
            "flagged_messages": all_flagged,
            "flagged_count": len(all_flagged),
            "risk_summary": risk_scores,
            "overall_risk_score": overall_risk,
            "risk_level": self._get_risk_level(overall_risk),
            "recommendations": recommendations,
            "analysis_date": datetime.utcnow().isoformat()
        }

    async def _analyze_batch(
        self,
        messages: List[Dict],
        context: Dict,
        language: str
    ) -> Dict:
        """Analyze a batch of messages using Claude"""

        # Prepare messages for analysis
        messages_text = self._format_messages_for_analysis(messages)

        system_prompt = f"""You are a forensic analyst specializing in child custody cases for SafeChild Law Firm.
Your role is to analyze communication evidence for legal proceedings.

IMPORTANT: You must be objective, thorough, and identify any content that could be relevant to child safety and custody decisions.

Risk Categories to Analyze:
{json.dumps(self.RISK_CATEGORIES, indent=2)}

Case Context:
{json.dumps(context, indent=2, default=str)}

OUTPUT FORMAT (JSON):
{{
    "flagged_messages": [
        {{
            "message_index": <int>,
            "risk_categories": ["<category1>", "<category2>"],
            "severity": "low|medium|high|critical",
            "reason": "<brief explanation>",
            "evidence_value": "low|medium|high",
            "quote": "<relevant quote from message>"
        }}
    ],
    "risk_scores": {{
        "threats": <0-100>,
        "manipulation": <0-100>,
        "parental_alienation": <0-100>,
        "neglect_indicators": <0-100>,
        "abuse_indicators": <0-100>,
        "substance_abuse": <0-100>,
        "financial_coercion": <0-100>,
        "custody_interference": <0-100>,
        "inappropriate_content": <0-100>,
        "documentation_value": <0-100>
    }},
    "summary": "<brief summary of findings>"
}}

Language for explanations: {language.upper()}
"""

        user_prompt = f"""Analyze the following messages for forensic relevance:

{messages_text}

Provide your analysis in the specified JSON format. Focus on:
1. Any threats or concerning language
2. Manipulation tactics
3. Evidence of parental alienation
4. Child safety concerns
5. High-value evidence for court proceedings

Be thorough but objective. Only flag messages with genuine forensic relevance."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Parse JSON response
            result_text = response.content[0].text

            # Extract JSON from response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                result = json.loads(result_text[json_start:json_end])
            else:
                result = {"flagged_messages": [], "risk_scores": {}, "summary": ""}

            # Enhance flagged messages with original data
            for flagged in result.get("flagged_messages", []):
                idx = flagged.get("message_index", 0)
                if 0 <= idx < len(messages):
                    flagged["original_message"] = messages[idx]
                    flagged["timestamp"] = messages[idx].get("timestamp")
                    flagged["contact"] = messages[idx].get("contact")

            return result

        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return {"flagged_messages": [], "risk_scores": {}, "error": str(e)}

    def _format_messages_for_analysis(self, messages: List[Dict]) -> str:
        """Format messages for AI analysis"""
        formatted = []
        for i, msg in enumerate(messages):
            timestamp = msg.get("timestamp", "")
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

            contact = msg.get("contact", msg.get("address", "Unknown"))
            content = msg.get("content", msg.get("message", ""))
            from_me = msg.get("from_me", msg.get("outgoing", False))
            direction = "SENT" if from_me else "RECEIVED"

            formatted.append(
                f"[{i}] {timestamp} | {direction} | {contact}\n{content}\n"
            )

        return "\n---\n".join(formatted)

    def _calculate_overall_risk(self, risk_scores: Dict[str, int]) -> int:
        """Calculate overall risk score with weighted categories"""
        weights = {
            "threats": 1.5,
            "manipulation": 1.2,
            "parental_alienation": 1.3,
            "neglect_indicators": 1.4,
            "abuse_indicators": 1.5,
            "substance_abuse": 1.2,
            "financial_coercion": 1.0,
            "custody_interference": 1.1,
            "inappropriate_content": 1.4,
            "documentation_value": 0.8
        }

        weighted_sum = sum(
            score * weights.get(cat, 1.0)
            for cat, score in risk_scores.items()
        )
        total_weight = sum(weights.values())

        return min(100, int(weighted_sum / total_weight))

    def _get_risk_level(self, score: int) -> str:
        """Convert risk score to level"""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        return "minimal"

    async def _generate_recommendations(
        self,
        flagged_messages: List[Dict],
        risk_scores: Dict[str, int],
        language: str
    ) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # High-risk categories
        high_risk_cats = [cat for cat, score in risk_scores.items() if score >= 60]

        if "abuse_indicators" in high_risk_cats:
            recommendations.append({
                "priority": "urgent",
                "category": "abuse_indicators",
                "action": {
                    "de": "Sofortige Meldung an Jugendamt empfohlen",
                    "en": "Immediate report to child protective services recommended",
                    "tr": "Derhal cocuk koruma servislerine bildirim onerilir"
                }.get(language, "Immediate report recommended"),
                "evidence_count": len([m for m in flagged_messages if "abuse_indicators" in m.get("risk_categories", [])])
            })

        if "threats" in high_risk_cats:
            recommendations.append({
                "priority": "urgent",
                "category": "threats",
                "action": {
                    "de": "Bedrohungslage dokumentieren und ggf. Polizei informieren",
                    "en": "Document threats and consider police involvement",
                    "tr": "Tehditleri belgeleyin ve polise bildirmeyi dusunun"
                }.get(language, "Document threats"),
                "evidence_count": len([m for m in flagged_messages if "threats" in m.get("risk_categories", [])])
            })

        if "parental_alienation" in high_risk_cats:
            recommendations.append({
                "priority": "high",
                "category": "parental_alienation",
                "action": {
                    "de": "Elterliche Entfremdung dokumentiert - Gutachten empfohlen",
                    "en": "Parental alienation documented - expert evaluation recommended",
                    "tr": "Ebeveyn yabancilastirmasi belgelendi - uzman degerlendirmesi onerilir"
                }.get(language, "Expert evaluation recommended"),
                "evidence_count": len([m for m in flagged_messages if "parental_alienation" in m.get("risk_categories", [])])
            })

        if "documentation_value" in high_risk_cats:
            recommendations.append({
                "priority": "medium",
                "category": "documentation_value",
                "action": {
                    "de": "Hochwertige Beweismittel identifiziert - fur Gerichtsakte vorbereiten",
                    "en": "High-value evidence identified - prepare for court filing",
                    "tr": "Yuksek degerli kanitlar belirlendi - mahkeme dosyasi icin hazirlayin"
                }.get(language, "Prepare evidence for court"),
                "evidence_count": len([m for m in flagged_messages if "documentation_value" in m.get("risk_categories", [])])
            })

        return recommendations

    async def generate_case_summary(
        self,
        analysis_result: Dict,
        case_info: Dict,
        language: str = "de"
    ) -> Dict:
        """Generate a comprehensive AI case summary"""
        if not self.client:
            return {"error": "AI service unavailable", "summary": ""}

        system_prompt = f"""You are a legal analyst at SafeChild Law Firm.
Generate a professional case summary based on forensic analysis results.

Output language: {language.upper()}
Format: Professional legal document style"""

        user_prompt = f"""Based on the following forensic analysis, generate a comprehensive case summary:

Case Information:
{json.dumps(case_info, indent=2, default=str)}

Analysis Results:
- Total Messages Analyzed: {analysis_result.get('total_analyzed', 0)}
- Flagged Messages: {analysis_result.get('flagged_count', 0)}
- Overall Risk Score: {analysis_result.get('overall_risk_score', 0)}/100
- Risk Level: {analysis_result.get('risk_level', 'unknown')}

Risk Categories:
{json.dumps(analysis_result.get('risk_summary', {}), indent=2)}

Recommendations:
{json.dumps(analysis_result.get('recommendations', []), indent=2)}

Generate a structured summary including:
1. Executive Summary (2-3 sentences)
2. Key Findings
3. Risk Assessment
4. Evidence Highlights
5. Recommended Actions
6. Conclusion"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            return {
                "success": True,
                "summary": response.content[0].text,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Case summary generation error: {str(e)}")
            return {"success": False, "error": str(e), "summary": ""}

    def _fallback_analysis(self, messages: List[Dict]) -> Dict:
        """Fallback analysis when AI is not available"""
        # Simple keyword-based analysis
        risk_keywords = {
            "threats": ["kill", "hurt", "threat", "harm", "destroy", "totet", "umbringen"],
            "manipulation": ["crazy", "liar", "imagining", "verruckt", "lugner"],
            "abuse_indicators": ["hit", "beat", "scared", "afraid", "schlagen", "angst"],
            "parental_alienation": ["hate your", "don't love", "bad parent", "hasst", "schlechter"]
        }

        flagged = []
        risk_scores = {cat: 0 for cat in self.RISK_CATEGORIES}

        for i, msg in enumerate(messages):
            content = str(msg.get("content", "")).lower()
            msg_risks = []

            for category, keywords in risk_keywords.items():
                if any(kw in content for kw in keywords):
                    msg_risks.append(category)
                    risk_scores[category] = min(100, risk_scores[category] + 20)

            if msg_risks:
                flagged.append({
                    "message_index": i,
                    "risk_categories": msg_risks,
                    "severity": "medium",
                    "reason": "Keyword match (AI analysis unavailable)",
                    "evidence_value": "medium",
                    "original_message": msg
                })

        return {
            "success": True,
            "total_analyzed": len(messages),
            "flagged_messages": flagged,
            "flagged_count": len(flagged),
            "risk_summary": risk_scores,
            "overall_risk_score": self._calculate_overall_risk(risk_scores),
            "risk_level": self._get_risk_level(self._calculate_overall_risk(risk_scores)),
            "recommendations": [],
            "note": "Basic analysis only - AI service unavailable",
            "analysis_date": datetime.utcnow().isoformat()
        }


class ChildSafetyRiskAssessor:
    """
    Specialized risk assessment for child safety in custody cases.

    Provides detailed risk scoring and recommendations.
    """

    SAFETY_INDICATORS = {
        "physical_safety": {
            "weight": 1.5,
            "indicators": [
                "violence_mentions",
                "injury_references",
                "unsafe_environment",
                "supervision_concerns"
            ]
        },
        "emotional_wellbeing": {
            "weight": 1.3,
            "indicators": [
                "emotional_distress",
                "fear_expressions",
                "behavioral_changes",
                "attachment_issues"
            ]
        },
        "developmental_needs": {
            "weight": 1.2,
            "indicators": [
                "educational_neglect",
                "social_isolation",
                "routine_disruption",
                "healthcare_concerns"
            ]
        },
        "relationship_quality": {
            "weight": 1.0,
            "indicators": [
                "conflict_exposure",
                "alienation_attempts",
                "boundary_violations",
                "communication_patterns"
            ]
        }
    }

    def __init__(self, ai_analyzer: AIForensicAnalyzer):
        """Initialize with AI analyzer"""
        self.ai_analyzer = ai_analyzer

    async def assess_child_safety(
        self,
        forensic_data: Dict,
        case_context: Dict,
        language: str = "de"
    ) -> Dict:
        """
        Comprehensive child safety risk assessment.

        Args:
            forensic_data: All forensic analysis data
            case_context: Case and family context
            language: Output language

        Returns:
            Detailed risk assessment with recommendations
        """
        assessment = {
            "case_id": case_context.get("case_id"),
            "assessment_date": datetime.utcnow().isoformat(),
            "child_info": case_context.get("child_info", {}),
            "safety_scores": {},
            "overall_safety_score": 0,
            "risk_factors": [],
            "protective_factors": [],
            "recommendations": [],
            "urgency_level": "standard"
        }

        # Calculate safety scores for each category
        for category, config in self.SAFETY_INDICATORS.items():
            score = await self._evaluate_category(
                category, config, forensic_data, case_context
            )
            assessment["safety_scores"][category] = {
                "score": score,
                "level": self._score_to_level(score),
                "weight": config["weight"]
            }

        # Calculate overall safety score (inverse of risk)
        weighted_sum = sum(
            data["score"] * data["weight"]
            for data in assessment["safety_scores"].values()
        )
        total_weight = sum(
            data["weight"] for data in assessment["safety_scores"].values()
        )
        assessment["overall_safety_score"] = int(weighted_sum / total_weight)

        # Determine urgency level
        if assessment["overall_safety_score"] < 30:
            assessment["urgency_level"] = "critical"
        elif assessment["overall_safety_score"] < 50:
            assessment["urgency_level"] = "high"
        elif assessment["overall_safety_score"] < 70:
            assessment["urgency_level"] = "elevated"
        else:
            assessment["urgency_level"] = "standard"

        # Generate specific recommendations
        assessment["recommendations"] = await self._generate_safety_recommendations(
            assessment, language
        )

        return assessment

    async def _evaluate_category(
        self,
        category: str,
        config: Dict,
        forensic_data: Dict,
        case_context: Dict
    ) -> int:
        """Evaluate a specific safety category"""
        # Base score starts at 100 (safest) and decreases with risk factors
        score = 100

        ai_results = forensic_data.get("ai_analysis", {})
        risk_summary = ai_results.get("risk_summary", {})

        # Deduct based on related risks
        if category == "physical_safety":
            score -= risk_summary.get("threats", 0) * 0.5
            score -= risk_summary.get("abuse_indicators", 0) * 0.5

        elif category == "emotional_wellbeing":
            score -= risk_summary.get("manipulation", 0) * 0.4
            score -= risk_summary.get("parental_alienation", 0) * 0.4
            score -= risk_summary.get("threats", 0) * 0.2

        elif category == "developmental_needs":
            score -= risk_summary.get("neglect_indicators", 0) * 0.6
            score -= risk_summary.get("substance_abuse", 0) * 0.4

        elif category == "relationship_quality":
            score -= risk_summary.get("parental_alienation", 0) * 0.5
            score -= risk_summary.get("custody_interference", 0) * 0.3
            score -= risk_summary.get("manipulation", 0) * 0.2

        return max(0, min(100, int(score)))

    def _score_to_level(self, score: int) -> str:
        """Convert score to safety level"""
        if score >= 80:
            return "safe"
        elif score >= 60:
            return "adequate"
        elif score >= 40:
            return "concerning"
        elif score >= 20:
            return "at_risk"
        return "critical"

    async def _generate_safety_recommendations(
        self,
        assessment: Dict,
        language: str
    ) -> List[Dict]:
        """Generate child safety recommendations"""
        recommendations = []

        translations = {
            "supervised_visitation": {
                "de": "Uberwachter Umgang empfohlen",
                "en": "Supervised visitation recommended",
                "tr": "Gozetimli ziyaret onerilir"
            },
            "psychological_evaluation": {
                "de": "Psychologische Begutachtung des Kindes empfohlen",
                "en": "Psychological evaluation of child recommended",
                "tr": "Cocugun psikolojik degerlendirmesi onerilir"
            },
            "family_counseling": {
                "de": "Familienberatung empfohlen",
                "en": "Family counseling recommended",
                "tr": "Aile danismanligi onerilir"
            },
            "emergency_measures": {
                "de": "Sofortige Schutzmanahmen erforderlich",
                "en": "Immediate protective measures required",
                "tr": "Acil koruma onlemleri gerekli"
            }
        }

        safety_scores = assessment.get("safety_scores", {})

        # Physical safety concerns
        if safety_scores.get("physical_safety", {}).get("score", 100) < 50:
            recommendations.append({
                "type": "supervised_visitation",
                "priority": "high",
                "action": translations["supervised_visitation"].get(language),
                "reason": "Physical safety score below threshold"
            })

        # Emotional wellbeing concerns
        if safety_scores.get("emotional_wellbeing", {}).get("score", 100) < 50:
            recommendations.append({
                "type": "psychological_evaluation",
                "priority": "high",
                "action": translations["psychological_evaluation"].get(language),
                "reason": "Emotional wellbeing score below threshold"
            })

        # Critical urgency
        if assessment.get("urgency_level") == "critical":
            recommendations.insert(0, {
                "type": "emergency_measures",
                "priority": "urgent",
                "action": translations["emergency_measures"].get(language),
                "reason": "Overall safety score critically low"
            })

        # General family counseling
        if assessment.get("overall_safety_score", 100) < 70:
            recommendations.append({
                "type": "family_counseling",
                "priority": "medium",
                "action": translations["family_counseling"].get(language),
                "reason": "Overall safety score indicates need for intervention"
            })

        return recommendations
