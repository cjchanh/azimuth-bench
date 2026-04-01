# Comment replies (short, honest)

Use these as templates; adjust tone to the subreddit / thread.

---

**“Why not PyPI?”**

v0.1.0 ships as a repo + `pip install -e .`; PyPI automation isn’t in scope yet (see SOURCE_OF_TRUTH). Local `python -m build` is documented.

---

**“Where’s llama.cpp / vLLM?”**

Not in v0.1.0—stubs/planned only. MLX, OpenAI-compatible HTTP, and Ollama are what’s implemented + tested today.

---

**“Is this a leaderboard for the best model?”**

No universal claim. Rows carry lane, protocol, and comparability flags; compare.json uses explicit projections and blocked pairs. Read the report notes and `compare.json`.

---

**“Is the hosted report running inference?”**

No. The public URL is **static files** on GitHub Pages, generated from **committed** benchmark artifacts in the repo—no live backend.

---

**“Can I merge arbitrary JSON?”**

No—only Azimuth-shaped run directories (token summary + per-row artifacts), with merge metadata and blockers when protocols differ.

---

**“Enterprise / SLA?”**

This is OSS tooling, not a hosted service.
