"""
Test script for memory system functionality.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db_pool import init_db_pool, close_db_pool
from memory.agent_memory import get_memory_system
from memory.reflection_system import get_reflection_system


async def test_memory_system():
    """Test the memory system."""
    print("🧪 Testing Memory System...")

    try:
        # Initialize database pool
        print("\n1. Initializing database pool...")
        db_pool = await init_db_pool()
        print("✅ Database pool initialized")

        # Get memory system
        print("\n2. Getting memory system...")
        memory_system = await get_memory_system(db_pool)
        print("✅ Memory system initialized")

        # Test storing a memory
        print("\n3. Storing test memory...")
        execution_data = {
            "description": "Test task for memory system",
            "task_type": "CODE",
            "status": "COMPLETED",
            "result": "Successfully completed test task",
            "reward": 1000000000000000000
        }

        memory_id = await memory_system.store_task_memory(
            agent_id=1,
            task_id=1,
            execution_data=execution_data,
            memory_type="task_execution"
        )
        print(f"✅ Memory stored with ID: {memory_id}")

        # Test retrieving recent memories
        print("\n4. Retrieving recent memories...")
        memories = await memory_system.get_recent_memories(
            agent_id=1,
            limit=5
        )
        print(f"✅ Retrieved {len(memories)} memories")
        for mem in memories:
            print(f"   - Memory {mem['id']}: {mem['memory_type']}")

        # Test similarity search
        print("\n5. Testing similarity search...")
        similar = await memory_system.find_similar_memories(
            agent_id=1,
            query_text="code development task",
            limit=3
        )
        print(f"✅ Found {len(similar)} similar memories")
        for mem in similar:
            print(f"   - Memory {mem['id']}: similarity={mem['similarity']:.3f}")

        # Test memory stats
        print("\n6. Getting memory statistics...")
        stats = await memory_system.get_memory_stats(agent_id=1)
        print(f"✅ Memory stats:")
        print(f"   - Total memories: {stats['total_memories']}")
        print(f"   - Memory types: {stats['memory_types']}")
        print(f"   - Unique tasks: {stats['unique_tasks']}")

        # Test reflection system
        print("\n7. Testing reflection system...")
        reflection_system = await get_reflection_system(db_pool, memory_system)
        print("✅ Reflection system initialized")

        # Create a reflection
        print("\n8. Creating reflection...")
        result = {
            "description": "Test task",
            "task_type": "CODE",
            "status": "COMPLETED",
            "result": "Success",
            "execution_time": 120
        }

        reflection_id = await reflection_system.reflect_on_task(
            agent_id=1,
            task_id=1,
            result=result
        )
        print(f"✅ Reflection created with ID: {reflection_id}")

        # Get agent skills
        print("\n9. Getting agent skills...")
        skills = await reflection_system.get_agent_skills(agent_id=1)
        print(f"✅ Retrieved {len(skills)} skills")
        for skill in skills:
            print(f"   - {skill['skill_name']}: Level {skill['skill_level']}, "
                  f"Success rate: {skill['success_rate']:.2%}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n10. Closing database pool...")
        await close_db_pool()
        print("✅ Database pool closed")

    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run tests
    success = asyncio.run(test_memory_system())
    sys.exit(0 if success else 1)
