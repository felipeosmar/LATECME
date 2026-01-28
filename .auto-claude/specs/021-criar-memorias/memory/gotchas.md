# Gotchas & Pitfalls

Things to watch out for in this codebase.

## [2026-01-27 19:07]
Graphiti-memory MCP service fails with API key error when configured with 'ollama' - requires valid OpenAI API key or proper local model configuration

_Context: When attempting to use graphiti-memory add_memory, search_nodes, or search_memory_facts, the service returns error 401 with message about incorrect API key 'ollama'. The service needs proper API key configuration._

## [2026-01-28 12:19]
Graphiti-memory MCP service requires valid OpenAI API key - currently configured with 'ollama' which causes 401 authentication errors. Cannot create memories until service is properly configured.

_Context: Attempted to create 10 LATECME codebase memories as part of subtask-1-1. All graphiti-memory tools (add_memory, search_nodes, search_memory_facts, get_status) fail with error: 'Incorrect API key provided: ollama'. Need to configure OPENAI_API_KEY environment variable for the MCP server._

## [2026-01-28 12:22]
Graphiti-memory MCP service has two issues: 1) add_memory tool requires explicit user permissions to be granted, 2) Even when tools execute, they fail with 401 API key error because service is configured with 'ollama' instead of valid OpenAI API key

_Context: Retry attempt 2 for subtask-1-1 (Create 10 memories). search_nodes executed but returned API key error. add_memory requires permission grant. Service needs proper OPENAI_API_KEY configuration to function._

## [2026-01-28 16:43]
Creating memories requires TWO permissions: 1) Claude tool permission for mcp__graphiti-memory__add_memory (user must grant), and 2) Valid OPENAI_API_KEY in graphiti-memory MCP service (currently 'ollama' causes 401 errors)

_Context: Retry attempt 3 for subtask-1-1 (Create 10 LATECME memories). Tool permission was not granted and API key issue persists. All 10 memory contents are prepared in build-progress.txt ready for creation once blockers resolved._

## [2026-01-28 16:45]
graphiti-memory MCP tools require explicit user permission grant - the permission prompt appears but user must actively approve it before tools can execute

_Context: Task 021 - Creating memories. Multiple retry attempts blocked waiting for user to grant permission for mcp__graphiti-memory__add_memory tool._
