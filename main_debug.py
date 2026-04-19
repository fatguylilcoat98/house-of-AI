"""
Debug version for Render deployment - tests imports step by step
"""

import sys
import traceback

def test_imports():
    print("🔍 DEBUGGING IMPORTS ON RENDER")
    print("=" * 50)

    try:
        print("✅ Python version:", sys.version)
        print("✅ Python path:", sys.path[:3])  # First 3 entries

        print("\n📦 Testing external packages...")

        print("1. FastAPI...", end=" ")
        import fastapi
        print(f"✅ {fastapi.__version__}")

        print("2. Uvicorn...", end=" ")
        import uvicorn
        print("✅")

        print("3. HTTPx...", end=" ")
        import httpx
        print("✅")

        print("4. Pydantic...", end=" ")
        import pydantic
        print(f"✅ {pydantic.__version__}")

        print("\n🏗️ Testing custom modules...")

        print("5. System Packet Builder...", end=" ")
        from system_packet_builder import SystemPacketBuilder
        print("✅")

        print("6. Council Execution Engine...", end=" ")
        from council_execution_engine import CouncilExecutionEngine
        print("✅")

        print("7. Synthesis Engine...", end=" ")
        from synthesis_engine import SynthesisEngine
        print("✅")

        print("8. Builder Instance Manager...", end=" ")
        from builder_instance_manager import BuilderInstanceManager
        print("✅")

        print("\n🚀 All imports successful!")
        print("Creating FastAPI app...")

        from fastapi import FastAPI
        app = FastAPI(title="Debug Test")

        @app.get("/")
        async def root():
            return {"status": "All imports working!", "message": "Ready for main_council.py"}

        print("✅ FastAPI app created successfully!")
        return app

    except Exception as e:
        print(f"\n❌ IMPORT FAILED: {str(e)}")
        print("\n🔍 Full traceback:")
        traceback.print_exc()

        # Create minimal app even if imports fail
        try:
            from fastapi import FastAPI
            app = FastAPI()
            @app.get("/")
            async def error_root():
                return {"error": str(e), "traceback": traceback.format_exc()}
            return app
        except:
            print("😰 Can't even create basic FastAPI app")
            return None

app = test_imports()

if __name__ == "__main__":
    if app:
        import uvicorn
        uvicorn.run("main_debug:app", host="0.0.0.0", port=8000)
    else:
        print("💥 Complete failure - no app created")