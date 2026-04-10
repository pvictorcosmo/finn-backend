# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZapFinance (Finn) is a personal finance management backend in Portuguese (pt-BR). Users send natural language messages (e.g., "gastei 50 no ifood") which are classified by an LLM-based agent system and routed to specialized handlers that manage expenses, budgets, installments, recurring charges, and 50-30-20 budget goals.

## Commands

```bash
# Start PostgreSQL (port 5433 -> 5432 inside container)
docker compose up -d

# Install dependencies (Python 3.12+, venv recommended)
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

There are no tests or linting configured yet.

## Architecture

### Agent System (LLM-powered intent routing)

The core flow is: **message → orchestrator → coordinator → action → DB**

- `app/agents/orchestrator.py` — Receives user text, calls Groq LLM (llama-3.1-8b for classification) to detect intent, then dispatches to the appropriate coordinator or action.
- `app/agents/coordinators/*.py` — Each coordinator calls the LLM with a specialized prompt to extract structured data (amount, category, description, etc.) from the message. Returns a dict consumed by action functions.
- `app/routers/actions.py` — All database operations. Both the agent system and REST endpoints use these functions. This is the largest file and contains the business logic.

### Dual Interface

The app serves two interfaces from the same action functions:
1. **NLP endpoint** (`POST /message`) — natural language input processed by the agent pipeline
2. **REST API** (`GET/PUT /categories`, `/transactions`, `/installments`, `/recurring`, `/salary`, `/goals`, `/goals/status`) — structured JSON endpoints for a frontend dashboard

### Database

- SQLAlchemy ORM with PostgreSQL (psycopg3 driver)
- Models in `app/core/models.py`, connection in `app/core/db.py`
- Auto-creates tables on startup via `Base.metadata.create_all()` + seed data (`app/core/seed.py`)
- Prisma schema exists (`prisma/schema.prisma`) as reference but the app uses SQLAlchemy at runtime
- Categories have a `goal_group` field (essenciais/desejos/poupanca) linking them to 50-30-20 budget goals

### Scheduled Jobs

APScheduler runs two cron jobs (configured in `app/main.py`):
- Daily summary at 20:00 (America/Sao_Paulo)
- Monthly installment/recurring expense processing on the 1st at 08:00

### Key Patterns

- Currency formatting uses BRL (`R$`) via `format_brl()` in `app/core/utils.py`
- Categories are auto-created on first use (`find_or_create_category`)
- All LLM calls go through `call_llm()` in the orchestrator, using Groq API with JSON response format
- The app uses `pydantic-settings` for config, loaded from `.env`

## Environment Variables

See `.env.example`: `DATABASE_URL`, `GROQ_API_KEY`, `MY_PHONE`, `PORT`
