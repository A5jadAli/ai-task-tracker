#!/usr/bin/env python3
"""
AI Coding Assistant - Automated Project Setup Script
Run this script to generate the complete project structure and all necessary files.

Usage:
    python setup_project.py
"""

import os
from pathlib import Path


def create_directory_structure():
    """Create all project directories"""
    directories = [
        "app",
        "app/api",
        "app/api/routes",
        "app/api/schemas",
        "app/agents",
        "app/memory",
        "app/tools",
        "app/services",
        "app/models",
        "app/utils",
        "storage/projects",
        "storage/plans",
        "storage/reports",
        "storage/memory",
        "storage/memory/chroma",
        "tests",
        "alembic/versions",
        "logs",
    ]

    print("📁 Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")

    print("\n✅ Directory structure created!\n")


def create_file(filepath, content):
    """Create a file with given content"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {filepath}")


def create_init_files():
    """Create __init__.py files"""
    init_files = [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/routes/__init__.py",
        "app/api/schemas/__init__.py",
        "app/agents/__init__.py",
        "app/memory/__init__.py",
        "app/tools/__init__.py",
        "app/services/__init__.py",
        "app/models/__init__.py",
        "app/utils/__init__.py",
        "tests/__init__.py",
    ]

    print("📄 Creating __init__.py files...")
    for filepath in init_files:
        create_file(filepath, "")


def create_config_file():
    """Create config.py"""
    content = """from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Coding Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.1
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    PROJECTS_BASE_PATH: Path = Path("./storage/projects")
    PLANS_PATH: Path = Path("./storage/plans")
    REPORTS_PATH: Path = Path("./storage/reports")
    MEMORY_PATH: Path = Path("./storage/memory")
    
    # Git Configuration
    GIT_USER_NAME: str = "AI Coding Assistant"
    GIT_USER_EMAIL: str = "ai@assistant.com"
    MAIN_BRANCH_NAMES: list = ["main", "dev", "development", "master"]
    
    # Notification
    NOTIFICATION_WEBHOOK_URL: Optional[str] = None
    NOTIFICATION_EMAIL: Optional[str] = None
    
    # Agent Configuration
    MAX_ITERATIONS: int = 10
    PLANNING_TIMEOUT: int = 300
    DEVELOPMENT_TIMEOUT: int = 1800
    TESTING_TIMEOUT: int = 600
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "chroma"
    CHROMA_PERSIST_DIRECTORY: Path = Path("./storage/memory/chroma")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
settings.PROJECTS_BASE_PATH.mkdir(parents=True, exist_ok=True)
settings.PLANS_PATH.mkdir(parents=True, exist_ok=True)
settings.REPORTS_PATH.mkdir(parents=True, exist_ok=True)
settings.MEMORY_PATH.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
"""
    create_file("app/config.py", content)


def create_main_file():
    """Create main.py"""
    content = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.config import settings
from app.api.routes import tasks, projects, status


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO" if not settings.DEBUG else "DEBUG"
)
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered coding assistant with autonomous development capabilities",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(status.router, prefix="/api", tags=["Status"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
'''
    create_file("app/main.py", content)


def create_requirements():
    """Create requirements.txt"""
    content = """# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# LangChain & LangGraph
langchain==0.1.4
langchain-openai==0.0.5
langgraph==0.0.20
langchain-community==0.0.17

# OpenAI
openai==1.10.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Vector Store
chromadb==0.4.22

# Git
GitPython==3.1.41

# Background Tasks
celery==5.3.6
redis==5.0.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3

# Utilities
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.26.0
python-multipart==0.0.6

# Monitoring & Logging
loguru==0.7.2
"""
    create_file("requirements.txt", content)


def create_env_example():
    """Create .env.example"""
    content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.1

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/ai_coding_assistant

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Git Configuration
GIT_USER_NAME=AI Coding Assistant
GIT_USER_EMAIL=ai@assistant.com

# Notification (Optional)
NOTIFICATION_WEBHOOK_URL=
NOTIFICATION_EMAIL=

# Application
DEBUG=True
"""
    create_file(".env.example", content)


def create_gitignore():
    """Create .gitignore"""
    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# Storage
storage/projects/*
!storage/projects/.gitkeep
storage/plans/*
!storage/plans/.gitkeep
storage/reports/*
!storage/reports/.gitkeep
storage/memory/*
!storage/memory/.gitkeep

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Alembic
alembic/versions/*.py
!alembic/versions/__init__.py
"""
    create_file(".gitignore", content)


def create_readme():
    """Create README.md"""
    content = """# AI Coding Assistant

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
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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
curl -X POST http://localhost:8000/api/projects \\
  -H "Content-Type: application/json" \\
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
curl -X POST http://localhost:8000/api/tasks \\
  -H "Content-Type: application/json" \\
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
curl -X POST http://localhost:8000/api/tasks/<task-uuid>/approve \\
  -H "Content-Type: application/json" \\
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
"""
    create_file("README.md", content)


def create_docker_files():
    """Create Docker files"""
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs storage/projects storage/plans storage/reports storage/memory

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    create_file("Dockerfile", dockerfile)

    docker_compose = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_coding_assistant
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - db
      - redis
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=ai_coding_assistant
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A app.services.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_coding_assistant
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - db
      - redis
    volumes:
      - ./storage:/app/storage

volumes:
  postgres_data:
"""
    create_file("docker-compose.yml", docker_compose)


def create_placeholder_routes():
    """Create placeholder route files"""

    projects_router = '''from fastapi import APIRouter, HTTPException
from app.api.schemas.project import ProjectCreate, ProjectResponse
from uuid import uuid4

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """Register a new project"""
    # TODO: Implement project creation logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details"""
    # TODO: Implement project retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")
'''
    create_file("app/api/routes/projects.py", projects_router)

    tasks_router = '''from fastapi import APIRouter, HTTPException
from app.api.schemas.task import TaskCreate, TaskResponse, TaskApproval

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new development task"""
    # TODO: Implement task creation logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task details"""
    # TODO: Implement task retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{task_id}/approve")
async def approve_task(task_id: str, approval: TaskApproval):
    """Approve or reject task plan"""
    # TODO: Implement approval logic
    raise HTTPException(status_code=501, detail="Not implemented yet")
'''
    create_file("app/api/routes/tasks.py", tasks_router)

    status_router = '''from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get real-time task status"""
    # TODO: Implement status retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
'''
    create_file("app/api/routes/status.py", status_router)


def create_placeholder_schemas():
    """Create schema files"""

    project_schema = """from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    repository_url: str = Field(..., description="Git repository URL")
    description: Optional[str] = Field(None, description="Project description")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    repository_url: str
    description: Optional[str]
    local_path: str
    main_branch: str
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
"""
    create_file("app/api/schemas/project.py", project_schema)

    task_schema = """from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCreate(BaseModel):
    project_id: UUID
    description: str = Field(..., min_length=10)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)


class TaskApproval(BaseModel):
    approved: bool
    feedback: Optional[str] = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    description: str
    status: TaskStatus
    priority: TaskPriority
    plan_path: Optional[str]
    report_path: Optional[str]
    branch_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
"""
    create_file("app/api/schemas/task.py", task_schema)


def create_gitkeep_files():
    """Create .gitkeep files for empty directories"""
    gitkeep_dirs = [
        "storage/projects",
        "storage/plans",
        "storage/reports",
        "storage/memory",
        "logs",
    ]

    for directory in gitkeep_dirs:
        create_file(f"{directory}/.gitkeep", "")


def main():
    """Main setup function"""
    print("\n" + "=" * 60)
    print("  AI Coding Assistant - Project Setup")
    print("=" * 60 + "\n")

    create_directory_structure()

    print("📝 Creating configuration files...")
    create_init_files()
    create_config_file()
    create_main_file()
    create_requirements()
    create_env_example()
    create_gitignore()
    create_readme()

    print("\n🐳 Creating Docker files...")
    create_docker_files()

    print("\n🛣️  Creating API routes...")
    create_placeholder_routes()

    print("\n📐 Creating schemas...")
    create_placeholder_schemas()

    print("\n📌 Creating .gitkeep files...")
    create_gitkeep_files()

    print("\n" + "=" * 60)
    print("  ✅ Project setup complete!")
    print("=" * 60 + "\n")

    print("📋 Next steps:")
    print("  1. Create virtual environment: python -m venv venv")
    print("  2. Activate it: source venv/bin/activate")
    print("  3. Install dependencies: pip install -r requirements.txt")
    print("  4. Copy .env.example to .env and configure")
    print("  5. Run: uvicorn app.main:app --reload")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
