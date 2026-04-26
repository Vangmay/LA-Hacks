# Critique Report: Scaling and Inductive Bias in SSMs
- **Critic ID:** `evidence_critic`
- **Critique Lens:** Source grounding and citation quality
- **Research Objective:** `novelty_ideation` (2026 Timeline)

---

## Blocking Issues

1.  **Mathematical Falsifiability of HR-Mamba's Associative Scan:**
    - **Affected Artifact:** Proposal: HR-Mamba (Investigator 02).
    - **Failure Mode:** The proposal claims a "minimax-optimal H-infinity robust estimation" can be implemented via a "hardware-aware associative scan."
    - **Evidence Weakness:** H-infinity Riccati updates typically involve matrix inversions or the solution of algebraic Riccati equations (ARE) that are fundamentally non-associative. Luis et al. (2024) successfully mapped the *Kalman* filter (L2-optimal) to a scan by exploiting the linear-Gaussian structure. H-infinity is notoriously sensitive to the performance bound $\gamma$; there is no evidence provided that the $\gamma$-dependent Riccati recursion can be reformulated into the semi-group properties required for a parallel scan.
    - **Concrete Repair:** Conduct a targeted search for `"H-infinity" associative property` or `minimax recurrence parallel scan`. If no derivation exists, the proposal must be downgraded to `speculative` or `rejected` for failing the technical specificity requirement.

2.  **Hardware-Agnostic "Elastic" Kernels (ESEK):**
    - **Affected Artifact:** Proposal: ESEK (Investigator 01).
    - **Failure Mode:** Lack of implementation path for variable-length hidden states.
    - **Evidence Weakness:** The proposal suggests dynamically scaling the hidden state dimension $d$ based on entropy. Current GPU kernels (Triton/CUDA for Mamba/FlashIteration) rely on fixed tiling and static shared memory allocation. A "variable-length memory" state breaks the fundamental parallelization of the scan/recurrence.
    - **Concrete Repair:** Specify the `Technical Mechanism` for hardware execution. Does this use a padding strategy, or a "Mixture of State-Sizes" (MoSS) approach where tokens are routed to fixed but different-sized buckets? Without this, the proposal is `too vague`.

---

## Major Issues

1.  **Collision between BQTL and Existing Diffusion SSMs:**
    - **Affected Artifact:** Proposal Candidate 2: BQTL.
    - **Failure Mode:** Probable collision with contemporaneously published or slightly older work.
    - **Evidence Weakness:** The synthesis mentions "Hong et al. (2025) Diffusion SSMs" as evidence but doesn't explain how BQTL is *distinct* from it. Furthermore, "ViM" (Vision Mamba) and "ZigZag Mamba" (2024) already proposed bidirectional scanning for spatial/temporal data.
    - **Concrete Repair:** Perform a collision search for `"Quasiseparable Matrix" video diffusion`. The proposal must explicitly state how the "low-rank temporal latent filter" differs from the bi-directional scan mechanisms in `ViM` or `Hydra`.

2.  **Incomplete Proof of "Curvature-Decay" Contradiction:**
    - **Affected Artifact:** Gap 1 (Investigator 01).
    - **Failure Mode:** Unsupported claim that DeltaNet (2026) fails on long-range decay.
    - **Evidence Weakness:** The synthesis claims DeltaNet solves curvature locally but ignores SCOUT’s long-range findings. However, preconditioning (second-order info) often inherently improves the spectral radius of the recurrence, potentially *fixing* decay.
    - **Concrete Repair:** Use `paper_relevance_search` on "DeltaNet (2026) long-context performance" to see if the authors already included a "decay-aware" version or an implicit hierarchy.

---

## Minor Issues

1.  **Over-reliance on "DeltaNet (2026)":** Both investigators treat DeltaNet as a "magic bullet" for expressivity without citing independent reproduction results. Given the 2026 date, recent "SCBench" reports should be checked to see if DeltaNet's theoretical gains translate to real-world VRAM savings.
2.  **SelecLR Novelty:** This proposal is largely a "training recipe." While useful, it borders on "generic" because "Adaptive Learning Rates" (Adam, Adafactor) already scale by gradient variance. The SNR-specific claim needs to be linked to the *selection* matrices $B$ and $C$ more specifically to survive.

---

## Targeted Follow-Up Searches

1.  `"H-infinity" Riccati equation "associative scan" OR "parallel scan"`: Determine if the minimax update is mathematically parallelizable.
2.  `"DeltaNet" hierarchical "segment tree"`: Check if the "Delta-Segment-Tree" in HPR was already anticipated by the original DeltaNet authors (Yang et al.).
3.  `"Hydra" SSM video diffusion scale`: Specifically check for VRAM benchmarks of Hydra-like mixers on 3D data.
4.  `"Mixture of Depths" vs "Jamba" entropy gating`: Evaluate if DyG-Hybrid's "Surprise Meter" is distinct from existing MoD/MoE gating mechanisms.

---

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
|---|---|---|---|---|---|
| **HPR** | `survives` | Complexity overhead | Block-State Transformer / Mega | Benchmark vs. 128k context SWA | Show HPR is $O(n)$ in VRAM, not just $O(n)$ in time. |
| **BQTL** | `speculative` | Domain application only | ViM / ZigZag Mamba | Proof of "ghosting" reduction | Define the "low-rank latent" math. |
| **ESEK** | `too vague` | Hardware implementation | Adaptive State-Space MoE | CUDA/Triton feasibility | Propose "Bucketed Dim sizes". |
| **HR-Mamba**| `survives but needs search`| Math correctness | Luis et al. (2024) | Associative proof for Riccati | Sketch the operator fusion. |
| **SelecLR** | `not actually novel` | Incremental optimizer | Adam / MuP | Proof that global LR fails | Link SNR to "Induction Heads". |
| **DyG-Hybrid**| `probably already done` | Structural similarity | Mixture of Depths (2024) | Gating signal performance | Differentiate from MoD. |

---

## Approval Verdict

**Verdict:** `Approve with Reservations`

The synthesis identifies high-value gaps (TTR framework, H-infinity restoration), but the proposals frequently border on "Apply X to Y" or ignore the hardware constraints of the associative scan. **Proposal Candidate 1 (HPR)** and **HR-Mamba** are the strongest, provided the mathematical associative property of the latter is verified. **ESEK** and **SelecLR** require significant hardening of their technical mechanisms to be considered peer-review-ready spinoffs.