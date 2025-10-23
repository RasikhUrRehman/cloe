# Utility Scripts

This folder contains utility scripts for setup, testing, and demonstrations.

## Available Scripts

### Setup & Configuration

- **`setup_knowledge_base.py`** - Set up and initialize the knowledge base with sample documents
- **`create_sample_docs.py`** - Generate sample documents for testing
- **`quickstart.py`** - Quick setup wizard for first-time users

### Testing & Demos

- **`demo_conversation.py`** - Run a demonstration conversation with the chatbot
- **`test_system.py`** - System integration tests
- **`test_parse.py`** - Test document parsing functionality

## Usage

Run scripts from the **project root directory**:

```bash
# Setup knowledge base
python scripts/setup_knowledge_base.py

# Run demo conversation
python scripts/demo_conversation.py

# Create sample documents
python scripts/create_sample_docs.py
```

## Note on Imports

These scripts may need to be updated to use the new package structure. If you encounter import errors, update the imports:

```python
# Add to the top of the script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Then use new imports
from chatbot.core.agent import CleoRAGAgent
from chatbot.utils.config import settings
```

## Creating New Scripts

When creating new utility scripts:

1. Place them in this `scripts/` folder
2. Add proper imports for the `chatbot` package
3. Add a docstring explaining what the script does
4. Update this README with the script description
