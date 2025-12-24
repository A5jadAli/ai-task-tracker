# AI Coding Assistant

An AI-powered autonomous coding assistant that can handle development tasks end-to-end with human oversight.

## Features

- 🤖 Autonomous development with AI agents
- 📋 Automatic planning with human approval workflow
- 🔄 Git integration (branch, commit, push)
- 🧪 Automated testing
- 💾 Project context memory
- 📊 Detailed completion reports

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-coding-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## Usage

### 1. Register a Project

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "repository_url": "git@github.com:user/repo.git",
    "context": {
      "tech_stack": ["fastapi", "postgresql"],
      "coding_style": "black"
    }
  }'
```

### 2. Create a Task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project-uuid>",
    "description": "Create a REST API endpoint for user registration",
    "priority": "high"
  }'
```

### 3. Monitor Progress

```bash
curl http://localhost:8000/api/status/<task-uuid>
```

### 4. Approve Plan

```bash
curl -X POST http://localhost:8000/api/tasks/<task-uuid>/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

## Project Structure

```
ai-coding-assistant/
├── app/
│   ├── agents/          # AI agents (planner, developer, tester)
│   ├── api/             # FastAPI routes and schemas
│   ├── memory/          # Context and memory management
│   ├── tools/           # Git, file, and test tools
│   ├── services/        # Business logic
│   └── models/          # Database models
├── storage/             # Project workspaces and reports
├── tests/               # Test suite
└── requirements.txt     # Dependencies
```

## Architecture

The system uses a multi-agent architecture with LangGraph:

1. **Orchestrator Agent**: Coordinates the entire workflow
2. **Planner Agent**: Generates implementation plans
3. **Developer Agent**: Writes code
4. **Tester Agent**: Tests implementations
5. **Git Agent**: Handles version control

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
