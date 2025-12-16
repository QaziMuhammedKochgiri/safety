"""
Test script for Legal Translation
Tests AI-powered legal document translation
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

from ai.claude import LegalTranslator, TranslationRequest, TranslationType


async def test_turkish_to_english():
    """Test Turkish to English legal translation."""
    print("\n" + "="*60)
    print("TEST: Turkish to English Legal Translation")
    print("="*60)

    translator = LegalTranslator()
    print("✓ Legal Translator initialized")

    # Sample Turkish legal text
    request = TranslationRequest(
        source_text="""
        Velayet davası açmak istiyorum. Eski eşim çocuğumuza fiziksel ve duygusal
        şiddet uygulamaktadır. Son 3 ayda çocuğumuz eski eşimin evinden morluklar
        ile döndü. Çocuk nafakası da düzenli ödenmiyor. Kişisel ilişki kurma hakkı
        kısıtlanmalıdır.
        """,
        source_language="tr",
        target_language="en",
        translation_type=TranslationType.PETITION,
        source_jurisdiction="turkey",
        target_jurisdiction="turkey",
        legal_domain="custody",
        include_annotations=True
    )

    result = await translator.translate(request)

    print(f"\n✓ Translation Completed!")
    print(f"  - Confidence: {result.confidence*100:.0f}%")
    print(f"  - Legal Accuracy: {result.legal_accuracy*100:.0f}%")
    print(f"  - Cultural Appropriateness: {result.cultural_appropriateness*100:.0f}%")

    print(f"\n📄 ORIGINAL TEXT:")
    print("-" * 60)
    print(request.source_text.strip())

    print(f"\n📄 TRANSLATED TEXT:")
    print("-" * 60)
    print(result.translated_text)

    if result.terminology_notes:
        print(f"\n📖 TERMINOLOGY NOTES:")
        for note in result.terminology_notes[:3]:
            print(f"  • {note.get('term')} → {note.get('translation')}")
            print(f"    {note.get('note')}")

    if result.cultural_notes:
        print(f"\n🌍 CULTURAL NOTES:")
        for note in result.cultural_notes[:2]:
            print(f"  • {note}")

    if result.warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in result.warnings:
            print(f"  • {warning}")

    return result


async def test_german_to_english():
    """Test German to English legal translation."""
    print("\n" + "="*60)
    print("TEST: German to English Legal Translation")
    print("="*60)

    translator = LegalTranslator()

    request = TranslationRequest(
        source_text="""
        Ich beantrage das alleinige Sorgerecht für mein Kind. Der Kindesvater
        gefährdet das Kindeswohl durch Alkoholmissbrauch. Das Umgangsrecht sollte
        auf begleiteten Umgang beschränkt werden.
        """,
        source_language="de",
        target_language="en",
        translation_type=TranslationType.PETITION,
        source_jurisdiction="germany",
        legal_domain="custody"
    )

    result = await translator.translate(request)

    print(f"\n✓ Translation Completed!")
    print(f"  - Confidence: {result.confidence*100:.0f}%")

    print(f"\n📄 ORIGINAL (German):")
    print("-" * 60)
    print(request.source_text.strip())

    print(f"\n📄 TRANSLATED (English):")
    print("-" * 60)
    print(result.translated_text)

    return result


async def test_english_to_turkish():
    """Test English to Turkish legal translation."""
    print("\n" + "="*60)
    print("TEST: English to Turkish Legal Translation")
    print("="*60)

    translator = LegalTranslator()

    request = TranslationRequest(
        source_text="""
        I am filing for sole custody of my child. The child's father has
        demonstrated substance abuse issues and has failed to maintain a safe
        environment. I request supervised visitation only.
        """,
        source_language="en",
        target_language="tr",
        translation_type=TranslationType.PETITION,
        target_jurisdiction="turkey",
        legal_domain="custody"
    )

    result = await translator.translate(request)

    print(f"\n✓ Translation Completed!")
    print(f"  - Confidence: {result.confidence*100:.0f}%")

    print(f"\n📄 ORIGINAL (English):")
    print("-" * 60)
    print(request.source_text.strip())

    print(f"\n📄 TRANSLATED (Turkish):")
    print("-" * 60)
    print(result.translated_text)

    return result


async def test_quick_translation():
    """Test quick translation without annotations."""
    print("\n" + "="*60)
    print("TEST: Quick Translation (No Annotations)")
    print("="*60)

    translator = LegalTranslator()

    # Quick translations
    test_phrases = [
        ("Velayet davası", "tr", "en"),
        ("Nafaka", "tr", "en"),
        ("Custody petition", "en", "tr"),
        ("Sorgerecht", "de", "en")
    ]

    for phrase, src, tgt in test_phrases:
        result = await translator.quick_translate(phrase, src, tgt)
        print(f"  {phrase} ({src}) → {result} ({tgt})")

    print("\n✓ All quick translations completed!")


async def test_batch_translation():
    """Test batch translation."""
    print("\n" + "="*60)
    print("TEST: Batch Translation")
    print("="*60)

    translator = LegalTranslator()

    legal_terms = [
        "Velayet",
        "Nafaka",
        "Kişisel ilişki kurma hakkı",
        "Çocuğun üstün yararı",
        "Gözetim altında görüşme"
    ]

    results = await translator.translate_batch(
        texts=legal_terms,
        source_language="tr",
        target_language="en",
        translation_type=TranslationType.TERMINOLOGY
    )

    print(f"\n✓ Batch translation completed: {len(results)} terms")
    print("\n📖 LEGAL TERMINOLOGY:")
    print("-" * 60)

    for i, result in enumerate(results):
        print(f"{i+1}. {legal_terms[i]} → {result.translated_text}")
        print(f"   Confidence: {result.confidence*100:.0f}%")


async def main():
    """Run all translation tests."""
    print("\n" + "="*60)
    print("AI Legal Translation Test Suite")
    print("="*60)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n✗ ANTHROPIC_API_KEY not found!")
        return

    print(f"✓ API Key found: {api_key[:20]}...")

    results = []

    # Test 1: Turkish to English
    try:
        result1 = await test_turkish_to_english()
        results.append(("Turkish to English", True, result1))
    except Exception as e:
        print(f"\n✗ Turkish to English test FAILED: {e}")
        results.append(("Turkish to English", False, None))

    # Test 2: German to English
    try:
        result2 = await test_german_to_english()
        results.append(("German to English", True, result2))
    except Exception as e:
        print(f"\n✗ German to English test FAILED: {e}")
        results.append(("German to English", False, None))

    # Test 3: English to Turkish
    try:
        result3 = await test_english_to_turkish()
        results.append(("English to Turkish", True, result3))
    except Exception as e:
        print(f"\n✗ English to Turkish test FAILED: {e}")
        results.append(("English to Turkish", False, None))

    # Test 4: Quick Translation
    try:
        await test_quick_translation()
        results.append(("Quick Translation", True, None))
    except Exception as e:
        print(f"\n✗ Quick translation test FAILED: {e}")
        results.append(("Quick Translation", False, None))

    # Test 5: Batch Translation
    try:
        await test_batch_translation()
        results.append(("Batch Translation", True, None))
    except Exception as e:
        print(f"\n✗ Batch translation test FAILED: {e}")
        results.append(("Batch Translation", False, None))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}\n")

    for test_name, success, _ in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status} - {test_name}")

    if passed == total:
        print("\n🎉 ALL TRANSLATION TESTS PASSED!")
        print("\nTranslation API Endpoints:")
        print("- POST /api/ai/translate - Full legal translation")
        print("- POST /api/ai/translate-quick - Quick translation")
        print("- POST /api/ai/translate-batch - Batch translation")
        print("- GET /api/ai/translation-languages - Language pairs")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
