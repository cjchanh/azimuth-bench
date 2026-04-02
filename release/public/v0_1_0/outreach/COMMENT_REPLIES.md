# Comment replies (short, honest)

Use these as templates; adjust tone to the subreddit / thread.

---

**“Why not PyPI?”**

v0.1.0 ships as a repo + `pip install -e .`; PyPI automation isn't in scope yet. Local `python -m build` is documented and works, but I didn't want to pretend the publish pipeline was done when it wasn't.

---

**“Where’s llama.cpp / vLLM?”**

Not in v0.1.0. They're still planned. I kept this release to what is actually implemented and tested today: MLX, OpenAI-compatible HTTP, and Ollama.

---

**“Is this a leaderboard for the best model?”**

No. That's exactly what I was trying to avoid. Rows carry lane, protocol, and comparability metadata, and the compare output is scoped on purpose.

For the launch batch specifically, I also kept the provenance explicit: the core lane and the 27B thinking lane did not come from the exact same serving path, so I’m not pretending that chart is some universal ranking.

---

**“Is the hosted report running inference?”**

No. It's just static files on GitHub Pages, generated from benchmark artifacts in the repo. No live backend behind it.

---

**“Can I merge arbitrary JSON?”**

No. Only Azimuth-shaped run directories. I didn't want a silent "import anything" path that made the results less trustworthy.

---

**“Enterprise / SLA?”**

This is OSS tooling, not a hosted service.
