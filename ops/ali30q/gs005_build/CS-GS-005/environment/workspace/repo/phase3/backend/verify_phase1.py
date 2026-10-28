#!/usr/bin/env python3
"""
Quick verification script for Phase 1 Memory System implementation.
Run this to verify all components are in place.
"""

import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND: {path}")
        return False

def check_directory(path, description):
    """Check if a directory exists."""
    if Path(path).is_dir():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND: {path}")
        return False

def main():
    """Run verification checks."""
    print("🔍 Phase 1 Memory System - Verification")
    print("=" * 50)

    all_good = True

    # Check directories
    print("\n📁 Checking Directories...")
    all_good &= check_directory("memory", "Memory module directory")
    all_good &= check_directory("migrations", "Migrations directory")
    all_good &= check_directory("alembic/versions", "Alembic versions directory")

    # Check core implementation files
    print("\n💻 Checking Core Implementation...")
    all_good &= check_file("memory/__init__.py", "Memory module init")
    all_good &= check_file("memory/embedding_service.py", "Embedding service")
    all_good &= check_file("memory/agent_memory.py", "Agent memory system")
    all_good &= check_file("memory/reflection_system.py", "Reflection system")

    # Check API files
    print("\n🌐 Checking API Layer...")
    all_good &= check_file("api/memory.py", "Memory API endpoints")
    all_good &= check_file("utils/db_pool.py", "Database pool utility")

    # Check database files
    print("\n🗄️ Checking Database Files...")
    all_good &= check_file("migrations/add_memory_system.sql", "SQL migration")
    all_good &= check_file("alembic/versions/002_add_memory_system.py", "Alembic migration")

    # Check testing
    print("\n🧪 Checking Test Files...")
    all_good &= check_file("test_memory_system.py", "Test script")

    # Check documentation
    print("\n📚 Checking Documentation...")
    all_good &= check_file("MEMORY_SYSTEM_IMPLEMENTATION.md", "Implementation guide")
    all_good &= check_file("MEMORY_SYSTEM_INSTALL.md", "Installation guide")
    all_good &= check_file("PHASE1_SUMMARY.md", "Phase 1 summary")
    all_good &= check_file("PHASE1_COMPLETE_REPORT.md", "Complete report")
    all_good &= check_file("MEMORY_QUICK_REFERENCE.md", "Quick reference")
    all_good &= check_file("PHASE1_FINAL.md", "Final report")

    # Check modified files
    print("\n📝 Checking Modified Files...")
    all_good &= check_file("requirements.txt", "Requirements file")
    all_good &= check_file("api/tasks.py", "Tasks API (modified)")
    all_good &= check_file("main.py", "Main application (modified)")

    # Check dependencies in requirements.txt
    print("\n📦 Checking Dependencies...")
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
            deps = [
                "sentence-transformers",
                "torch",
                "transformers",
                "chromadb",
                "pgvector"
            ]
            for dep in deps:
                if dep in content:
                    print(f"✅ {dep} in requirements.txt")
                else:
                    print(f"❌ {dep} NOT in requirements.txt")
                    all_good = False
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        all_good = False

    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All Phase 1 components verified!")
        print("\n📋 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Setup database: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector")
        print("3. Run migration: alembic upgrade head")
        print("4. Test system: python test_memory_system.py")
        print("5. Start server: uvicorn main:app --reload")
        return 0
    else:
        print("❌ Some components are missing!")
        print("\n⚠️ Please review the errors above and ensure all files are in place.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
