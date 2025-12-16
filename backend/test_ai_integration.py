"""
Quick test script for AI integration
Tests Claude client, Risk Analyzer, and Chat Assistant
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from ai.claude import ClaudeClient, RiskAnalyzer, ChatAssistant, ChatSession


async def test_claude_client():
    """Test basic Claude client connectivity."""
    print("\n" + "="*60)
    print("TEST 1: Claude Client Connectivity")
    print("="*60)

    try:
        client = ClaudeClient()
        print("✓ Claude client initialized")

        # Simple test prompt
        response = await client.simple_prompt(
            prompt="Merhaba! Bana 'Çalışıyorum' diye cevap ver.",
            max_tokens=50
        )
        print(f"✓ API Response: {response}")
        print("✓ Claude client test PASSED")
        return True
    except Exception as e:
        print(f"✗ Claude client test FAILED: {e}")
        return False


async def test_risk_analyzer():
    """Test Risk Analyzer with sample case."""
    print("\n" + "="*60)
    print("TEST 2: Risk Analyzer")
    print("="*60)

    try:
        analyzer = RiskAnalyzer()
        print("✓ Risk Analyzer initialized")

        # Sample Turkish case description
        case_description = """
        Eski eşim son 3 ayda alkol alırken çocuğa bakmaya geldi.
        Çocuğum 5 yaşında ve geçen hafta eve geldiğinde üzgün ve korkmuştu.
        Bana babası ile görüşmek istemediğini söyledi.
        Komşular eski eşimin çocuğa bağırdığını duymuşlar.
        """

        print("Analyzing sample case...")
        result = await analyzer.analyze_case(
            case_id="test_case_001",
            case_description=case_description,
            additional_context={"child_age": 5}
        )

        print(f"\n✓ Risk Analysis Complete:")
        print(f"  - Risk Level: {result.risk_level.value}")
        print(f"  - Risk Score: {result.overall_risk_score}/10")
        print(f"  - Confidence: {result.confidence*100:.0f}%")
        print(f"  - Top Concerns: {len(result.top_concerns)} identified")
        print(f"  - Summary: {result.parent_friendly_summary[:100]}...")
        print(f"  - Immediate Actions: {len(result.immediate_actions)} suggested")
        print("\n✓ Risk Analyzer test PASSED")
        return True
    except Exception as e:
        print(f"✗ Risk Analyzer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chat_assistant():
    """Test Chat Assistant with sample conversation."""
    print("\n" + "="*60)
    print("TEST 3: Chat Assistant (40+ Women UX)")
    print("="*60)

    try:
        assistant = ChatAssistant()
        print("✓ Chat Assistant initialized")

        # Create test session
        session = ChatSession(
            session_id="test_session_001",
            user_id="test_user",
            case_id="test_case_001",
            messages=[],
            created_at=datetime.now(),
            last_activity=datetime.now()
        )

        # Test welcome message
        welcome = await assistant.create_welcome_message(user_name="Ayşe")
        print(f"✓ Welcome message created")
        print(f"  - Quick actions: {len(welcome.quick_actions)} buttons")

        # Test user message
        user_message = "Çocuğum tehlikede mi? Eski eşim alkollü geldi."
        print(f"\n📨 User: {user_message}")

        response = await assistant.send_message(
            session=session,
            user_message=user_message
        )

        print(f"🤖 Assistant: {response.content[:150]}...")
        print(f"  - Quick actions suggested: {len(response.quick_actions or [])} buttons")

        if response.quick_actions:
            print("  - Actions:")
            for action in response.quick_actions[:2]:
                print(f"    • {action['label']}: {action['description']}")

        # Test legal term explanation
        term_explanation = await assistant.explain_legal_term("velayet")
        print(f"\n✓ Legal term explained: {term_explanation[:100]}...")

        print("\n✓ Chat Assistant test PASSED")
        return True
    except Exception as e:
        print(f"✗ Chat Assistant test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SafeChild AI Integration Test Suite")
    print("Testing Claude AI connectivity and features")
    print("="*60)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n✗ ANTHROPIC_API_KEY not found in environment!")
        print("Please set it in .env file")
        return

    print(f"✓ API Key found: {api_key[:20]}...")

    # Run tests
    results = []
    results.append(await test_claude_client())
    results.append(await test_risk_analyzer())
    results.append(await test_chat_assistant())

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! AI Integration is ready.")
        print("\nNext steps:")
        print("1. Start FastAPI server: uvicorn backend.server:app --reload")
        print("2. Test endpoints at http://localhost:8000/api/docs")
        print("3. Test chat: POST /api/ai/chat")
        print("4. Test risk: POST /api/ai/analyze-risk")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
