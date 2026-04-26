# critique.md

## Blocking Issues
- **The "Hardware-Efficiency Paradox" is unresolved across all syntheses**: Every investigator identifies a gap related to efficiency (scaling, sparsity, SSMs, linear attention), yet almost every proposed solution introduces a new computational or structural overhead (gating networks, entropy estimators, DCT-based probes, dual-stream kernels, kernel-switching logic). There is currently no unified analysis of whether the *control mechanism* is cheaper than the *bottleneck it solves*. This makes the entire deep dive vulnerable to the critique that it is proposing "theoretically interesting but practically dead" architectures.
- **Systemic Collision with Hardware Optimization**: Several proposals (MoAA, GLGA, SFGA) assume that the cost of *selection* or *routing* is negligible. However, modern SOTA performance is driven by highly optimized, static kernels (FlashAttention, etc.). If the novelty requires breaking these static execution paths, the "Efficiency" goal is fundamentally at odds with the "Novelty" goal.

## Major Issues
- **Conceptual Confusion: Observation vs. Mechanism (ASD & Intrinsic Filtering)**: 
    - *Affected Artifact*: `investigator_02` (Intrinsic Spectral Filtering) and `investigator_01` (ASD).
    - *Failure Mode*: These are framed as "proposals," but they are actually "empirical studies." A proposal must be a *new component or algorithm*. A study asking "does X happen?" is not a spinoff research idea in the context of `novelty_ideation`.
    - *Evidence Weakness*: They lack a technical mechanism that *implements* the finding.
    - *Repair Action*: Reframe these. Instead of "Investigating if X happens," propose "An Attention-based Adaptive Spectral Filter (AASF) that uses [specific mechanism] to enforce [observed property]."
- **Insufficient Mathematical Differentiation (IL-LA vs. LaplacianFormer)**:
    - *Affected Artifact*: `investigator_03` (IL-LA).
    - *Failure Mode*: The proposal for Injective-Local Linear Attention claims novelty based on "hybridizing" a kernel with a local stream, but the collision with LaplacianFormer is noted as "High." 
    - *Evidence Weakness*: It does not specify *why* the Laplacian kernel alone is insufficient in a way that a local stream specifically solves, rather than just a better global kernel.
    - *Repair Action*: Perform an adversarial search specifically on the *residual error* of LaplacianFormer in high-frequency/local-dependency tasks to justify the local stream.
- **Vague Technical Mechanism in SSM Proposal**:
    - *Affected Artifact*: `investigator_02` (Single-Pass Non-Causal SSM).
    - *Failure Mode*: "A modified State-Space Duality (SSD) kernel that incorporates a non-causal mechanism" is too vague to be a valid proposal.
    - *Evidence Weakness*: It lacks a concrete "kernel shape" or "asymmetric update rule."
    - *Repair Action*: The subagent must propose a specific mathematical form (e.g., "An asymmetric state-update $\mathbf{h}_t = \mathbf{A}\mathbf{h}_{t-1} + \mathbf{B}\mathbf{x}_t$ where $\mathbf{A}$ is a function of future-lookahead $\tau$").

## Minor Issues
- **Terminology Drift**: The term "Sink" is used inconsistently across `investigator_01` (geometric necessity) and `investigator_03` (semantic shortcut). While this is a known research tension, the synthesis should explicitly label this as a "definitional contradiction" to prevent merging incompatible ideas.
- **Over-reliance on CV/Signal Benchmarks**: Several proposals (ASD, SFGA, GLGA) rely heavily on Vision or Signal-processing evidence. The transition to LLM-scale text workloads is assumed rather than justified.

## Targeted Follow-Up Searches
1. **Kernel Dispatch Overhead**: `search(query="Triton kernel launch latency vs. static CUDA kernel", tools=["google_scholar_search"])` - To validate or kill MoAA and GLGA.
2. **Entropy-Quantization Link**: `search(query="correlation between attention entropy and quantization error in LLMs", tools=["paper_relevance_search"])` - To promote or demote ED-DRP.
3. **Mathematical Collision (SSM)**: `search(query="single-pass bidirectional state space model kernel", tools=["paper_bulk_search"])` - To check if the "Single-Pass Non-Causal SSM" is actually already a known technique in non-autoregressive transduction.

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
|---|---|---|---|---|---|
| **MoAA** | `survives but needs more search` | Hardware/Launch overhead | FlashAttention/Static kernels | Kernel switching latency vs. FLOP savings | Profile Triton kernel switching overhead. |
| **ED-DRP** | `survives` | Entropy $\neq$ Precision requirement | MLoRQ | Empirical correlation of entropy to bit-width loss | Test entropy vs. quantization error. |
| **ASD** | `speculative` | Proxy error (Attention $\neq$ Model) | Zhai et al. (2023) | Correlation of $\text{Var}(A)$ to $\text{Loss}$ | Define $\delta$ (perturbation) and correlate to F1. |
| **GLGA** | `survives but needs more search` | Collision with "Learned Sparsity" | Asadi et al. (2025) | Conv-mask overhead vs. sparsity gains | Search "learned structural sparsity". |
| **Non-Causal SSM** | `too vague` | Mathematical feasibility/Redundancy | VSSD (2024) | Specific kernel update equation | Define the asymmetric update rule. |
| **Intrinsic Filtering** | `not technically meaningful` | It's a study, not a method | Momentum Attention | A specific implementable component | Turn "investigation" into "adaptive filter layer." |
| **LCA** | `survives` | Complexity vs. Stability | Registers (Darcet et al.) | Stability gain per parameter added | Compare LCA smoothness vs. Register noise. |
| **SFGA** | `speculative` | DCT-probe latency | Swin / FANet | Latency of intra-block DCT | Measure DCT overhead in standard Transformer blocks. |
| **IL-LA** | `probably already done` | Mathematical overlap | LaplacianFormer | Why a local stream is needed if kernel is injective | Define the injectivity-locality mismatch. |

## Approval Verdict
**approve-with-reservations**

**Reasoning**: The depth of the literature review is excellent, and the "Research Gaps" are well-grounded in actual collisions. However, the synthesis is currently too "optimistic" regarding hardware feasibility. The investigators have identified high-value theoretical gaps, but have failed to adequately pressure-test the *system-level* cost of their proposed solutions. The transition from "observation" to "proposal" is also inconsistent. Proceed only after the "Hardware-Efficiency Paradox" is addressed and the "studies-as-proposals" are reframed as actual technical components.