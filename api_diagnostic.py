#!/usr/bin/env python3
"""
API Diagnostic Script
Tests each API individually with detailed error reporting
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_claude_api():
    """Test Claude API with detailed diagnostics"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"success": False, "error": "No API key found"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": "Say OK"}]
                }
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data["content"][0]["text"],
                    "usage": data.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "headers": dict(response.headers)
                }

    except Exception as e:
        return {"success": False, "error": str(e)}

async def test_gemini_api():
    """Test Gemini API with detailed diagnostics"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {"success": False, "error": "No API key found"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": "Say OK"}]}],
                    "generationConfig": {"maxOutputTokens": 50}
                }
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data["candidates"][0]["content"]["parts"][0]["text"]
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "headers": dict(response.headers)
                }

    except Exception as e:
        return {"success": False, "error": str(e)}

async def test_perplexity_api():
    """Test Perplexity API with detailed diagnostics"""
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        return {"success": False, "error": "No API key found"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 50
                }
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data["choices"][0]["message"]["content"]
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "headers": dict(response.headers)
                }

    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    """Run all API tests"""
    print("=== API DIAGNOSTIC REPORT ===\n")

    tests = [
        ("Claude (Anthropic)", test_claude_api),
        ("Gemini (Google)", test_gemini_api),
        ("Perplexity", test_perplexity_api)
    ]

    for name, test_func in tests:
        print(f"Testing {name}...")
        result = await test_func()

        if result["success"]:
            print(f"  SUCCESS SUCCESS: {result['response']}")
        else:
            print(f"  FAILED FAILED")
            print(f"     Error: {result.get('error', 'Unknown')}")
            if "status_code" in result:
                print(f"     Status: {result['status_code']}")
        print()

if __name__ == "__main__":
    asyncio.run(main())