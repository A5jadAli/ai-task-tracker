import argparse
from agent.core import AutonomousAgent


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid AI Agent - Uses shortcuts for reliable tasks, AI for complex ones"
    )
    parser.add_argument("--goal", type=str, help="The goal for the agent to achieve")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    args = parser.parse_args()

    if args.demo:
        print("Running demo tasks...")
        agent = AutonomousAgent()

        # Example: Open an application
        print("\n" + "=" * 60)
        print("DEMO 1: Open VSCode")
        print("=" * 60)
        agent.run("Open VSCode")

        return

    goal = args.goal
    if not goal:
        goal = input("Enter a goal for the agent: ")

    agent = AutonomousAgent()
    success = agent.run(goal)

    if success:
        print("\n✓ Agent completed successfully!")
    else:
        print("\n✗ Agent failed to complete the goal")


if __name__ == "__main__":
    main()
