"""
Test script for Parental Alienation Detector
Tests AI-powered parental alienation detection
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from ai.claude import AlienationDetector, AlienationAnalysisRequest, AlienationEvidence


async def test_severe_alienation():
    """Test detection of severe parental alienation."""
    print("\n" + "="*60)
    print("TEST: Severe Parental Alienation Detection")
    print("="*60)

    detector = AlienationDetector()
    print("✓ Alienation Detector initialized")

    # Sample severe alienation case
    evidence_items = [
        AlienationEvidence(
            evidence_type="message",
            description="Text from father: 'Your mother doesn't want you anymore, she has a new family now'",
            date="2024-12-10",
            source="other_parent"
        ),
        AlienationEvidence(
            evidence_type="behavior",
            description="Child refuses to take phone calls from mother, becomes anxious when mother's name is mentioned",
            date="2024-12-12",
            source="child"
        ),
        AlienationEvidence(
            evidence_type="incident",
            description="Father cancelled last 3 scheduled visitations, claiming child was 'too busy' or 'sick'",
            date="2024-11-20",
            source="other_parent"
        ),
        AlienationEvidence(
            evidence_type="statement",
            description="Child told therapist: 'Daddy says mommy is a bad person who abandoned us'",
            date="2024-12-05",
            source="child"
        )
    ]

    request = AlienationAnalysisRequest(
        case_id="case_001",
        child_name="Emma",
        child_age=8,
        alienating_parent="Michael Johnson",
        targeted_parent="Sarah Johnson",
        case_description="""
        After divorce 18 months ago, the father has engaged in a systematic campaign to
        turn our 8-year-old daughter against me. He makes disparaging comments about me
        in front of Emma, tells her I don't love her anymore, and actively interferes
        with my visitation time. Emma used to be close to me but now refuses to see me
        or talk to me on the phone. The father rewards her when she rejects me and
        makes her feel guilty if she shows any affection toward me.
        """,
        evidence_items=evidence_items,
        custody_arrangement="Joint custody with primary residence with father",
        child_statements=[
            "Daddy says mommy doesn't love me anymore",
            "I don't want to see mommy",
            "Mommy left us and doesn't care about me",
            "Daddy gets sad when I talk about mommy"
        ],
        behavioral_changes=[
            "Refuses phone calls from mother (started 6 months ago)",
            "Becomes anxious or upset before scheduled visits",
            "Uses negative language about mother that mirrors father's words",
            "Shows no emotion or affection toward mother",
            "Refuses gifts or letters from mother"
        ]
    )

    result = await detector.analyze_case(request)

    print(f"\n✓ Analysis Completed!")
    print(f"  - Severity: {result.severity.value.upper()}")
    print(f"  - Severity Score: {result.severity_score:.1f}/10")
    print(f"  - Confidence: {result.confidence*100:.0f}%")

    print(f"\n🚨 DETECTED ALIENATION TACTICS ({len(result.detected_tactics)}):")
    for i, tactic in enumerate(result.detected_tactics, 1):
        print(f"\n  {i}. {tactic.tactic.value.upper().replace('_', ' ')}")
        print(f"     {tactic.description}")
        print(f"     Severity: {tactic.severity*10:.1f}/10")

    print(f"\n⚠️  PRIMARY CONCERNS:")
    for i, concern in enumerate(result.primary_concerns[:3], 1):
        print(f"  {i}. {concern}")

    print(f"\n👤 CHILD IMPACT:")
    print(f"  {result.child_impact_assessment[:200]}...")

    print(f"\n📋 IMMEDIATE ACTIONS:")
    for i, action in enumerate(result.immediate_actions[:3], 1):
        print(f"  {i}. {action}")

    print(f"\n⚖️  EXECUTIVE SUMMARY (for court):")
    print("-" * 60)
    print(result.executive_summary[:400] + "...")

    return result


async def test_moderate_alienation():
    """Test detection of moderate parental alienation."""
    print("\n" + "="*60)
    print("TEST: Moderate Parental Alienation Detection")
    print("="*60)

    detector = AlienationDetector()

    request = AlienationAnalysisRequest(
        case_id="case_002",
        child_name="Jake",
        child_age=10,
        alienating_parent="Lisa Martinez",
        targeted_parent="Carlos Martinez",
        case_description="""
        My ex-wife frequently makes negative comments about me in front of our son.
        She tells him that I left the family and don't care about them. She schedules
        activities during my visitation time and 'forgets' to tell me about school events.
        Our son is starting to resist visits with me and repeats things his mother says.
        """,
        evidence_items=[
            AlienationEvidence(
                evidence_type="incident",
                description="Mother scheduled son's birthday party during father's visitation weekend without consulting father",
                date="2024-11-15",
                source="other_parent"
            ),
            AlienationEvidence(
                evidence_type="statement",
                description="Son said: 'Mom says you only care about your new girlfriend'",
                date="2024-12-01",
                source="child"
            )
        ],
        child_statements=[
            "Mom says you chose your new girlfriend over us",
            "I want to stay with mom this weekend instead"
        ],
        behavioral_changes=[
            "Less enthusiastic about visits (last 3 months)",
            "Asks to go home early from visits"
        ]
    )

    result = await detector.analyze_case(request)

    print(f"\n✓ Analysis Completed!")
    print(f"  - Severity: {result.severity.value.upper()}")
    print(f"  - Severity Score: {result.severity_score:.1f}/10")
    print(f"  - Detected Tactics: {len(result.detected_tactics)}")

    print(f"\n📊 DETECTED TACTICS:")
    for tactic in result.detected_tactics[:3]:
        print(f"  • {tactic.tactic.value}")

    return result


async def test_mild_alienation():
    """Test detection of mild/early warning signs."""
    print("\n" + "="*60)
    print("TEST: Mild Alienation (Early Warning Signs)")
    print("="*60)

    detector = AlienationDetector()

    result = await detector.quick_analysis(
        case_description="""
        Recently noticed that my ex-husband occasionally makes negative comments
        about me when picking up our daughter. She mentioned that he said I'm
        'always working' and 'too busy for her.' I want to address this early
        before it becomes a bigger problem.
        """,
        child_name="Sophia",
        child_age=6,
        alienating_parent="David Brown",
        targeted_parent="Emily Brown"
    )

    print(f"\n✓ Quick Analysis Completed!")
    print(f"  - Severity: {result.severity.value.upper()}")
    print(f"  - Severity Score: {result.severity_score:.1f}/10")

    if result.severity_score < 3:
        print(f"\n✅ Good news: Early warning signs detected, but preventable!")

    print(f"\n💡 IMMEDIATE ACTIONS:")
    for i, action in enumerate(result.immediate_actions[:2], 1):
        print(f"  {i}. {action}")

    return result


async def test_no_alienation():
    """Test case with no alienation."""
    print("\n" + "="*60)
    print("TEST: No Alienation Detected")
    print("="*60)

    detector = AlienationDetector()

    result = await detector.quick_analysis(
        case_description="""
        My ex-wife and I have a healthy co-parenting relationship. We communicate
        well about our son's needs, share information openly, and both support his
        relationship with the other parent. Sometimes there are minor disagreements,
        but we resolve them maturely.
        """,
        child_name="Oliver",
        child_age=9,
        alienating_parent="N/A",
        targeted_parent="N/A"
    )

    print(f"\n✓ Analysis Completed!")
    print(f"  - Severity: {result.severity.value.upper()}")
    print(f"  - Severity Score: {result.severity_score:.1f}/10")

    if result.severity_score < 2:
        print(f"\n✅ Healthy co-parenting relationship!")

    return result


async def main():
    """Run all alienation detection tests."""
    print("\n" + "="*60)
    print("AI Parental Alienation Detection Test Suite")
    print("="*60)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n✗ ANTHROPIC_API_KEY not found!")
        return

    print(f"✓ API Key found: {api_key[:20]}...")

    results = []

    # Test 1: Severe Alienation
    try:
        result1 = await test_severe_alienation()
        results.append(("Severe Alienation", True, result1))
    except Exception as e:
        print(f"\n✗ Severe alienation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Severe Alienation", False, None))

    # Test 2: Moderate Alienation
    try:
        result2 = await test_moderate_alienation()
        results.append(("Moderate Alienation", True, result2))
    except Exception as e:
        print(f"\n✗ Moderate alienation test FAILED: {e}")
        results.append(("Moderate Alienation", False, None))

    # Test 3: Mild Alienation
    try:
        result3 = await test_mild_alienation()
        results.append(("Mild Alienation", True, result3))
    except Exception as e:
        print(f"\n✗ Mild alienation test FAILED: {e}")
        results.append(("Mild Alienation", False, None))

    # Test 4: No Alienation
    try:
        result4 = await test_no_alienation()
        results.append(("No Alienation", True, result4))
    except Exception as e:
        print(f"\n✗ No alienation test FAILED: {e}")
        results.append(("No Alienation", False, None))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}\n")

    for test_name, success, result in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status} - {test_name}")
        if success and result:
            print(f"           Severity: {result.severity.value} ({result.severity_score:.1f}/10)")

    if passed == total:
        print("\n🎉 ALL ALIENATION DETECTION TESTS PASSED!")
        print("\nParental Alienation API Endpoints:")
        print("- POST /api/ai/analyze-alienation - Full analysis")
        print("- POST /api/ai/analyze-alienation-quick - Quick screening")
        print("- GET /api/ai/alienation-info - Tactics & severity info")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
