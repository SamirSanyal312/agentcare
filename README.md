# AgentCare

AgentCare is an agentic AI application for healthcare administration
and care coordination.

The system coordinates non-clinical patient workflows such as:

- patient registration
- administrative intent detection
- department routing
- appointment scheduling
- document coordination
- reminders
- follow-up scheduling
- human escalation

## Safety Boundary

AgentCare is not a diagnosis or treatment system.

The application does not autonomously:

- diagnose medical conditions
- prescribe medication
- recommend medication dosages
- change treatment
- replace clinician judgement

Medical and uncertain requests are escalated for human review.

## Technology

- Python
- FastAPI
- SQLAlchemy
- Alembic
- LangGraph
- LangChain
- Groq
- Qwen
- SQLite for local development
- PostgreSQL-compatible architecture

## Development

Create a virtual environment:

```bash
python -m venv .venv

Install dependencies:

pip install -r requirements.txt

Create the local configuration:

cp .env.example .env

Run the application:

uvicorn app.main:app --reload
Status

AgentCare is currently under active development for the
AgentCare Build Challenge 2026.

Only synthetic/anonymized patient data is used.


We'll replace this with a much stronger README later.

---

# 17. Verify secrets before committing

Run:

```powershell
git status

Make sure .env is not there.

Then:

git check-ignore .env

Expected:

.env

Excellent.

Also:

git status

should show:

.env.example
.gitignore
README.md
requirements.txt
app/
scripts/
storage/
tests/