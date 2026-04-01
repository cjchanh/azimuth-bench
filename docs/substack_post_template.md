# The Memory Threshold: When Structure Helps AI Agents and When It Hurts

I gave the same memory system to AI agents on both sides of a cooperation threshold. Above it, memory doubled sharing. Below it, memory tripled overhead. The intervention didn't change. The model did.

---

## The Setup

I run ten AI agents in a shared world with limited food and tools. Each tick, every agent decides what to do: gather, share, request help, move, or post knowledge. They can't see the full board. They can only see their immediate neighbors and whatever the community board tells them. If an agent's food drops to zero, it enters starvation. If it stays there, it dies.

The experiment runs on an M5 Max with 128GB unified memory, all inference through MLX. I tested four Qwen 2.5 variants — 7B-Coder, 7B-Instruct, 14B-Coder, 14B-Instruct — five seeds each, 150 ticks per run, with and without episodic memory (personal history of what the agent has done) and social memory (observations about what other agents have done). Every run produces a hash-chained SQLite database with every action, every state snapshot, every model call logged. Over seventy complete runs so far, with cross-family models (Gemma 3 12B, Llama 3.1 8B) currently executing.

The question wasn't "does memory help?" It was "what determines whether memory helps?"

## The Crossover

![Cooperation Heatmap](../visuals/cooperation_heatmap.png)

At 7B parameters, Instruct-tuned models produce roughly 55 sharing events per run. Coder-tuned models produce 9. The Instruct objective — trained on conversations, social norms, cooperative dialogue — creates agents that share resources without memory scaffolding.

At 14B parameters, it flips. Coder produces 63 mean shares. Instruct produces 0.2.

![Threshold Chart](../visuals/threshold_chart.png)

Same architecture family. Same tokenizer. Same task. Somewhere between 7B and 14B, Coder-trained models cross a capability threshold where their code-reasoning ability lets them plan cooperative sequences. Meanwhile, the Instruct models at 14B appear to over-optimize for response formatting, producing syntactically valid but strategically empty actions.

I did not expect this. I expected Instruct to dominate at every scale. It doesn't.

## Memory as Amplifier

![Memory Effect](../visuals/memory_effect.png)

Here is where it gets interesting. I added episodic memory (personal history) and social memory (observations about other agents) as a toggleable layer. Same system for every model. Same implementation. Same prompt integration. The only variable is whether the memory module is active.

Memory amplified 14B-Coder cooperation from 35 to 63 mean shares (p=0.031, Wilcoxon rank-sum). Memory destroyed 7B-Instruct cooperation from 55 to 13 mean shares (p=0.031). Both effects are statistically significant across five seeds.

The memory system didn't change. The models receiving it did.

For 14B-Coder, memory provides context that supports multi-step cooperative planning. The model already has the capability to reason about resource allocation — it can look at its history of interactions with a specific neighbor and decide to share based on past reciprocity. Memory gives it the information to execute strategies it already has the capacity to form.

For 7B-Instruct, memory adds cognitive overhead to a model already running near its capability ceiling on this task. More context doesn't help when you can't process context efficiently. The model spends tokens summarizing memories instead of deciding actions. Starvation rates climb. Sharing collapses.

The starvation data tells the same story from the other side. 7B models converge on roughly 46% starvation regardless of memory condition. 14B-Coder with memory drops to under 20%. The floor and the ceiling move together.

## The General Principle

The effect of structure depends on the base capability of the system receiving it.

This isn't just a finding about language models. I've been thinking about this pattern in policy contexts. When the federal student loan reclassification moved millions of borrowers from income-based repayment into standard repayment, the theory was structural: simplify the system, reduce overhead, improve outcomes. For borrowers who were already on stable income trajectories, the structural change worked as designed. For borrowers who relied on the income-based floor — people in public service, early-career positions, or volatile income situations — removing the floor didn't create efficiency. It created deprivation. Same structural intervention. Opposite effects. The outcome depended entirely on what was already there.

I'm not drawing a perfect analogy between language model cognition and federal loan policy. But the pattern is the same: structure amplifies existing capability. It doesn't substitute for it.

## What's Next

Cross-family runs are completing now. Gemma 3 12B and Llama 3.1 8B operate on different architectures and training distributions entirely. Early signal suggests the threshold isn't Qwen-specific — it's a property of how capability interacts with task complexity.

Cloud instances are running Coder-32B and DeepSeek-R1:32B for scale confirmation. If the crossover holds across families and at larger scale, this becomes a general finding about intervention design: you need to know where a system sits relative to the capability threshold before you can predict whether adding structure will help or hurt.

I'm targeting NeurIPS 2026 for the full paper. All code, all data, all evidence chains are open source.

## The Takeaway

Structure doesn't fix what isn't there. It amplifies what is.

If you're building AI systems — or any system where you're adding scaffolding to improve behavior — you need to measure the baseline first. Not just "does it work?" but "where is this system relative to the threshold where this intervention starts helping instead of hurting?"

That measurement changes everything.
