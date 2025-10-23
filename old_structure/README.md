# Old Structure Files

This folder contains the original Python files before the reorganization.

These files are kept for reference only and are **no longer used** by the application.

## What happened?

The project was reorganized into a proper package structure under `chatbot/`:

- `agent.py` → `chatbot/core/agent.py`
- `states.py` → `chatbot/state/states.py`
- `config.py` → `chatbot/utils/config.py`
- `utils.py` → `chatbot/utils/utils.py`
- `fit_score.py` → `chatbot/utils/fit_score.py`
- `verification.py` → `chatbot/utils/verification.py`
- `retrievers.py` → `chatbot/core/retrievers.py`
- `ingestion.py` → `chatbot/core/ingestion.py`
- `report_generator.py` → `chatbot/utils/report_generator.py`
- `main.py` → Replaced with new `main.py` (formerly `main_new.py`)

## New Structure

All functionality now lives under the `chatbot/` package with proper submodules:

```
chatbot/
├── core/       # Core agent and retrieval logic
├── api/        # FastAPI application
├── prompts/    # Centralized prompts configuration
├── state/      # State management
└── utils/      # Utility functions and helpers
```

## Migration

If you have scripts that import from these old files, update them:

```python
# Old import
from agent import CleoRAGAgent

# New import
from chatbot.core.agent import CleoRAGAgent
```

## Can I delete this folder?

Yes, once you've verified everything works with the new structure, you can safely delete this folder.
