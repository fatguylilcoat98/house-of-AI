#!/usr/bin/env python3
"""
Gemini API Diagnostic Script
Comprehensive testing of different Gemini configurations
"""

import asyncio
import httpx
import json
from dotenv import load_dotenv
import os

load_dotenv()

async def test_gemini_configurations():
    """Test different Gemini API configurations"""
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"Testing Gemini API key: {api_key[:15]}...")
    print("=" * 50)

    # Test different API versions and models
    configurations = [
        # v1beta configurations
        {
            "url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}",
            "description": "v1beta + gemini-pro"
        },
        {
            "url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            "description": "v1beta + gemini-1.5-flash"
        },
        {
            "url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}",
            "description": "v1beta + gemini-1.5-pro"
        },
        # v1 configurations
        {
            "url": f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}",
            "description": "v1 + gemini-pro"
        },
        {
            "url": f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}",
            "description": "v1 + gemini-1.5-flash"
        },
        {
            "url": f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}",
            "description": "v1 + gemini-1.5-pro"
        }
    ]

    test_payload = {
        "contents": [{"parts": [{"text": "Say 'Hello from Gemini'"}]}],
        "generationConfig": {"maxOutputTokens": 10}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for config in configurations:
            print(f"\nTesting: {config['description']}")
            try:
                response = await client.post(
                    config['url'],
                    headers={"Content-Type": "application/json"},
                    json=test_payload
                )

                if response.status_code == 200:
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"  [SUCCESS]: {text}")
                    print(f"  [WORKING CONFIG]: {config['description']}")
                    return config  # Return the working config
                else:
                    print(f"  [FAILED]: {response.status_code}")
                    error_text = response.text[:100] + "..." if len(response.text) > 100 else response.text
                    print(f"    Error: {error_text}")

            except Exception as e:
                print(f"  [EXCEPTION]: {str(e)[:100]}...")

            await asyncio.sleep(1)  # Avoid rate limits

    print(f"\n[NO WORKING CONFIG] No working Gemini configuration found")
    return None

async def list_available_models():
    """List available Gemini models"""
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"\n[MODELS] Listing available models...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            )

            if response.status_code == 200:
                models = response.json()
                print("Available models that support generateContent:")
                for model in models.get('models', []):
                    name = model.get('name', '').replace('models/', '')
                    methods = model.get('supportedGenerationMethods', [])
                    if 'generateContent' in methods:
                        print(f"  - {name}")
                return True
            else:
                print(f"Failed to list models: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"Error listing models: {e}")
            return False

if __name__ == "__main__":
    async def main():
        await list_available_models()
        working_config = await test_gemini_configurations()

        if working_config:
            print(f"\n[SOLUTION FOUND]")
            print(f"Use this configuration: {working_config['description']}")
            print(f"URL pattern: {working_config['url'].split('?')[0]}")
        else:
            print(f"\n[TROUBLESHOOTING] Try checking:")
            print(f"1. API key permissions/restrictions")
            print(f"2. Billing/quota limits")
            print(f"3. Regional restrictions")

    asyncio.run(main())