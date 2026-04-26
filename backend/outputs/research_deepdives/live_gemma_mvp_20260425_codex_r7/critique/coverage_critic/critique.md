# Critique: coverage_critic

**Critic ID:** `coverage_critic`  
**Critique lens:** `coverage and search recall`  
**Workspace:** `backend/outputs/research_deepdives/live_gemma_mvp_20260425_codex_r7/critique/coverage_critic`  
**Research objective:** `novelty_ideation`

---

## Blocking Issues

1.  **Unresolved Architectural Collision (Nemotron Nano 2):** In Synthesis 2, the "Hierarchical Local-Global Transformer-SSM Hybrid" is flagged as having a high-priority collision with *NVIDIA Nemotron Nano 2*. However, the synthesis fails to provide a definitive distinction. If Nemotron Nano 2 already implements parallel/hierarchical fusion, the entire "Hierarchical" branch of research is dead. The investigator must move from "needs verification" to "architectural differentiation" before any proposal can be considered.
2.  **Routing Absorption Neglect:** Synthesis 3 identifies "Routing Absorption" (the tendency of gates to collapse to a single mode) as a fundamental barrier. However, Synthesis 2's "Continuous/Soft Hybridization" proposal proposes a sigmoid-gated mechanism that is *highly susceptible* to exactly this failure mode. The subagents are working in silos; the efficiency subagent is proposing a solution that the novelty auditor has already labeled as fundamentally broken.

## Major Issues

1.  **Weak Novelty Differentiation (Constrained Policy Optimization):** The proposal in Synthesis 1 to use Lagrangian-constrained optimization to fix exposure bias is technically thin. Standard PPO and DPO already utilize KL-divergence penalties as a constraint to prevent distribution drift. The proposal must specify exactly how its Lagrangian formulation differs from the standard $\text{Reward} - \beta \text{KL}$ objective to claim novelty. Without a specific math-level differentiator (e.g., a dynamic $\lambda$ tied to semantic fidelity metrics rather than just distribution distance), this is a "rebranding" of existing RLHF, not a new idea.
2.  **Signal-to-Noise Gap (Faithfulness Score):** The "Quantifying Attention Faithfulness" proposal (Synthesis 1) relies on weight-patching. The literature (e.g., Jain & Wallace) suggests that attention weights are often non-causal. While the proposal acknowledges high variance as a risk, it fails to provide a technical mechanism to distinguish *causal weight signal* from *stochastic noise* in a high-dimensional parameter space. It lacks a "denoising" or "aggregation" component to make the Spearman correlation statistically significant.
3.  **Computational Circularity (DITA):** The DITA proposal (Synthesis 1) suggests using "differentiable surprisal" as a gate. Surprisal is typically a function of the output distribution $P(x_t | x_{<t})$. To use it as an *input* to a gating coefficient $\alpha_t$ for the *current* state update, the model must effectively predict its own uncertainty or perform a look-ahead. This creates a computational loop that may negate the $O(L)$ complexity benefits the proposal aims to achieve.

## Minor Issues

1.  **Inconsistent Paper IDs:** Synthesis 2, Subagent 03 refers to a paper ID `9e06fa...` as a "critical comparison paper" but does not resolve it. This is a failure in the evidence chain.
2.  **Terminology Overlap:** The term "Sculpting" is used in Synthesis 2 (ASUR) and Synthesis 3. While semantically related, the investigator should clarify if "sculpting" refers to the manifold topology or the parameter optimization process to avoid conceptual blurring.

## Targeted Follow-Up Searches

1.  **Architectural Audit:** `exact search: "NVIDIA Nemotron Nano 2" architecture fusion mechanism` (to resolve the blocking collision).
2.  **Adversarial Collision:** `search: "differentiable surprisal gating" AND "linear attention" OR "SSM"` (to check if DITA is actually a known technique in recent SSM literature).
3.  **Mathematical Differentiation:** `search: "Lagrangian multipliers" vs "KL penalty" in RLHF and DPO` (to find the technical gap for the Constrained Policy proposal).
4.  **Hardware Feasibility:** `search: "kernel switching latency" AND "Attention vs SSM" OR "Mamba"` (to quantify the "death by a thousand cuts" risk in the SEG-TKR proposal).

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
|---|---|---|---|---|---|
| **DITA** | `speculative` | Computational overhead of calculating surprisal for gating. | SAGA / KV Admission | How is surprisal calculated without a full pass? | Define a lightweight "surprisal proxy" head. |
| **Faithfulness Score** | `survives but needs more search` | Signal-to-noise ratio in weight-patching. | Stolfo et al. (2023) | Stability of weight-level vs activation-level patching. | Propose an ensemble or aggregation method for weight signals. |
| **Constrained Policy** | `not actually novel` | It is a restatement of KL-regularized RLHF/DPO. | DPO / PPO | The mathematical delta from standard $\beta$-KL. | Define a *semantic* constraint vs a *distributional* constraint. |
| **Continuous Hybrid** | `probably already done` | It is essentially a Mixture-of-Experts (MoE) with architectural experts. | MambaFormer / MoE | Evidence that routing doesn't collapse (Absorption). | Add a "diversity penalty" to the gating loss. |
| **ASUR** | `survives` | Overlap with "Structured SSMs". | Mamba / Structured SSMs | Distinction between "sculpting" and "parameterized gating". | Define the specific "reservoir" manifold being sculpted. |
| **Hierarchical Hybrid** | `too vague` | Collision with Nemotron Nano 2. | NVIDIA Nemotron Nano 2 | Verification of Nemotron's fusion type. | Pivot to "asynchronous" rather than "parallel" fusion. |
| **SEG-TKR** | `too vague` | Kernel-switching latency/complexity. | Jamba / Sparsifiner | Hardware-level cost of Attention-SSM switching. | Propose a "unified kernel" implementation detail. |
| **CO-SHT** | `survives` | Reward sparsity for structural consistency. | VERITAS / ReFIne | Definition of $R_{structural\_consistency}$. | Formalize the reward as a causal impact score. |

## Approval Verdict

**reject**

**Reasoning:** The current syntheses are a collection of "high-level intuitions" rather than "technically precise research directions." While the literature coverage is broad, the subagents are failing to perform the most critical task: **adversarial reconciliation.** 

The "Routing Absorption" problem identified in Synthesis 3 should have triggered a "Major Issue" or "Blocking Issue" flag in the proposals of Synthesis 2. Furthermore, the novelty claims for the RL and Gating proposals are currently indistinguishable from existing SOTA (PPO/DPO/KV-Admission) without deeper mathematical specification. The research is currently "synthesis-rich but novelty-poor." 

**Required Action:** The investigator must re-run the synthesis with a focus on **cross-artifact tension.** Every proposal must explicitly state how it avoids the "Routing Absorption" and "Kernel-Switching Latency" traps identified by other subagents.