# UdaPlay — AI Research Agent for Gaming Analytics

A Retrieval-Augmented Generation (RAG) agent that answers natural language questions about video games. Built as a Udacity capstone project for the *Building Agents* course.

---

## How It Works

### Where does it actually run?

| Component | Runs where? |
|-----------|-------------|
| Your Python code | **Locally** (or in Udacity's Jupyter workspace) |
| LLM inference (`gpt-4o-mini`) | **Remote** — OpenAI API (cloud) |
| Text embeddings | **Remote** — OpenAI API (cloud) |
| ChromaDB vector store | **Local** — in-memory, rebuilt each session |
| Tavily web search | **Remote** — Tavily API (cloud) |

There is **no local AI model**. The Python code orchestrates everything, but the actual intelligence comes from OpenAI's API. When used in the Udacity workspace, API calls are routed through a Vocareum proxy (`https://openai.vocareum.com/v1`) using the course-provided API key.

---

### Architecture Overview

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Agent (lib/agents.py — StateMachine)                   │
│                                                         │
│  message_prep ──► llm_processor ──► tool_executor       │
│                        ▲                  │             │
│                        └──────────────────┘             │
│                   (loop until no more tool calls)       │
└─────────────────────────────────────────────────────────┘
    │
    ├── Tool 1: retrieve_game
    │       └── RAG pipeline (lib/rag.py)
    │               ├── retrieve  →  ChromaDB vector search
    │               ├── augment   →  build prompt with context
    │               └── generate  →  OpenAI gpt-4o-mini
    │
    ├── Tool 2: evaluate_retrieval
    │       └── Direct LLM call → returns JSON confidence score
    │
    └── Tool 3: game_web_search
            └── Tavily API → live web results
```

### Decision Flow Per Query

```
1. retrieve_game(query)
        ↓
2. evaluate_retrieval(query, result)
   → confidence_score ≥ 0.7?  ──YES──► compose final answer
                               ──NO───► game_web_search(query)
                                              ↓
                                       compose final answer
                                       (citing [Internal DB] or [Web Search])
```

---

### The `lib/` Framework

The course provides a small framework (in `lib/`) that mirrors patterns used in production agent systems:

| Class | What it does |
|-------|-------------|
| `Agent` | Wires together a `StateMachine` + `ShortTermMemory`. Drives the LLM → tool → LLM loop. |
| `StateMachine` / `Step` / `Run` | Generic state machine. Each `Step` is a function that transforms state. `Run` captures a full execution snapshot. |
| `LLM` | Thin wrapper around the OpenAI chat API with tool-calling support. |
| `RAG` | Three-step state machine: retrieve → augment → generate. |
| `VectorStoreManager` | Creates and manages ChromaDB collections with OpenAI embeddings. |
| `CorpusLoaderService` | Loads documents (PDF or JSON) into a vector store. |
| `@tool` decorator | Reads a function's type hints and docstring to auto-generate an OpenAI function-calling schema. No manual JSON needed. |
| `ShortTermMemory` | Stores `Run` objects per `session_id`, enabling multi-turn conversations. |

---

## Project Structure

```
udaplay/
├── Udaplay_01_solution_project.ipynb   # Part 1: RAG pipeline demo
├── Udaplay_02_solution_project.ipynb   # Part 2: Full agent with tools
├── test_agent.py                       # Standalone smoke-test script
├── games.json                          # 25 curated game records (2013–2023)
├── config.env.template                 # Copy → config.env, fill in keys
├── requirements.txt
└── lib/                                # Course framework (do not modify)
    ├── agents.py
    ├── rag.py
    ├── llm.py
    ├── vector_db.py      ← extended: api_base support + load_json()
    ├── loaders.py        ← extended: JSONGameLoader
    ├── state_machine.py
    ├── tooling.py
    ├── memory.py
    ├── messages.py
    ├── documents.py
    ├── parsers.py
    └── __init__.py
```

### Dataset — `games.json`

25 game records spanning 2013–2023:

| Genre | Examples |
|-------|---------|
| Open World / RPG | GTA V, The Witcher 3, Elden Ring, Cyberpunk 2077, Starfield, AC Valhalla |
| Action/Adventure | God of War Ragnarok, Spider-Man Miles Morales, Zelda BotW, Hogwarts Legacy |
| Sports | FIFA 21 |
| Platformer/Classic | Pokemon Red, Minecraft, Animal Crossing |
| Shooter | Halo Infinite, Doom Eternal, CoD: MW II, Fortnite |
| RPG | Final Fantasy XVI, Diablo IV, Baldur's Gate 3 |
| Survival/Horror | The Last of Us Part I |
| Multiplayer | Among Us, Overwatch 2 |

---

## Setup

### 1. Install Python

If Python is not installed:

```powershell
winget install Python.Python.3.12
```

Close and reopen PowerShell after installing.

### 2. Install dependencies

```powershell
cd udaplay
pip install -r requirements.txt
```

### 3. Configure API keys

Copy the template and fill in your keys:

```powershell
copy config.env.template config.env
```

Edit `config.env`:

```
OPENAI_API_KEY=your-key-here
TAVILY_API_KEY=your-key-here
OPENAI_BASE_URL=https://openai.vocareum.com/v1
```

> **Udacity workspace**: use the API key from your workspace environment and keep `OPENAI_BASE_URL` as-is. The proxy routes your calls through the course account.  
> **Running locally with your own OpenAI account**: set `OPENAI_BASE_URL=https://api.openai.com/v1` (or remove it entirely).

Get a free Tavily API key at [tavily.com](https://tavily.com) — 1000 searches/month free.

---

## Running the Agent

### Option A — Smoke-test script

```powershell
cd udaplay
python test_agent.py
```

This runs the query:
> *"What is the best open world game ever made? Based on what makes it great, give me practical tips on how to build a similar game and monetize it successfully."*

### Option B — Jupyter notebooks (recommended for Udacity submission)

Open `Udaplay_01_solution_project.ipynb` first, then `Udaplay_02_solution_project.ipynb`. Run all cells top to bottom.

### Option C — Interactive cell in Notebook 2

In `Udaplay_02_solution_project.ipynb`, find the last cell and change the `question` variable:

```python
question = "Which games in the database were released on Nintendo Switch?"
run = udaplay.invoke(query=question, session_id="interactive")
print(run.get_final_state()["messages"][-1].content)
```

---

## Multi-Turn Sessions

The agent remembers conversation history within a `session_id`. Pronouns and references from earlier turns resolve correctly:

```python
# Turn 1
run_a = udaplay.invoke(
    query="What games has CD Projekt Red developed?",
    session_id="my_session"
)

# Turn 2 — "their" resolves from session history
run_b = udaplay.invoke(
    query="Which of their games has the most DLC?",
    session_id="my_session"
)
```

---

## Example Queries

| Query | Expected path |
|-------|--------------|
| "Who developed FIFA 21?" | retrieve → evaluate → answer (Internal DB) |
| "When was God of War Ragnarok released?" | retrieve → evaluate → answer (Internal DB) |
| "What is Rockstar Games working on now?" | retrieve → evaluate → web search → answer |
| "Tell me about Metaphor: ReFantazio" | retrieve → evaluate → web search → answer |
| "Best open world RPGs and how to build one?" | retrieve → evaluate → web search → answer |
