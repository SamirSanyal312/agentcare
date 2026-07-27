# AgentCare

AgentCare is an agentic AI application for healthcare administration and care coordination.

It coordinates non-clinical patient workflows including:

- patient registration
- administrative intent detection
- department routing
- appointment scheduling and rescheduling
- document coordination
- reminders
- follow-up scheduling
- human escalation

## Healthcare Safety Boundary

AgentCare is not a diagnosis or treatment system.

The application does not autonomously:

- diagnose medical conditions
- prescribe medication
- recommend medication dosages
- change treatment
- interpret medical findings as clinical advice
- replace clinician judgment

Medical, emergency, uncertain, or sensitive requests are escalated for human review.

## Planned Agent Architecture

AgentCare will use multiple specialized agents coordinated through a persistent workflow:

- Coordinator Agent
- Safety Agent
- Department Routing Agent
- Appointment Agent
- Document Agent
- Follow-up Agent

Agents interact with real application tools backed by persistent SQL data.

## Technology Stack

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

### Agentic AI

- LangGraph
- LangChain
- Groq
- Qwen

### Database

- SQLite for local development
- PostgreSQL-compatible architecture

### Frontend

- Jinja2
- HTMX
- Bootstrap

## LLM

AgentCare currently uses Groq with:

```text
qwen/qwen3.6-27b
```

The LLM provider is configured through environment variables and is not hardcoded into individual agents.

## Development Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Add the required local credentials to `.env`.

Never commit `.env`.

Run the FastAPI application:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Data and Privacy

AgentCare uses only synthetic or anonymized sample data.

Real patient data, private credentials, production tokens, and API secrets must never be committed to this repository.

## Project Status

AgentCare is under active development for the AgentCare Build Challenge 2026.