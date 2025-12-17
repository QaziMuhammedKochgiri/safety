"""
Child Safety Risk Predictor API Router
Provides endpoints for predicting and analyzing child safety risks.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.risk_predictor.risk_model import RiskPredictor, RiskLevel
from ..ai.risk_predictor.feature_extractor import FeatureExtractor
from ..ai.risk_predictor.outcome_correlator import OutcomeCorrelator
from ..ai.risk_predictor.intervention_recommender import InterventionRecommender
from ..ai.risk_predictor.explainer import RiskExplainer
from .. import db

router = APIRouter(
    prefix="/risk",
    tags=["risk-predictor"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Pydantic Models
# =============================================================================

class CaseData(BaseModel):
    """Input model for case data."""
    case_id: str
    alienation_score: Optional[float] = 0
    communication_frequency: Optional[int] = 0
    contact_violations: Optional[int] = 0
    court_filings: Optional[int] = 0
    child_age: Optional[int] = None
    separation_months: Optional[int] = None
    has_restraining_order: Optional[bool] = False
    custody_arrangement: Optional[str] = "joint"
    additional_factors: Optional[Dict[str, Any]] = {}


class RiskAnalysisRequest(BaseModel):
    """Request model for risk analysis."""
    case_data: CaseData
    include_explanation: bool = True
    include_interventions: bool = True


class RiskFactorDetail(BaseModel):
    """Details of a single risk factor."""
    factor_id: str
    name: str
    category: str
    value: float
    weight: float
    contribution: float
    description: str


class InterventionItem(BaseModel):
    """A recommended intervention."""
    id: str
    name: str
    priority: str  # urgent, high, medium, low
    category: str
    description: str
    rationale: str
    effectiveness_score: float


class RiskAnalysisResponse(BaseModel):
    """Response model for risk analysis."""
    case_id: str
    overall_score: float
    risk_level: str
    confidence: float
    risk_factors: List[RiskFactorDetail]
    top_contributors: List[str]
    interventions: Optional[List[InterventionItem]] = None
    explanation: Optional[str] = None
    trajectory: Optional[str] = None
    analyzed_at: datetime


class WhatIfRequest(BaseModel):
    """Request for what-if scenario analysis."""
    case_id: str
    scenario_changes: Dict[str, Any]


class WhatIfResponse(BaseModel):
    """Response for what-if scenario analysis."""
    case_id: str
    original_score: float
    projected_score: float
    score_change: float
    affected_factors: List[str]
    recommendations: List[str]


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest):
    """
    Analyze child safety risk for a case.

    Performs comprehensive risk assessment using multiple factors
    including alienation patterns, communication data, and
    historical case outcomes.
    """
    try:
        # Initialize components
        risk_model = RiskPredictor()
        feature_extractor = FeatureExtractor()
        explainer = RiskExplainer()
        intervention_recommender = InterventionRecommender()

        # Extract features from case data
        features = feature_extractor.extract({
            "alienation_score": request.case_data.alienation_score,
            "communication_frequency": request.case_data.communication_frequency,
            "contact_violations": request.case_data.contact_violations,
            "court_filings": request.case_data.court_filings,
            "child_age": request.case_data.child_age,
            "separation_months": request.case_data.separation_months,
            "has_restraining_order": request.case_data.has_restraining_order,
            "custody_arrangement": request.case_data.custody_arrangement,
            **request.case_data.additional_factors
        })

        # Calculate risk score
        risk_result = risk_model.predict(features)

        # Build risk factors detail
        risk_factors = []
        for factor_id, value in features.items():
            factor_info = risk_model.get_factor_info(factor_id)
            if factor_info:
                risk_factors.append(RiskFactorDetail(
                    factor_id=factor_id,
                    name=factor_info.get("name", factor_id),
                    category=factor_info.get("category", "general"),
                    value=float(value) if value else 0,
                    weight=factor_info.get("weight", 1.0),
                    contribution=risk_result.factor_contributions.get(factor_id, 0),
                    description=factor_info.get("description", "")
                ))

        # Sort by contribution and get top contributors
        risk_factors.sort(key=lambda x: x.contribution, reverse=True)
        top_contributors = [f.name for f in risk_factors[:5]]

        # Generate explanation if requested
        explanation = None
        if request.include_explanation:
            explanation = explainer.explain(risk_result, features)

        # Get interventions if requested
        interventions = None
        if request.include_interventions:
            recommended = intervention_recommender.recommend(
                risk_level=risk_result.level,
                risk_factors=risk_factors,
                case_data=request.case_data.dict()
            )
            interventions = [
                InterventionItem(
                    id=i.id,
                    name=i.name,
                    priority=i.priority,
                    category=i.category,
                    description=i.description,
                    rationale=i.rationale,
                    effectiveness_score=i.effectiveness
                )
                for i in recommended
            ]

        # Determine trajectory
        trajectory = "stable"
        if request.case_data.alienation_score > 7:
            trajectory = "increasing"
        elif request.case_data.contact_violations > 3:
            trajectory = "concerning"

        # Store analysis in database
        analysis_doc = {
            "case_id": request.case_data.case_id,
            "type": "risk_analysis",
            "overall_score": risk_result.score,
            "risk_level": risk_result.level.value,
            "confidence": risk_result.confidence,
            "risk_factors": [f.dict() for f in risk_factors],
            "analyzed_at": datetime.utcnow()
        }
        await db.db.forensic_analyses.update_one(
            {"case_id": request.case_data.case_id, "type": "risk_analysis"},
            {"$set": analysis_doc},
            upsert=True
        )

        return RiskAnalysisResponse(
            case_id=request.case_data.case_id,
            overall_score=risk_result.score,
            risk_level=risk_result.level.value,
            confidence=risk_result.confidence,
            risk_factors=risk_factors,
            top_contributors=top_contributors,
            interventions=interventions,
            explanation=explanation,
            trajectory=trajectory,
            analyzed_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.get("/factors")
async def get_risk_factors():
    """
    Get list of all risk factors used in analysis.

    Returns the complete list of factors with their weights
    and descriptions.
    """
    try:
        risk_model = RiskPredictor()
        factors = risk_model.get_all_factors()

        return {
            "total_factors": len(factors),
            "categories": _get_factor_categories(factors),
            "factors": factors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get factors: {str(e)}")


@router.get("/interventions/{case_id}")
async def get_interventions(
    case_id: str,
    priority: Optional[str] = Query(None, description="Filter by priority: urgent, high, medium, low")
):
    """
    Get recommended interventions for a case.

    Returns prioritized list of recommended interventions
    based on the case's risk profile.
    """
    try:
        # Get latest risk analysis
        analysis = await db.db.forensic_analyses.find_one({
            "case_id": case_id,
            "type": "risk_analysis"
        })

        if not analysis:
            raise HTTPException(status_code=404, detail="No risk analysis found for this case")

        # Generate interventions
        intervention_recommender = InterventionRecommender()
        risk_level = RiskLevel(analysis.get("risk_level", "medium"))

        interventions = intervention_recommender.recommend(
            risk_level=risk_level,
            risk_factors=analysis.get("risk_factors", []),
            case_data={"case_id": case_id}
        )

        # Filter by priority if specified
        if priority:
            interventions = [i for i in interventions if i.priority == priority]

        return {
            "case_id": case_id,
            "risk_level": analysis.get("risk_level"),
            "total_interventions": len(interventions),
            "interventions": [
                {
                    "id": i.id,
                    "name": i.name,
                    "priority": i.priority,
                    "category": i.category,
                    "description": i.description,
                    "rationale": i.rationale,
                    "effectiveness_score": i.effectiveness
                }
                for i in interventions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interventions: {str(e)}")


@router.post("/explain")
async def explain_risk(case_id: str):
    """
    Get detailed explanation of risk score.

    Provides human-readable explanation of why a particular
    risk score was assigned, including key contributing factors.
    """
    try:
        # Get latest risk analysis
        analysis = await db.db.forensic_analyses.find_one({
            "case_id": case_id,
            "type": "risk_analysis"
        })

        if not analysis:
            raise HTTPException(status_code=404, detail="No risk analysis found for this case")

        explainer = RiskExplainer()

        # Build explanation
        explanation = explainer.generate_detailed_explanation(
            score=analysis.get("overall_score", 0),
            level=analysis.get("risk_level", "unknown"),
            factors=analysis.get("risk_factors", [])
        )

        return {
            "case_id": case_id,
            "overall_score": analysis.get("overall_score"),
            "risk_level": analysis.get("risk_level"),
            "explanation": {
                "summary": explanation.summary,
                "key_factors": explanation.key_factors,
                "detailed_analysis": explanation.detailed,
                "confidence_note": explanation.confidence_note
            },
            "what_if_scenarios": explanation.scenarios if hasattr(explanation, "scenarios") else []
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


@router.post("/what-if", response_model=WhatIfResponse)
async def what_if_analysis(request: WhatIfRequest):
    """
    Perform what-if scenario analysis.

    Allows exploring how changes to certain factors would
    affect the overall risk score.
    """
    try:
        # Get current analysis
        analysis = await db.db.forensic_analyses.find_one({
            "case_id": request.case_id,
            "type": "risk_analysis"
        })

        if not analysis:
            raise HTTPException(status_code=404, detail="No risk analysis found for this case")

        original_score = analysis.get("overall_score", 0)

        # Create modified features
        risk_model = RiskPredictor()
        feature_extractor = FeatureExtractor()

        # Get original factors and apply changes
        original_factors = {f["factor_id"]: f["value"] for f in analysis.get("risk_factors", [])}
        modified_factors = {**original_factors, **request.scenario_changes}

        # Calculate new score
        features = feature_extractor.extract(modified_factors)
        new_result = risk_model.predict(features)

        # Identify affected factors
        affected = [k for k in request.scenario_changes.keys()]

        # Generate recommendations based on changes
        recommendations = []
        score_change = new_result.score - original_score
        if score_change < -1:
            recommendations.append("This scenario shows significant risk reduction")
        elif score_change > 1:
            recommendations.append("This scenario would increase risk")

        return WhatIfResponse(
            case_id=request.case_id,
            original_score=original_score,
            projected_score=new_result.score,
            score_change=score_change,
            affected_factors=affected,
            recommendations=recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis failed: {str(e)}")


@router.get("/trajectory/{case_id}")
async def get_risk_trajectory(case_id: str):
    """
    Get risk score trajectory over time.

    Shows how the risk score has changed over multiple
    assessments.
    """
    try:
        # Get all risk analyses for this case, sorted by date
        analyses = await db.db.forensic_analyses.find({
            "case_id": case_id,
            "type": "risk_analysis"
        }).sort("analyzed_at", 1).to_list(length=50)

        if not analyses:
            raise HTTPException(status_code=404, detail="No risk analyses found for this case")

        trajectory_points = [
            {
                "date": a.get("analyzed_at").isoformat() if a.get("analyzed_at") else None,
                "score": a.get("overall_score", 0),
                "level": a.get("risk_level", "unknown")
            }
            for a in analyses
        ]

        # Calculate trend
        scores = [p["score"] for p in trajectory_points]
        trend = "stable"
        if len(scores) >= 2:
            if scores[-1] > scores[0] + 1:
                trend = "increasing"
            elif scores[-1] < scores[0] - 1:
                trend = "decreasing"

        return {
            "case_id": case_id,
            "total_assessments": len(trajectory_points),
            "current_score": scores[-1] if scores else 0,
            "trend": trend,
            "trajectory": trajectory_points
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trajectory: {str(e)}")


def _get_factor_categories(factors: List[Dict]) -> Dict[str, int]:
    """Get count of factors by category."""
    categories = {}
    for f in factors:
        cat = f.get("category", "general")
        categories[cat] = categories.get(cat, 0) + 1
    return categories
