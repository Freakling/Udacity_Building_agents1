# AI Transparency

**Project:** UdaPlay
**Author:** Vikingur Saemundsson
**Date:** 2026-09-10

---

## AI assistance scope

AI coding assistants were used during development of this capstone submission.

### Files with AI involvement

| File | What AI contributed |
|------|---------------------|
| `lib/llm_claude.py` | Full generation: Anthropic API client, OpenAI-to-Anthropic message format translation |
| `lib/agents.py` | Added `llm_class` parameter for pluggable backends |
| `lib/vector_db.py` | Added `use_local_embeddings` flag, `api_base` proxy support |
| `lib/loaders.py` | Moved top-level `import pdfplumber` to lazy import |
| `test_agent.py` | Backend auto-detection logic, `argparse` CLI wiring |
| `init.py` | SQLite3 shim ordering, dependency smoke-test structure |
| `games.json` | Dataset expansion from 25 to 210 records |
| `README.md`, `AI_TRANSPARENCY.md` | Structure and content |

### Human-authored

- Course framework (`lib/`: `Agent`, `StateMachine`, `@tool`, `ShortTermMemory`, `RAG`, `VectorStoreManager`, `LLM`)
- Udacity notebook scaffolding (`Udaplay_01_solution_project.ipynb`, `Udaplay_02_solution_project.ipynb`)
- Architecture decisions: RAG pipeline design, tool orchestration, backend selection strategy
- Debugging and validation of all AI-generated code
- Config and secrets management structure

---

## What AI was not used for

- Understanding course concepts (RAG, tool-calling, vector databases)
- System architecture design
- Evaluating output correctness

---

## Limitations

- `games.json` data is sourced from public rankings and general knowledge. Release dates, developer/publisher names, and platform lists are best-effort and may contain inaccuracies.
- All AI-generated code was reviewed and tested before submission.
- Runtime outputs from the agent (LLM + Tavily) are non-deterministic and may contain errors.

---

## Standards

- EU AI Act Art. 50: disclosure of AI-generated content
- Montreal Declaration for Responsible AI: transparency principle
- IEEE 7000-2021: ethically aligned design
- Udacity Academic Integrity Policy: AI tools permitted; student must understand and explain all submitted work
