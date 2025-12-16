"""
Test script for Petition Generator
Tests AI-powered court document generation
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from ai.claude import PetitionGenerator, PetitionType, CourtJurisdiction


async def test_custody_petition():
    """Test custody petition generation."""
    print("\n" + "="*60)
    print("TEST: Custody Petition Generation")
    print("="*60)

    generator = PetitionGenerator()
    print("✓ Petition Generator initialized")

    # Sample custody case
    petition = await generator.generate_quick_petition(
        petition_type=PetitionType.CUSTODY,
        case_description="""
        Over the past 6 months, my ex-spouse has demonstrated concerning behavior
        that endangers our 7-year-old daughter's wellbeing. On three separate occasions,
        the child has been returned from visitation with bruises. The child has expressed
        fear of returning to the respondent's home. I have documented evidence including
        photos, text messages, and witness statements from neighbors.
        """,
        petitioner_name="Jane Smith",
        respondent_name="John Smith",
        child_name="Emily Smith",
        child_age=7,
        relief_requested=[
            "Grant primary physical custody to petitioner",
            "Restrict respondent's visitation to supervised only",
            "Order psychological evaluation of child",
            "Award decision-making authority to petitioner"
        ],
        jurisdiction=CourtJurisdiction.TURKEY,
        language="en"
    )

    print(f"\n✓ Petition Generated Successfully!")
    print(f"  - Title: {petition.title}")
    print(f"  - Word Count: {petition.word_count}")
    print(f"  - Estimated Pages: {petition.estimated_pages}")
    print(f"  - Confidence: {petition.confidence*100:.0f}%")
    print(f"  - Key Legal Points: {len(petition.key_legal_points)}")

    print(f"\n📄 PETITION PREVIEW:")
    print("-" * 60)
    print(petition.full_document[:500] + "...")
    print("-" * 60)

    print(f"\n✓ Key Legal Points:")
    for i, point in enumerate(petition.key_legal_points[:3], 1):
        print(f"  {i}. {point}")

    return petition


async def test_protection_order():
    """Test protection order generation."""
    print("\n" + "="*60)
    print("TEST: Protection Order Generation")
    print("="*60)

    generator = PetitionGenerator()

    petition = await generator.generate_quick_petition(
        petition_type=PetitionType.PROTECTION_ORDER,
        case_description="""
        My ex-spouse has been sending threatening messages daily for the past two weeks.
        He has shown up unannounced at my workplace three times. Last week, he followed
        me home and confronted me aggressively in front of our 5-year-old son. I fear
        for my safety and my child's safety. I have saved all threatening messages
        and have a police report from the workplace incident.
        """,
        petitioner_name="Sarah Johnson",
        respondent_name="Michael Johnson",
        child_name="Alex Johnson",
        child_age=5,
        relief_requested=[
            "Issue protection order against respondent",
            "Prohibit respondent from contacting petitioner",
            "Establish 500-meter minimum distance requirement",
            "Grant temporary sole custody to petitioner"
        ],
        jurisdiction=CourtJurisdiction.TURKEY,
        language="en"
    )

    print(f"\n✓ Protection Order Generated!")
    print(f"  - Title: {petition.title}")
    print(f"  - Word Count: {petition.word_count}")
    print(f"  - Estimated Pages: {petition.estimated_pages}")

    print(f"\n📄 LEGAL ARGUMENTS PREVIEW:")
    print("-" * 60)
    legal_text = str(petition.legal_arguments)[:400]
    print(legal_text + "...")

    return petition


async def test_emergency_custody():
    """Test emergency custody petition."""
    print("\n" + "="*60)
    print("TEST: Emergency Custody Petition")
    print("="*60)

    generator = PetitionGenerator()

    petition = await generator.generate_quick_petition(
        petition_type=PetitionType.EMERGENCY_CUSTODY,
        case_description="""
        URGENT: My ex-spouse has relapsed into alcohol abuse. Yesterday, neighbors
        called police after witnessing the respondent driving intoxicated with our
        4-year-old daughter in the car. Police report confirms BAC of 0.18%. The child
        was removed by authorities and is currently with me. This is the third DUI
        incident in 18 months. I am filing for emergency custody to protect my daughter.
        """,
        petitioner_name="Maria Rodriguez",
        respondent_name="Carlos Rodriguez",
        child_name="Sofia Rodriguez",
        child_age=4,
        relief_requested=[
            "Grant emergency temporary custody to petitioner",
            "Suspend respondent's visitation rights immediately",
            "Order substance abuse evaluation and treatment",
            "Schedule expedited hearing within 14 days"
        ],
        jurisdiction=CourtJurisdiction.TURKEY,
        language="en"
    )

    print(f"\n✓ Emergency Custody Petition Generated!")
    print(f"  - Title: {petition.title}")
    print(f"  - Word Count: {petition.word_count}")
    print(f"  - Urgency Reflected: {'EMERGENCY' in petition.full_document}")

    print(f"\n📄 STATEMENT OF FACTS:")
    print("-" * 60)
    facts_text = str(petition.statement_of_facts)[:400]
    print(facts_text + "...")

    return petition


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AI Petition Generator Test Suite")
    print("="*60)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n✗ ANTHROPIC_API_KEY not found!")
        return

    print(f"✓ API Key found: {api_key[:20]}...")

    results = []

    # Test 1: Custody Petition
    try:
        petition1 = await test_custody_petition()
        results.append(("Custody Petition", True, petition1))
    except Exception as e:
        print(f"\n✗ Custody petition test FAILED: {e}")
        results.append(("Custody Petition", False, None))

    # Test 2: Protection Order
    try:
        petition2 = await test_protection_order()
        results.append(("Protection Order", True, petition2))
    except Exception as e:
        print(f"\n✗ Protection order test FAILED: {e}")
        results.append(("Protection Order", False, None))

    # Test 3: Emergency Custody
    try:
        petition3 = await test_emergency_custody()
        results.append(("Emergency Custody", True, petition3))
    except Exception as e:
        print(f"\n✗ Emergency custody test FAILED: {e}")
        results.append(("Emergency Custody", False, None))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}\n")

    for test_name, success, petition in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status} - {test_name}")
        if success and petition:
            print(f"           Words: {petition.word_count}, Pages: ~{petition.estimated_pages}")

    if passed == total:
        print("\n🎉 ALL PETITION GENERATION TESTS PASSED!")
        print("\nNext steps:")
        print("1. Test via FastAPI: uvicorn backend.server:app --reload")
        print("2. API endpoint: POST /api/ai/generate-petition")
        print("3. View docs: http://localhost:8000/api/docs")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
