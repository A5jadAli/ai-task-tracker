# -*- coding: utf-8 -*-
"""
Demonstration of the hybrid agent with various tasks.
Shows how shortcuts + AI + verification work together.
"""

from agent.core import AutonomousAgent


def demo_1_open_app():
    """Demo 1: Open an application reliably using shortcuts."""
    print("\n" + "=" * 70)
    print("DEMO 1: OPEN APPLICATION (Shortcut-based)")
    print("=" * 70)
    agent = AutonomousAgent()
    agent.run("Open Notepad")


def demo_2_install_package():
    """Demo 2: Install a Python package with verification."""
    print("\n" + "=" * 70)
    print("DEMO 2: INSTALL PYTHON PACKAGE (Verified)")
    print("=" * 70)
    agent = AutonomousAgent()
    agent.run("Install the requests package using pip")


def demo_3_write_code():
    """Demo 3: AI-based task - write code."""
    print("\n" + "=" * 70)
    print("DEMO 3: WRITE CODE (AI-based)")
    print("=" * 70)
    agent = AutonomousAgent()
    agent.run("Write a Python function that calculates the factorial of a number")


def demo_4_complex_workflow():
    """Demo 4: Complex workflow mixing shortcuts and AI."""
    print("\n" + "=" * 70)
    print("DEMO 4: COMPLEX WORKFLOW (Mixed)")
    print("=" * 70)
    agent = AutonomousAgent()
    agent.run("Open VSCode and write a Python script for fibonacci sequence")


def demo_5_file_operations():
    """Demo 5: File creation and verification."""
    print("\n" + "=" * 70)
    print("DEMO 5: FILE OPERATIONS (With Verification)")
    print("=" * 70)
    agent = AutonomousAgent()
    agent.run("Create a new text file with hello world content")


def run_interactive():
    """Run interactive mode where user enters goal."""
    print("\n" + "=" * 70)
    print("HYBRID AGENT - INTERACTIVE MODE")
    print("=" * 70)
    print("\nEnter your goal for the agent:")
    print("Examples:")
    print("  - Open Chrome")
    print("  - Install numpy package")
    print("  - Write a function to reverse a string")
    print("  - Create a new Python file")
    print()

    goal = input("Your goal: ").strip()
    if goal:
        agent = AutonomousAgent()
        success = agent.run(goal)

        if success:
            print("\n[OK] Goal completed successfully!")
        else:
            print("\n[FAIL] Goal could not be completed")


def main():
    """Main demo runner."""
    print("\n" + "=" * 70)
    print("HYBRID AI AGENT DEMONSTRATION")
    print("=" * 70)
    print("\nChoose a demo:")
    print("1. Open Application (Shortcut-based, 100% reliable)")
    print("2. Install Package (Verified execution)")
    print("3. Write Code (AI-powered)")
    print("4. Complex Workflow (Mixed approach)")
    print("5. File Operations (With verification)")
    print("6. Interactive Mode (Enter your own goal)")
    print("0. Exit")
    print()

    choice = input("Select demo (0-6): ").strip()

    if choice == "1":
        demo_1_open_app()
    elif choice == "2":
        demo_2_install_package()
    elif choice == "3":
        demo_3_write_code()
    elif choice == "4":
        demo_4_complex_workflow()
    elif choice == "5":
        demo_5_file_operations()
    elif choice == "6":
        run_interactive()
    elif choice == "0":
        print("Exiting...")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
