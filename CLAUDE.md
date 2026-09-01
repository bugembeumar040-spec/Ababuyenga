# Ababuyenga

## Repo map
- `credit-card-prompt-pack.txt` — prompt pack, plain text.
- `youtube/` — YouTube content work.

No build, no tests, no package manager. Don't look for them.

## Working rules (token/credit efficiency)

The owner has asked for low token/credit usage. Treat that as standing policy.

1. **Trust this file.** It is the repo survey. Skip discovery unless a task
   touches something not described here.
2. **Read narrowly.** `sed -n`/`head` a range, `grep` for the symbol. Never
   `cat` a whole large file to "get oriented".
3. **Batch shell work.** One Bash call chaining commands beats five calls.
4. **No subagents, no plan mode, no web search** unless explicitly asked —
   each one re-pays the full context cost from cold.
5. **Don't call MCP tools speculatively.** The Adobe / ElevenLabs / vidIQ /
   Nexlev / HF servers here return large payloads; only reach for one when
   the task names that capability.
6. **Don't re-read a file you just wrote.** The edit tools already error on
   failure.
7. **Answer short.** No preambles, no summaries of what you're about to do,
   no recaps of unchanged work.

## Git
- Work on the branch given in the task; push with `git push -u origin <branch>`.
- Never open a PR unless asked.
