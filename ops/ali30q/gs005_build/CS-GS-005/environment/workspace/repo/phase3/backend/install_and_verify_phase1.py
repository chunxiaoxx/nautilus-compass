#!/usr/bin/env python3
"""
Phase 1 Memory System - Complete Installation and Verification Script

This script performs a complete installation and verification of the Phase 1 memory system.
It checks all components, installs dependencies, and runs tests.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_step(step_num, text):
    """Print a step header."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 60)

def run_command(cmd, description, check=True):
    """Run a shell command and return success status."""
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_file_exists(path, description):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def main():
    """Main installation and verification process."""
    print_header("Phase 1: Evomap.ai Memory System")
    print("Complete Installation and Verification")

    all_checks_passed = True

    # Step 1: Verify file structure
    print_step(1, "Verifying File Structure")

    files_to_check = [
        ("memory/__init__.py", "Memory module init"),
        ("memory/embedding_service.py", "Embedding service"),
        ("memory/agent_memory.py", "Agent memory system"),
        ("memory/reflection_system.py", "Reflection system"),
        ("api/memory.py", "Memory API"),
        ("utils/db_pool.py", "Database pool"),
        ("migrations/add_memory_system.sql", "SQL migration"),
        ("alembic/versions/002_add_memory_system.py", "Alembic migration"),
        ("test_memory_system.py", "Test script"),
        ("requirements.txt", "Requirements file"),
    ]

    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Step 2: Check dependencies in requirements.txt
    print_step(2, "Checking Dependencies")

    required_deps = [
        "sentence-transformers",
        "torch",
        "transformers",
        "chromadb",
        "pgvector"
    ]

    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
            for dep in required_deps:
                if dep in content:
                    print(f"✅ {dep} found in requirements.txt")
                else:
                    print(f"❌ {dep} NOT found in requirements.txt")
                    all_checks_passed = False
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        all_checks_passed = False

    # Step 3: Install dependencies
    print_step(3, "Installing Dependencies")

    install_deps = input("\nInstall dependencies now? (y/n): ").lower().strip()
    if install_deps == 'y':
        if run_command(
            "pip install -r requirements.txt",
            "Installing Python dependencies",
            check=False
        ):
            print("✅ Dependencies installed successfully")
        else:
            print("⚠️ Some dependencies may have failed to install")
            all_checks_passed = False
    else:
        print("⏭️ Skipping dependency installation")

    # Step 4: Check PostgreSQL and pgvector
    print_step(4, "Checking Database Setup")

    print("\n📋 Database Requirements:")
    print("- PostgreSQL 12+ with pgvector extension")
    print("- Recommended: Docker with ankane/pgvector image")
    print("\nDocker command:")
    print("  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector")

    db_ready = input("\nIs PostgreSQL with pgvector ready? (y/n): ").lower().strip()
    if db_ready != 'y':
        print("⚠️ Please setup PostgreSQL with pgvector before continuing")
        all_checks_passed = False

    # Step 5: Run database migration
    print_step(5, "Database Migration")

    if db_ready == 'y':
        run_migration = input("\nRun database migration now? (y/n): ").lower().strip()
        if run_migration == 'y':
            if run_command(
                "alembic upgrade head",
                "Running Alembic migration",
                check=False
            ):
                print("✅ Migration completed successfully")
            else:
                print("⚠️ Migration may have failed - check logs")
                all_checks_passed = False
        else:
            print("⏭️ Skipping migration")

    # Step 6: Run tests
    print_step(6, "Running Tests")

    run_tests = input("\nRun test suite now? (y/n): ").lower().strip()
    if run_tests == 'y':
        if run_command(
            "python test_memory_system.py",
            "Running memory system tests",
            check=False
        ):
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")
            all_checks_passed = False
    else:
        print("⏭️ Skipping tests")

    # Step 7: Summary
    print_header("Installation Summary")

    if all_checks_passed:
        print("\n✅ Phase 1 Memory System - Installation Complete!")
        print("\n📋 Next Steps:")
        print("1. Start the server: uvicorn main:app --reload")
        print("2. Check API docs: http://localhost:8000/docs")
        print("3. Test endpoints: http://localhost:8000/api/memory/memories")
        print("\n📚 Documentation:")
        print("- Quick Start: PHASE1_README.md")
        print("- Full Report: PHASE1_FINAL.md")
        print("- Quick Reference: MEMORY_QUICK_REFERENCE.md")
        print("- Installation Guide: MEMORY_SYSTEM_INSTALL.md")
        return 0
    else:
        print("\n⚠️ Installation completed with warnings")
        print("\nPlease review the errors above and:")
        print("1. Ensure all files are present")
        print("2. Install missing dependencies")
        print("3. Setup PostgreSQL with pgvector")
        print("4. Run migrations")
        print("5. Run tests to verify")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
