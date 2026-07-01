# Aegis Assessment — AI-Powered Technical Interview Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![React](https://img.shields.io/badge/React-18-cyan)
![Pinecone](https://img.shields.io/badge/Pinecone-v9-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

I built this because every AI interview tool I tried asked the same generic questions regardless of who was being interviewed. This one actually reads your resume, finds your skills, pulls relevant content from real ML textbooks using RAG, and generates questions tailored to you specifically.

The core idea: upload a PDF resume, pick a role, and get 5 questions that are grounded in actual textbook knowledge — not a static question bank.

---

## Demo

▶️ [Watch Full Demo](your-demo-video-link-here)

---

## How it works under the hood

```
┌─────────────────────────────────────────────────────────────┐
│                        CANDIDATE                            │
└───────────────────────┬─────────────────────────────────────┘
                        │ Upload Resume + Select Role
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   REACT FRONTEND                            │
│  Landing → Upload → Interview → Summary                     │
│  TanStack Query │ shadcn/ui │ Tailwind CSS                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP REST API
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                             │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Routes    │  │   Services   │  │    Database      │   │
│  │             │  │              │  │                  │   │
│  │ session.py  │  │resume_parser │  │   SQLite via     │   │
│  │interview.py │  │rag_service   │  │   aiosqlite      │   │
│  │             │  │question_gen  │  │                  │   │
│  │             │  │session_mgr   │  │ sessions         │   │
│  └─────────────┘  └──────┬───────┘  │ questions        │   │
│                          │          │ answers          │   │
└──────────────────────────┼──────────┴──────────────────┴───┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌─────────────────────┐    ┌────────────────────────┐
│   PINECONE (RAG)    │    │   OPENROUTER API        │
│                     │    │                         │
│ 1,214 vectors from  │    │ Embeddings:             │
│ 4 ML textbooks:     │    │ text-embedding-3-small  │
│ • Tom Mitchell      │    │                         │
│ • Bishop PRML       │    │ Generation:             │
│ • Burkov 100-page   │    │ claude-3-haiku          │
│ • ML Beginners      │    │                         │
└─────────────────────┘    └────────────────────────┘
```

---

## Full flow, step by step

```
1. RESUME UPLOAD
   Candidate uploads PDF resume + selects role

2. RESUME PARSING (PyMuPDF)
   Extract full text → detect candidate name →
   match 60+ skill keywords → return skills list

3. CONTEXT CONSTRUCTION
   Build query: "Technical interview about: {skills} for {role}"

4. RAG RETRIEVAL (Pinecone)
   Embed query → vector search → top 5 textbook chunks

5. QUESTION GENERATION (Claude-3-Haiku via OpenRouter)
   Prompt = skills + role + retrieved chunks →
   5 personalized non-generic questions with topics

6. INTERACTIVE INTERVIEW
   One question at a time → answer stored → next question

7. SESSION STORAGE (SQLite)
   Every question and answer persisted with session metadata

8. SUMMARY GENERATION
   Join all QA pairs → calculate stats → display analysis
```

---

## RAG design decisions (and the reasoning behind them)

I made a few non-obvious calls here that are worth explaining.

### Chunking
- **Chunk size:** 500 words with 50-word overlap
- Went with 500 because smaller chunks (100-200 words) lose enough context that the retrieved content feels disconnected. Larger chunks (1000+) dilute the semantic signal. 500 felt like the right middle ground after testing.
- The 50-word overlap exists specifically to avoid splitting concepts that span a chunk boundary — things like a theorem definition that bleeds into its explanation.

### Embedding model
- **Model:** `openai/text-embedding-3-small` via OpenRouter
- 1536-dimensional vectors, good semantic understanding of technical content, and cheap enough that I don't have to worry about costs during testing. Beats ada-002 on technical retrieval without the price jump of the large variant.

### Why Pinecone over FAISS or ChromaDB
- No local storage or RAM required — the index lives remotely and persists across deployments without re-ingestion
- Sub-100ms query latency even as the index grows
- Metadata filtering opens up future features like role-specific retrieval
- Cosine similarity, 1536 dimensions

### Knowledge base
I picked these four books specifically because they cover different parts of the ML space without too much overlap:

| Book | Coverage |
|---|---|
| Tom Mitchell — Machine Learning | Classic foundations, decision trees, neural nets |
| Bishop — PRML | Probabilistic models, Bayesian methods |
| Burkov — 100-Page ML | Concise practical coverage, great for targeted Q gen |
| ML Absolute Beginners | Accessible concept definitions, fills vocabulary gaps |

### Prompt design for question generation
- System prompt forces textbook-grounded questions only
- Explicitly bans generic openers like "what is machine learning"
- Forces JSON output for reliable parsing
- Skills + role + retrieved chunks are all injected, which is what actually makes the questions different per candidate
- Claude-3-Haiku was the right call: fast (< 5s), cheap, and it follows structured JSON instructions reliably

### How the resume actually influences the output
Three ways, not one:
1. **Topic selection** — detected skills become the Pinecone query
2. **Prompt injection** — skill list is passed directly into the generation prompt
3. **Retrieval shaping** — the embedding is built from actual resume content, so different resumes pull different textbook chunks

---

## Project structure

```
├── backend/
│   ├── main.py                  # FastAPI app, CORS, lifespan
│   ├── database/
│   │   └── db.py                # SQLite init, connection manager
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routes/
│   │   ├── session.py           # POST /session/start, GET /session/:id
│   │   └── interview.py         # POST /answer, GET /summary/:id
│   └── services/
│       ├── resume_parser.py     # PyMuPDF text extraction + skill matching
│       ├── rag_service.py       # Pinecone query + OpenRouter embeddings
│       ├── question_generator.py # Claude prompt + JSON parsing
│       └── session_manager.py   # SQLite CRUD operations
│
├── artifacts/interview-app/
│   └── src/
│       ├── pages/
│       │   ├── Landing.tsx      # Hero page with features
│       │   ├── upload.tsx       # Resume upload + role selection
│       │   ├── interview.tsx    # Q&A interface with progress
│       │   └── summary.tsx      # Session review + stats
│       └── components/
│           └── AnimatedBackground.tsx
│
└── lib/
    ├── api-spec/openapi.yaml    # OpenAPI contract (source of truth)
    └── api-client-react/        # Auto-generated TanStack Query hooks
```

---

## Setup

### What you need
- Python 3.11+
- Node.js 18+
- pnpm (`npm install -g pnpm`)
- Pinecone account (free tier works fine)
- OpenRouter account (they give free credits to start)

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/aegis-assessment.git
cd aegis-assessment
```

### 2. Set environment variables
Create a `.env` file in the root:
```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_HOST=your_pinecone_index_host_url
PINECONE_INDEX=interview-kb
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 3. Install backend dependencies
```bash
pip install fastapi "uvicorn[standard]" python-multipart aiosqlite pymupdf requests pinecone pydantic
```

### 4. Install frontend dependencies
```bash
pnpm install
```

### 5. Run the knowledge base ingestion (one time only)
```bash
# Create a ./books/ directory and place your ML textbook PDFs inside it
mkdir books
# cp your-textbooks/*.pdf books/

# Optional: dry run to verify chunk count without uploading anything
python backend/ingest.py --dry-run

# Full ingestion — uploads ~1200 vectors to Pinecone (takes 30-60 minutes)
python backend/ingest.py
```

### 6. Start the backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

### 7. Start the frontend
```bash
pnpm --filter @workspace/interview-app run dev
```

### 8. Open the app
```
http://localhost:5173
```

---

## API reference

### POST `/api/session/start`
Starts a new interview session. Expects multipart form data.

| Field | Type | Description |
|---|---|---|
| resume | File | PDF resume |
| role | string | "AI/ML Engineer" or "Backend Engineer" |

```json
{
  "session_id": "uuid",
  "candidate_name": "Jane Smith",
  "role": "AI/ML Engineer",
  "extracted_skills": ["Python", "PyTorch", "NLP"],
  "questions": [
    { "id": 1, "question": "...", "topic": "Neural Networks" }
  ],
  "total_questions": 5
}
```

### POST `/api/answer`
Submit an answer to the current question.

```json
{
  "session_id": "uuid",
  "question_id": 1,
  "answer": "My answer..."
}
```

### GET `/api/summary/{session_id}`
Returns the full session with all Q&A pairs, extracted skills, and topics covered.

### GET `/api/healthz`
Health check.

---

## Engineering decisions at a glance

| Decision | Choice | Why |
|---|---|---|
| Backend | FastAPI | Async, auto OpenAPI docs, Pydantic validation |
| Database | SQLite + aiosqlite | Zero infra, async, more than enough for session data |
| Vector DB | Pinecone Serverless | Persistent, no local storage, production-grade latency |
| LLM | Claude-3-Haiku | Fast, cheap, great at following JSON instructions |
| Embeddings | text-embedding-3-small | Best quality-per-dollar for technical content |
| Frontend state | TanStack Query | Server state caching, loading/error states built in |
| API contract | OpenAPI + Orval codegen | Type-safe auto-generated hooks, one source of truth |
| PDF parsing | PyMuPDF | Fastest Python PDF library, handles messy layouts well |

---

## What makes this different from other interview tools

Most AI interview tools use a static question bank and maybe do a light keyword match against your resume. This one:

- Generates every question fresh using actual retrieved textbook content
- Two different resumes genuinely produce two completely different question sets
- Questions are grounded in real ML concepts from Bishop, Mitchell, and Burkov — not hallucinated generics
- The entire API contract is OpenAPI-first with auto-generated type-safe frontend hooks, which is the same pattern you'd use in production

---

## Built with

FastAPI · Pinecone · OpenRouter · Claude AI · React · TanStack Query · shadcn/ui · PyMuPDF · SQLite
