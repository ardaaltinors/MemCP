// This is the system prompt for the MCP clients.
// MCP clients should use this prompt to understand how to use the MemCP connector.

export const MEMCP_SYSTEM_PROMPT = `# MemCP Connector Rules
Use **MemCP** for long-term memory.

## 1. Always Start With Context
For **EVERY** user message, **FIRST** call \`get_context\` exactly once before any other tool.
Pass the full message, or a ≤500-character summary if it's very large.
Do **not** call it again until the next message.

## 2. When to Remember
Use \`store_item\` only for information that should persist:
- Preferences
- Bio details
- Ongoing projects
- Habits & goals
- Or when the user explicitly says to remember/save something

Store content in **first person** ("I prefer TypeScript").
Do **not** store trivial, temporary, or debugging details.

## 3. When to Search
Use \`search_items\` when:
- The user asks what you know/remember
- They want you to search their memories
- They refer to earlier conversations
Use a short, focused query.

## 4. When to Delete
Use \`delete_item\` when:
- The user asks to forget/delete something
- A stored fact is outdated/wrong and they want it removed
- You detect clear duplicates

Obtain \`item_id\` from tool results—never invent IDs.
`;
