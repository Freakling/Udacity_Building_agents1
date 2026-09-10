# UdaPlay

Udacity *Building AI Agents* capstone. RAG pipeline and stateful tool-calling agent over a 210-game dataset.

## Architecture

```
query -> retrieve_game (ChromaDB) -> evaluate_retrieval (confidence score)
             |- score >= 0.7: answer [Internal DB]
             +- score < 0.7: game_web_search (Tavily) -> answer [Web Search]
```

Session memory keyed by `session_id` resolves follow-up references across turns.

## Stack

| Component | Implementation |
|-----------|---------------|
| LLM | `gpt-4o-mini` via Vocareum proxy; `claude-haiku-4-5` as fallback |
| Embeddings | OpenAI `text-embedding-ada-002`; local `onnxruntime` MiniLM in Claude mode |
| Vector store | ChromaDB in-memory |
| Web search | Tavily API |
| Framework | `lib/`: `Agent`, `StateMachine`, `@tool`, `ShortTermMemory` |

## Quickstart

```bash
git clone https://github.com/Freakling/Udacity_Building_agents1.git
cd Udacity_Building_agents1/udaplay
python init.py
cp config.env.template config.env  # fill OPENAI_API_KEY + TAVILY_API_KEY
```

Run `Udaplay_01_solution_project.ipynb` then `Udaplay_02_solution_project.ipynb`.

## CLI

```bash
python test_agent.py
python test_agent.py "Who developed Elden Ring?"
python test_agent.py '{"query": "What has CD Projekt Red made?", "session_id": "cdpr"}'
python test_agent.py '{"query": "Which has the most DLC?", "session_id": "cdpr"}'
```

## Project layout

```
udaplay/
|- Udaplay_01_solution_project.ipynb
|- Udaplay_02_solution_project.ipynb
|- test_agent.py
|- init.py
|- games.json               # 210 game records, 1978-2024
|- config.env.template
|- requirements.txt
+- lib/                     # course framework; loaders.py + vector_db.py extended
```
