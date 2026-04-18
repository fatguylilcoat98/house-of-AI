#!/usr/bin/env python3
"""
Production Deployment Test Script
Tests all providers on your live Render deployment
"""

import asyncio
import httpx
import json

async def test_production_deployment(base_url):
    """Test all providers on production deployment"""
    print("=== PRODUCTION DEPLOYMENT TEST ===\n")
    print(f"Testing: {base_url}\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Test provider status endpoint
            print("1. Testing provider status endpoint...")
            response = await client.get(f"{base_url}/api/providers/status")

            if response.status_code == 200:
                data = response.json()
                print("   SUCCESS: Provider status endpoint working")

                working_count = 0
                for provider, status in data.items():
                    is_healthy = status.get('status') == 'healthy'
                    mode = status.get('mode', 'unknown')
                    print(f"   {provider:<12} {'✓' if is_healthy else '✗'} {status.get('status', 'unknown')} (Mode: {mode})")
                    if is_healthy:
                        working_count += 1

                print(f"\n   Working Providers: {working_count}/5")
                print(f"   Council Status: {'OPERATIONAL' if working_count >= 3 else 'INSUFFICIENT'}")

                if working_count == 5:
                    print("\n🎉 SUCCESS: All 5 providers operational!")
                elif working_count >= 3:
                    print(f"\n⚠️  PARTIAL: {working_count}/5 providers working (sufficient for council)")
                else:
                    print(f"\n❌ FAILED: Only {working_count}/5 providers working")

            else:
                print(f"   FAILED: Status {response.status_code}")
                print(f"   Error: {response.text}")

        except Exception as e:
            print(f"   ERROR: {str(e)}")

# Update this with your actual Render URL
RENDER_URL = "https://your-app-name.onrender.com"

if __name__ == "__main__":
    print("Update RENDER_URL with your actual Render deployment URL")
    print("Then run: python test_production.py")
    # asyncio.run(test_production_deployment(RENDER_URL))