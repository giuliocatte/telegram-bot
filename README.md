# Telegram AI Agent

AI agent with a Telegram Bot as interface.
Uses gemini flash 2.5 as llm, and right now it has just a toolset of D&D 5e knowledge, via a MCP server (the project mounted as a submodule).

## Setup
The telegram bot has to be created as explained in the bot_creation.py file.
The server then should be activated running:

```
python main.py
```

## TODO
- Sostituire le print con dei log sensati
- Capire come mai c'è un fiume di warning che arrivano dall'mcp
- Gestire I/O multimodale