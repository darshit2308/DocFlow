# DocFlow

> AI-powered document approval workflow for vendor invoices and purchase requests.

Built for the Google Forward Deployed Engineer Intern 2027 application.

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic v2 |
| AI | Gemini 1.5 Flash (Google AI Studio, free tier) |
| Agents | Google ADK |
| Database | Postgres 16 + pgvector (Supabase free tier) |
| Storage | Supabase Storage |
| Deploy | Render.com / Railway (free tier) |
| Tracing | OpenTelemetry + Jaeger (local) |
| UI | Streamlit |

## Quick Start

```bash
cp .env.example .env   # fill in GOOGLE_API_KEY and SUPABASE_* values
make up                # start Postgres with pgvector
make migrate           # run Alembic migrations
make run               # start the API on :8000
make test              # run unit tests
make eval              # run the golden eval set
```

## Architecture

_Diagram added in Step 18._

## Eval Results

_Populated after full eval run. See `docs/eval/`._

## Cost

This project runs entirely on **free tiers** (Google AI Studio free quota, Supabase free tier, Render free tier).
Estimated cost: **\$0** during development. Vertex AI / Cloud SQL noted as the production upgrade path.
