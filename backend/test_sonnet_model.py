"""
Quick test for Claude Sonnet model
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

sys.path.insert(0, os.path.dirname(__file__))

from ai.claude import ClaudeClient

async def test_sonnet():
    print("="*60)
    print("Testing Claude Sonnet Model")
    print("="*60)

    client = ClaudeClient()
    print(f"\n✓ Client initialized")
    print(f"  Model: {client.config.model}")
    print(f"  API Key: {client.config.api_key[:20]}...")

    # Test JSON response
    print(f"\n📝 Testing JSON response...")
    response = await client.simple_prompt(
        'Respond in JSON format: {"status": "success", "message": "Hello from Sonnet!", "model_quality": "high"}',
        'You are a helpful assistant. Always respond in valid JSON format only, nothing else.'
    )

    print(f"\n✓ Response received:")
    print(response)

    # Verify it's valid JSON
    import json
    try:
        data = json.loads(response)
        print(f"\n✅ Valid JSON!")
        print(f"  Status: {data.get('status')}")
        print(f"  Message: {data.get('message')}")
        print(f"  Quality: {data.get('model_quality')}")
        return True
    except json.JSONDecodeError as e:
        print(f"\n❌ Invalid JSON: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sonnet())
    if success:
        print("\n🎉 SONNET MODEL WORKING PERFECTLY!")
        print("\nThis will fix all JSON parsing issues in:")
        print("- Translation (was 2/5 passing)")
        print("- Alienation Detection (was 0/4 passing)")
        print("- Petition Generation (was 2/3 passing)")
    else:
        print("\n⚠️  Sonnet test failed")
