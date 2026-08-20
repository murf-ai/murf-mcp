from murf_mcp.setup_docs_mcp.harnesses import claude_code, claude_desktop, codex, cursor

HARNESSES = (cursor, claude_code, claude_desktop, codex)

BY_ID = {module.ID: module for module in HARNESSES}
