# Hybrid AI Agent - New Architecture

## Overview

The agent has been refactored from a pure AI/screenshot-based system to a **hybrid architecture** that combines:

- **Keyboard Shortcuts**: 100% reliable, deterministic operations (no AI guessing)
- **Verification System**: Confirms actions succeeded without AI interpretation
- **Task Decomposition**: Breaks complex goals into simpler subtasks
- **State Machine**: Tracks execution state and prevents invalid operations
- **AI for Complex Tasks**: Uses AI only for code writing, analysis, and complex decision-making

## Why This Approach is Better

### Old System (Pure AI Loop)
```
Screenshot → AI interprets pixels → Click/type → Loop
```
**Problems:**
- AI can misinterpret screenshots (wrong coordinates, invisible UI elements)
- No verification that action actually worked
- Slow (screenshot-analyze loop after every action)
- Expensive (many vision API calls)

### New System (Hybrid)
```
Simple tasks (open apps, tabs, etc) → Use shortcuts (100% reliable)
Complex tasks (code writing) → Use AI
Always verify after actions → No guessing
```
**Benefits:**
- Shortcuts are deterministic - they always work the same way
- AI focuses on what it's good at (understanding, writing, analyzing)
- Verification ensures tasks actually succeeded
- Fewer API calls = faster & cheaper
- Structured task execution with state tracking

## Architecture Components

### 1. **ShortcutsActionExecutor** (`shortcuts_actions.py`)
Executes common tasks using keyboard shortcuts, not mouse clicks.

```python
shortcuts = ShortcutsActionExecutor()
shortcuts.open_application("vscode")      # Opens VSCode
shortcuts.switch_tab("next")              # Ctrl+Tab
shortcuts.save_file()                     # Ctrl+S
shortcuts.run_command("pip install x")    # Execute terminal command
```

**Supported operations:**
- Application management (open, close, check if running)
- Tab management (open new, switch, close)
- File operations (open, save, save as)
- Text editing (type, paste, undo, redo)
- Terminal commands
- Window management

### 2. **Verifier** (`verification.py`)
Checks if actions succeeded deterministically (no AI guessing).

```python
verifier = Verifier()
verifier.app_is_running("vscode")         # Check process list
verifier.file_exists("/path/to/file")     # Check file system
verifier.package_is_installed("numpy")    # Check pip packages
verifier.command_succeeds("npm install")  # Verify exit code
```

**Verification types:**
- Application running/closed
- File exists/doesn't exist/has content
- Directory exists/has files
- Text in file
- Command exit code
- Package installation
- Custom conditions

### 3. **TaskDecomposer** (`task_decomposer.py`)
Breaks complex goals into structured subtasks.

```python
decomposer = TaskDecomposer()
plan = decomposer.decompose("Open VSCode and write a Python function")
# Returns: [open_app → verify → ai_task]
```

**Task types:**
- `SHORTCUT`: Use keyboard shortcuts
- `COMMAND`: Run terminal command
- `VERIFY`: Check if something happened
- `AI`: Use AI for complex reasoning

**Example decomposition:**
```
Goal: "Install Flask and create a new project"
↓
Tasks:
  1. [SHORTCUT] Open terminal
  2. [COMMAND] Run: pip install flask
  3. [VERIFY] Package is installed
  4. [SHORTCUT] Open VSCode
  5. [VERIFY] VSCode opened
  6. [AI] Generate project structure
```

### 4. **StateMachine** (`state_machine.py`)
Tracks execution state and prevents invalid operations.

```
INITIALIZED → PLANNING → READY → EXECUTING → VERIFYING → SUCCESS
                  ↓         ↓         ↓         ↓
                FAILED  CANCELLED  PAUSED   FAILED
```

**Prevents:**
- Executing before planning
- Verifying before executing
- Invalid state transitions
- Inconsistent execution flow

### 5. **AutonomousAgent** (refactored `core.py`)
Main agent that orchestrates everything.

```python
agent = AutonomousAgent()
agent.run("Open VSCode and write a Python function")
```

**Flow:**
1. Decompose goal into tasks
2. For each task (in order of dependencies):
   - Execute based on task type (shortcut/command/AI/verify)
   - Track execution with state machine
   - Verify result
3. Report success/failure

## Usage

### Basic Usage
```bash
python main.py --goal "Open Notepad"
```

### Interactive Mode
```bash
python demo_agent.py
# Choose demo option 6 for interactive mode
```

### Programmatic Usage
```python
from agent.core import AutonomousAgent

agent = AutonomousAgent()

# Simple shortcut task
agent.run("Open Chrome")

# Package installation with verification
agent.run("Install the requests package using pip")

# AI-based task
agent.run("Write a Python function that calculates fibonacci")

# Complex workflow
agent.run("Open VSCode and create a hello world Python file")
```

## Running Tests

```bash
python test_suite.py
```

This runs comprehensive tests on all components:
- Shortcuts actions
- Verification system
- Task decomposition
- State machine
- Integration tests

## Configuration

### Environment Variables (`.env`)
```
# AI Provider (gemini or openai)
MODEL_PROVIDER=gemini
MODEL_NAME=gemini-2.0-flash-exp

# API Keys
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Human approval before executing
HUMAN_IN_THE_LOOP=false
```

## Examples

### Example 1: Open Application
```python
agent.run("Open VSCode")
```
**Flow:**
1. Decompose → Open app task
2. Execute → Use subprocess to launch VSCode
3. Verify → Check process list
4. Success ✓

### Example 2: Install Package
```python
agent.run("Install the Flask package using pip")
```
**Flow:**
1. Decompose → Open terminal, run pip, verify
2. Execute terminal command → `pip install flask`
3. Verify → Check with `pip show flask`
4. Success ✓

### Example 3: Write Code
```python
agent.run("Write a Python function that reverses a string")
```
**Flow:**
1. Decompose → AI task
2. Ask AI → Generate function code
3. Show code to user
4. Success ✓

### Example 4: Complex Workflow
```python
agent.run("Open VSCode and write a function that calculates factorial")
```
**Flow:**
1. Decompose:
   - [SHORTCUT] Open VSCode
   - [VERIFY] VSCode opened
   - [AI] Write factorial function code
   - [VERIFY] Code ready
2. Execute each task in sequence
3. Success ✓

## Key Improvements

| Aspect | Old System | New System |
|--------|-----------|-----------|
| **Reliability** | AI guesses coordinates (error-prone) | Keyboard shortcuts (100% reliable) |
| **Verification** | Screenshot interpretation | Process list, file system checks |
| **Task Handling** | Loop-based, no structure | Structured tasks with dependencies |
| **AI Usage** | Every decision (overhead) | Only complex tasks (efficient) |
| **State Tracking** | History list only | Full state machine with validation |
| **Error Handling** | Screenshot-based retry | Deterministic verification + retry |
| **Speed** | Screenshot after each action (slow) | Only verify when needed (fast) |
| **Cost** | Many vision API calls | Minimal AI usage |

## Extending the System

### Add New Shortcut Action
Edit `shortcuts_actions.py`:
```python
def your_action(self, param1, param2):
    """Description of your action."""
    try:
        # Your code here
        print(f"✓ Action completed")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
```

### Add New Verification
Edit `verification.py`:
```python
def verify_your_condition(self, param1):
    """Verify custom condition."""
    # Check your condition
    if condition_met:
        print(f"✓ Verified: Condition met")
        return True
    else:
        print(f"✗ Verification failed")
        return False
```

### Add New Task Type
Edit `task_decomposer.py`:
```python
def decompose(self, goal: str) -> TaskPlan:
    # ... existing code ...
    
    # Your new decomposition rule
    if "your_keyword" in goal_lower:
        plan.add_shortcut_task(...)
        return plan
```

## Troubleshooting

**Agent not opening applications:**
- Ensure applications are installed and in PATH
- Check `is_app_running()` works for your app

**Verification failing:**
- Increase timeout values
- Check file paths are absolute
- Verify commands manually first

**AI not responding:**
- Check API keys in `.env`
- Verify internet connection
- Check rate limits haven't been exceeded

## Future Enhancements

1. **Learning**: Track which tasks fail most and optimize decomposition
2. **Parallel Execution**: Execute independent tasks in parallel
3. **Rollback**: Undo failed tasks automatically
4. **GUI Dashboard**: Visual task execution tracker
5. **Custom Task Registry**: User-defined task types
6. **Performance Analytics**: Track execution time and success rates

## Architecture Diagram

```
User Input (Goal)
        ↓
  Task Decomposer ← Uses patterns to break into subtasks
        ↓
  Task Queue (with dependencies)
        ↓
   State Machine (validates state)
        ↓
   ┌─────────────────────────────┐
   │  For Each Task:             │
   │  ┌─────────────────────────┐│
   │  │ Task Type?              ││
   │  ├─────────────────────────┤│
   │  │ SHORTCUT → Shortcuts    ││
   │  │ COMMAND  → Subprocess   ││
   │  │ AI       → Brain        ││
   │  │ VERIFY   → Verification ││
   │  └─────────────────────────┘│
   │         ↓                     │
   │      Execute                  │
   │         ↓                     │
   │      Verify                   │
   │         ↓                     │
   │   Update State                │
   └─────────────────────────────┘
        ↓
   All Tasks Done?
        ├─ Yes → SUCCESS
        └─ No → Next Task

Success/Failure Report
```

---

**Last Updated**: December 2024
**Version**: 2.0 (Hybrid Architecture)
