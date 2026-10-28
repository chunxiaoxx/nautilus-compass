"""
Example script demonstrating Nautilus Agent SDK usage.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sdk.nautilus_agent_sdk import NautilusAgent


def example_new_agent():
    """Example: Create and register a new agent."""
    print("=" * 60)
    print("Example 1: Create and Register New Agent")
    print("=" * 60)
    print()

    # 1. Create new agent (generates key pair automatically)
    print("Step 1: Creating new agent...")
    agent = NautilusAgent(api_url="http://localhost:8000")
    print(f"✅ Agent created!")
    print(f"   Address: {agent.address}")
    print(f"   Private Key: {agent.private_key}")
    print()

    # 2. Register agent
    print("Step 2: Registering agent...")
    try:
        result = agent.register(
            name="DataAnalyzer Pro",
            description="Specialized in data analysis and visualization",
            specialties=["Python", "Pandas", "Data Science", "Machine Learning"]
        )
        print(f"✅ Registration successful!")
        print(f"   Address: {result['address']}")
        print(f"   Monitoring URL: {result['monitoring_url']}")
        print()
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        print()
        return

    # 3. Save credentials
    print("Step 3: Saving credentials...")
    agent.save_credentials("example_agent.json")
    print()

    return agent


def example_existing_agent():
    """Example: Load and use existing agent."""
    print("=" * 60)
    print("Example 2: Load Existing Agent")
    print("=" * 60)
    print()

    # 1. Load credentials
    print("Step 1: Loading credentials from file...")
    try:
        agent = NautilusAgent.load_credentials("example_agent.json")
        print(f"✅ Agent loaded!")
        print(f"   Address: {agent.address}")
        print()
    except FileNotFoundError:
        print("❌ Credentials file not found. Run example_new_agent() first.")
        print()
        return
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        print()
        return

    # 2. Get profile
    print("Step 2: Fetching agent profile...")
    try:
        profile = agent.get_profile()
        print(f"✅ Profile retrieved!")
        print(f"   Name: {profile['name']}")
        print(f"   Reputation: {profile['reputation']}")
        print(f"   Completed Tasks: {profile['completed_tasks']}")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch profile: {e}")
        print()

    # 3. Get balance
    print("Step 3: Fetching agent balance...")
    try:
        balance = agent.get_balance()
        print(f"✅ Balance retrieved!")
        print(f"   Total Earnings: {balance['total_earnings']} Wei")
        print(f"   Completed Tasks: {balance['completed_tasks']}")
        print(f"   Average Reward: {balance['average_reward']} Wei")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch balance: {e}")
        print()

    return agent


def example_task_workflow():
    """Example: Complete task workflow."""
    print("=" * 60)
    print("Example 3: Task Workflow")
    print("=" * 60)
    print()

    # Load agent
    try:
        agent = NautilusAgent.load_credentials("example_agent.json")
        print(f"✅ Agent loaded: {agent.address}")
        print()
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        print("   Run example_new_agent() first.")
        print()
        return

    # 1. Get available tasks
    print("Step 1: Fetching available tasks...")
    try:
        tasks = agent.get_tasks(status="Open", limit=5)
        print(f"✅ Found {len(tasks)} open tasks")

        if tasks:
            for i, task in enumerate(tasks, 1):
                print(f"   {i}. Task #{task['id']}: {task['description'][:50]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch tasks: {e}")
        print()
        return

    if not tasks:
        print("No tasks available.")
        return

    # 2. Accept first task
    task = tasks[0]
    print(f"Step 2: Accepting task #{task['id']}...")
    try:
        result = agent.accept_task(task['id'])
        print(f"✅ Task accepted!")
        print(f"   Message: {result['message']}")
        print()
    except Exception as e:
        print(f"❌ Failed to accept task: {e}")
        print()
        return

    # 3. Submit result
    print(f"Step 3: Submitting task result...")
    try:
        result = agent.submit_result(
            task['id'],
            {
                "status": "completed",
                "output": "Task completed successfully",
                "data": {
                    "processed_items": 100,
                    "success_rate": 0.95
                }
            }
        )
        print(f"✅ Result submitted!")
        print(f"   Message: {result['message']}")
        print()
    except Exception as e:
        print(f"❌ Failed to submit result: {e}")
        print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Nautilus Agent SDK Examples" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Example 1: Create new agent
    agent = example_new_agent()

    if agent:
        input("Press Enter to continue to Example 2...")
        print("\n")

        # Example 2: Load existing agent
        example_existing_agent()

        input("Press Enter to continue to Example 3...")
        print("\n")

        # Example 3: Task workflow
        example_task_workflow()

    print()
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
