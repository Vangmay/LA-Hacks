# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: The seed paper itself
- Why it matters: Fundamental architecture for modern LLMs and sequence transduction, introducing the Transformer model.
- Caveat: N/A


## Paper: Mechanisms of Symbol Processing for In-Context Learning in Transformer Networks

- Paper ID: 0e703833cf10099e0d825b3490a6956c88e00d73
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Investigates a fundamental capability (symbol processing) of the Transformer architecture.
- Why it matters: Explores the gap between the computability of symbolic programs and the learnability of these programs by transformers; proposes a mechanistically interpretable approach (PSL) to bridge this.
- Caveat: Focuses on computability rather than learnability.


## Paper: The Kinetics of Reasoning: How Chain-of-Thought Shapes Learning in Transformers?

- Paper ID: 58549bbb5bffab9c286694963639586c5388313f
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Directly investigates the learning dynamics of symbolic reasoning and the impact of CoT.
- Why it matters: Shows that CoT accelerates generalization but fails to overcome high algorithmic complexity tasks (like list intersections) and identifies a 'transient trace unfaithfulness phase' where models provide correct answers without following the CoT steps.
- Caveat: Investigates learning through the lens of 'grokking'.


## Paper: FaithCoT-Bench: Benchmarking Instance-Level Faithfulness of Chain-of-Thought Reasoning

- Paper ID: 6968f45aabe7b328bb322bc35c808a6d5e5ea006
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Directly addresses the problem of evaluating CoT faithfulness at an instance level.
- Why it matters: Introduces a unified benchmark (FaithCoT-Bench) and an expert-annotated collection (FINE-CoT) to move beyond mechanism-level analysis to practical, instance-level detection of unfaithfulness.
- Caveat: Focuses on detection rather than inherently fixing unfaithfulness.


## Paper: Measuring Faithfulness in Chain-of-Thought Reasoning

- Paper ID: 827afa7dd36e4afbb1a49c735bfbb2c69749756e
- Year: 2023
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: One of the foundational papers investigating whether CoT is actually a faithful explanation of the model's internal process.
- Why it matters: Shows that models exhibit high variation in faithfulness and often ignore the CoT when predicting answers. Suggests faithfulness is task- and model-size dependent.
- Caveat: Focuses on measuring faithfulness via interventions (e.g., adding mistakes) rather than detecting it in real-time.


## Paper: Chain-of-Thought Reasoning In The Wild Is Not Always Faithful

- Paper ID: e71ff5188cc6435f0ba3ebbb054829c0b1dd3ba8
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Investigates unfaithfulness in realistic (in-the-wild) settings, specifically through post-hoc rationalization.
- Why it matters: Identifies 'Implicit Post-Hoc Rationalization' where models generate coherent but logically contradictory arguments to satisfy implicit biases (e.g., towards 'Yes' or 'No'). Shows that even frontier models have non-zero unfaithfulness rates.
- Caveat: Focuses on bias-driven unfaithfulness rather than mechanistic failures.


## Paper: Emergence of Superposition: Unveiling the Training Dynamics of Chain of Continuous Thought

- Paper ID: 09fdff4870d6e390a9151562a286ed27fba0fe6d
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Investigates how models learn to maintain multiple reasoning traces (superposition) in continuous thought.
- Why it matters: Provides theoretical insight into how a two-layer transformer can solve graph reachability by balancing exploration and exploitation through logit dynamics.
- Caveat: Theoretical analysis on a simplified two-layer architecture.


## Paper: How Does Unfaithful Reasoning Emerge from Autoregressive Training? A Study of Synthetic Experiments

- Paper ID: 60bf56ed72d032600f01161fd40769273bef84a8
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Investigates the fundamental emergence of unfaithfulness from autoregressive training.
- Why it matters: Uses controlled synthetic experiments (modular arithmetic) to study how unfaithful reasoning patterns emerge during training.
- Caveat: Uses small transformers and synthetic tasks.


## Paper: Beyond Correctness: Rewarding Faithful Reasoning in Retrieval-Augmented Generation

- Paper ID: 01021187b2ac3b2341b674c2063b1566b87ec6ef
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_bulk_search
- Relation to seed: Investigates training objectives for faithfulness within the context of RAG.
- Why it matters: Introduces VERITAS, a framework that integrates fine-grained faithfulness rewards (information-think, think-answer, think-search) into RL, showing that rewarding intermediate traceability outperforms pure outcome-based rewards.
- Caveat: Specifically targeted at agentic search/RAG settings.


## Paper: ReFIne: A Framework for Trustworthy Large Reasoning Models with Reliability, Faithfulness, and Interpretability

- Paper ID: 0287972927ca35f5d07485bccb7d0f51599b9288
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_bulk_search
- Relation to seed: Proposes a training framework for multi-dimensional trustworthiness in reasoning models.
- Why it matters: Uses SFT combined with GRPO to optimize for interpretability, faithfulness (disclosing decisive information), and reliability (self-assessment). Demonstrates improvements in faithfulness (+18.8%) and interpretability (+44.0%).
- Caveat: Evaluated on Qwen3 models and mathematical benchmarks.
