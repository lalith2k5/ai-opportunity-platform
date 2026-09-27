# AI Opportunity Discovery & Innovation Intelligence Platform

An AI-powered decision support system that discovers startup and research opportunities by analyzing data from GitHub, arXiv, and News RSS feeds.

## Quick Start

Start both servers (opens new Terminal tabs):

    bash ~/ai-opportunity-platform/start-all.sh

Then open:
- Frontend:            http://localhost:5173
- Backend API docs:    http://localhost:8000/docs
- Health check:        http://localhost:8000/api/health

## Features

- Multi-source data collection (GitHub, arXiv, News RSS)
- NLP pipeline: cleaning, keywords, NER, sentiment
- Knowledge graph of entities and relationships
- Problem discovery via TF-IDF clustering
- Research gap detection (papers vs. real-world problems)
- Innovation trend monitoring
- Explainable multi-factor opportunity scoring
- RAG-based AI chat (Gemini 3.8 Flash)
- Interactive React dashboard + CSV reports

## Architecture

- Frontend:  React 18, TypeScript, Tailwind CSS, Vite, Recharts
- Backend:   FastAPI, Python 3.12, SQLAlchemy, Uvicorn
- Databases: PostgreSQL 17 (structured), ChromaDB (vectors)
- AI:        Sentence Transformers, Google Gemini 3.8 Flash
- Agents:    10 specialized AI agents

## AI Agents

1.  Orchestrator            - coordinates pipeline
2.  Data Collection         - GitHub, arXiv, News, Reddit
3.  NLP                     - text processing
4.  Knowledge Graph         - entity relationships
5.  Problem Discovery       - recurring problem clusters
6.  Research Gap            - missing research areas
7.  Innovation Monitor      - emerging trends
8.  Opportunity Intelligence - multi-factor scoring
9.  Explainable AI          - reasoning generation
10. AI Chat                 - RAG-based Q&A

## API Endpoints

| Method | Endpoint              | Purpose                |
|--------|-----------------------|------------------------|
| GET    | /api/health           | Health + vector count  |
| POST   | /api/pipeline/run     | Run full pipeline      |
| GET    | /api/opportunities    | Ranked opportunities   |
| GET    | /api/problems         | Problem clusters       |
| GET    | /api/research-gaps    | Research gaps          |
| GET    | /api/trends           | Emerging trends        |
| POST   | /api/chat             | AI chat                |
| POST   | /api/search           | Semantic search        |

## Opportunity Score Formula

    Score = 0.25*Demand + 0.20*ResearchGap + 0.15*Trend
          + 0.10*(1-Competition) + 0.15*Feasibility
          + 0.10*MarketReadiness + 0.05*Confidence

## Configuration

Edit backend/.env to add:
- GEMINI_API_KEY                      (required for AI chat)
- GITHUB_TOKEN                        (optional, higher rate limit)
- REDDIT_CLIENT_ID + _SECRET          (optional, Reddit data)

## Project Structure

    ai-opportunity-platform/
    |-- backend/
    |   |-- app/
    |   |   |-- agents/       (10 AI agents)
    |   |   |-- services/     (external APIs + embeddings + LLM)
    |   |   |-- api/          (routes)
    |   |   |-- models.py
    |   |   |-- schemas.py
    |   |   |-- database.py
    |   |   |-- config.py
    |   |   \-- main.py
    |   \-- .env
    |-- frontend/
    |   \-- src/
    |       |-- pages/
    |       |-- components/
    |       \-- services/
    |-- start-all.sh
    |-- start-backend.sh
    \-- start-frontend.sh
