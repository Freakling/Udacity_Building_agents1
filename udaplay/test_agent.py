"""
UdaPlay smoke-test — auto-selects backend based on available API keys.

  ANTHROPIC_API_KEY set  →  uses Claude (Anthropic) + local embeddings (free, no OpenAI key needed)
  OPENAI_API_KEY set     →  uses GPT-4o-mini + OpenAI embeddings (Vocareum proxy or direct)

Run from the udaplay/ directory:
    python test_agent.py

Keys are loaded from config.env.
"""

import importlib.util
import sys
import os
import json

# Udacity workspace sqlite3 shim
if importlib.util.find_spec("pysqlite3") is not None:
    import pysqlite3
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

from dotenv import load_dotenv
load_dotenv("config.env")

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY  = os.getenv("TAVILY_API_KEY")

assert TAVILY_API_KEY, "Set TAVILY_API_KEY in config.env"
assert ANTHROPIC_API_KEY or OPENAI_API_KEY, (
    "Set either ANTHROPIC_API_KEY (Claude) or OPENAI_API_KEY (OpenAI) in config.env"
)

USE_CLAUDE = bool(ANTHROPIC_API_KEY) and not bool(OPENAI_API_KEY)

if USE_CLAUDE:
    print("Backend: Claude (Anthropic) + local embeddings")
    from lib.llm_claude import ClaudeLLM as LLMClass
    LLM_MODEL = "claude-haiku-4-5-20251001"
else:
    print(f"Backend: OpenAI ({OPENAI_BASE_URL})")
    from lib.llm import LLM as LLMClass
    LLM_MODEL = "gpt-4o-mini"

from lib.agents import Agent
from lib.llm import LLM
from lib.state_machine import Run
from lib.messages import SystemMessage, UserMessage
from lib.tooling import tool
from lib.vector_db import VectorStoreManager, CorpusLoaderService
from lib.rag import RAG
from tavily import TavilyClient

# ── Vector store + RAG ──────────────────────────────────────────────────────
print("Setting up vector store...")

if USE_CLAUDE:
    db = VectorStoreManager(use_local_embeddings=True)
else:
    db = VectorStoreManager(OPENAI_API_KEY, api_base=OPENAI_BASE_URL)

loader_service = CorpusLoaderService(db)
games_store = loader_service.load_json(store_name="games", json_path="games.json")

rag_llm = LLMClass(model=LLM_MODEL, temperature=0.3)
games_rag = RAG(llm=rag_llm, vector_store=games_store)

# ── Tools ────────────────────────────────────────────────────────────────────
@tool
def retrieve_game(query: str) -> str:
    """
    Search the internal game database for video game information.
    ALWAYS call this tool first before any other source.

    Source: Internal ChromaDB — 25 curated game records (2013–2023).

    args:
        query (str): Natural-language search query about a game, developer,
                     platform, genre, or release date.
    """
    result: Run = games_rag.invoke(query)
    final_state = result.get_final_state()
    docs = final_state.get("documents", [])
    answer = final_state.get("answer", "No results found.")
    context = "\n\n".join(docs[:3]) if docs else "(no documents retrieved)"
    return f"[Retrieved Documents]\n{context}\n\n[Generated Answer]\n{answer}"


_eval_llm = LLMClass(model=LLM_MODEL, temperature=0.0)


@tool
def evaluate_retrieval(query: str, retrieved_info: str) -> str:
    """
    Evaluate whether the retrieved game information sufficiently answers
    the user's query. Returns a JSON confidence assessment.

    Call this IMMEDIATELY after retrieve_game. If confidence_score < 0.7
    or is_sufficient=false, call game_web_search next.

    args:
        query (str): The original user question.
        retrieved_info (str): The full output from retrieve_game.
    """
    prompt = f"""You are a quality evaluator for a gaming information retrieval system.

User query: {query}

Retrieved information:
{retrieved_info}

Assess whether the retrieved information sufficiently answers the query.
Respond ONLY with this JSON:
{{
  "confidence_score": <float 0.0-1.0>,
  "is_sufficient": <true if score >= 0.7, else false>,
  "reasoning": "<one sentence>",
  "missing_information": ["<item>"] or null
}}"""

    response = _eval_llm.invoke([
        SystemMessage(content="Respond only with valid JSON."),
        UserMessage(content=prompt),
    ])
    return response.content


_tavily = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def game_web_search(query: str) -> str:
    """
    Search the web for video game information using the Tavily API.
    Use this ONLY when evaluate_retrieval returns confidence_score < 0.7
    or is_sufficient=false.

    Source: Live web search (Tavily), up-to-date as of today.

    args:
        query (str): Search query. Include the game title or developer name.
    """
    try:
        results = _tavily.search(
            query=f"{query} video game",
            search_depth="advanced",
            max_results=5,
        )
        parts = []
        for r in results.get("results", []):
            parts.append(
                f"Source: {r.get('url', 'N/A')}\n"
                f"Title: {r.get('title', 'N/A')}\n"
                f"Content: {r.get('content', '')}"
            )
        return "\n\n---\n\n".join(parts) if parts else "No web results found."
    except Exception as exc:
        return f"Web search failed: {exc}"


# ── Agent ────────────────────────────────────────────────────────────────────
udaplay = Agent(
    model_name=LLM_MODEL,
    temperature=0.3,
    tools=[retrieve_game, evaluate_retrieval, game_web_search],
    llm_class=LLMClass,
    instructions=(
        "You are UdaPlay, an expert AI research agent specializing in video game information. "
        "Follow this exact workflow for every query:\n"
        "1. ALWAYS call retrieve_game first to search the internal database.\n"
        "2. ALWAYS call evaluate_retrieval immediately after to assess the result.\n"
        "3. If confidence_score < 0.7 or is_sufficient=false, call game_web_search.\n"
        "4. After gathering information, provide a comprehensive, well-cited answer. "
        "Label each fact with its source: [Internal DB] or [Web Search].\n"
        "Use session context to resolve follow-up questions."
    ),
)

# ── Parse CLI argument ────────────────────────────────────────────────────────
import argparse

_DEFAULT_QUERY = (
    "What is the best open world game ever made? "
    "Based on what makes it great, give me practical tips on how to build "
    "a similar game and monetize it successfully."
)

parser = argparse.ArgumentParser(description="Run the UdaPlay agent with a query.")
parser.add_argument(
    "input",
    nargs="?",
    default=None,
    help='Free text query or JSON object: \'{"query": "...", "session_id": "..."}\'',
)
args = parser.parse_args()

QUERY = _DEFAULT_QUERY
SESSION = "open_world_research"

if args.input:
    try:
        parsed = json.loads(args.input)
        QUERY = parsed.get("query", _DEFAULT_QUERY)
        SESSION = parsed.get("session_id", "cli_session")
    except (json.JSONDecodeError, ValueError):
        QUERY = args.input
        SESSION = "cli_session"

print(f"\n{'='*70}")
print(f"Query: {QUERY}")
print("=" * 70)

run = udaplay.invoke(query=QUERY, session_id=SESSION)
messages = run.get_final_state()["messages"]

print("\n=== Tool calls made ===")
for m in messages:
    tc = getattr(m, "tool_calls", None)
    if tc:
        for c in tc:
            print(f"  → {c.function.name}()")

print("\n=== Final Answer ===")
print(messages[-1].content)
