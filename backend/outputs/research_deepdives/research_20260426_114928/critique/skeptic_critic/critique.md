# Critique Report: Scaling and Inductive Bias in Sequence Modeling
**Critic ID:** `skeptic_critic`  
**Lens:** `overclaiming, contradictions, and weak inference`  
**Date:** 2026-04-26

---

## Blocking Issues

1.  **Mathematical Associativity of HR-Mamba (Proposal Candidate):** The investigator claims that H-infinity Riccati updates can be integrated into "hardware-aware associative scans." Classical H-infinity and Kalman filters involve matrix inversion or complex non-linear updates ($P_{t+1} = f(P_t)$) that are notoriously non-associative in their standard Riccati form. If the update $f$ is not associative, the model falls back to $O(n)$ serial recurrence, losing the parallel speedup of Mamba/S4. **Action:** Perform a targeted search for "associative scan Riccati" or "parallelizable H-infinity Filter" to verify if a linear/associative approximation even exists.
2.  **Over-reliance on TTR (DeltaNet 2026) for Scaling:** Proposal Candidate 1 (HPR) assumes that "Test-Time Regression" (TTR) with second-order preconditioning can scale to 1M+ context via hierarchy. However, second-order methods typically incur $O(d^3)$ or $O(d^2)$ costs relative to the state dimension $d$. In 1M context scenarios, $d$ is often expanded to compensate for loss. The investigator fails to reconcile the $O(d^2)$ preconditioning overhead with the VRAM efficiency goals. **Action:** Analyze DeltaNet's actual state-update complexity to see if "Preconditioned TTR" is feasible at scale.

## Major Issues

1.  **The "Selection vs. Coverage" Contradiction:** Investigator 02 identifies a "Selection Gap" where SSMs fail to pick the best reasoning path, while Investigator 01 proposes "HPR" to solve "decay-precision." These are mid-level contradictions: if the problem is *selection* (picking one out of many), a *hierarchical summary* (HPR) might actually worsen the problem by blurring the distinctness of candidates into a "compressed second-order summary."
2.  **SelecLR Novelty Collision:** The `SelecLR` proposal claims novelty in SNR-based parameter-group learning rates. This is functionally identical to many adaptive optimization strategies (e.g., Lion, Sophia, or even standard Adam with per-layer scaling) used in 2024-2025. Without a specific "SSM-aware" mechanism that differs from general gradient variance adaptations, this is an incremental optimization tweak, not a research spinoff.
3.  **Vague "Entropy Controller" in ESEK:** Proposal Candidate 3 (ESEK) relies on a "controller sub-network" predicting state-pressure. This is a classic "deus ex machina" in architecture proposals. If the controller is too small, it won't capture entropy accurately; if it's large, it defeats the efficiency gains of the linear model.
4.  **Missing "V-Mamba / VGamba" Collision Check:** Proposal Candidate 2 (BQTL) for video diffusion ignores the heavy competition from 2024-2025 Vision-Mamba variants. Many of these already use bidirectional scans and "temporal latents." The distinction ("Quasiseparable Matrix" instead of "Simple Scan") needs a much higher evidence bar to prove it's not just a rebranded Hydra (2024).

## Minor Issues

1.  **Stale Terminology:** The use of "Needle-in-a-Haystack" as the primary validation for 1M+ context in 2026 is becoming "stale." Evidence (SCBench 2024) suggests models now pass the "needle" test but fail on "Reasoning-in-a-Haystack" or "Logic-Chain-Retrieval."
2.  **Hardware-Awareness Gap:** While "FlashAttention-3" is mentioned as a competitor, there is no mention of the specific hardware constraints of Blackwell or post-Cerebras chips which favor specific tensor-core layouts over the "matrix mixers" suggested in Hydra/HPR.

## Targeted Follow-Up Searches

1.  `"DeltaNet" + "preconditioning complexity" + "state dimension"`: Determine if $O(d^2)$ makes it slower than FlashAttention at 32k.
2.  `"associative scan" + "Riccati" + "minimax"`: Check for any existing proofs of H-infinity parallelization.
3.  `"VGamba" (2025) OR "Hydra-Video" (2025)`: Check if BQTL's core mechanism is already published.
4.  `"UnHiPPO" (2025) limitations`: Verify if the "noise-free" failure can be solved by simple layer-norm adjustments rather than a full H-infinity overhaul.

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HPR** | `survives but needs more search` | Does DeltaNet already imply hierarchical summaries? | *Block-State Transformers* | Overhead of summary gradients. | Formalize the "Delta-Segment-Tree" update rule. |
| **BQTL** | `probably already done` | Hydra (2024) already did QMMs; VGamba (2025) did video. | *VGamba / Hydra-Video* | Comparative VRAM at 3D volumes. | Define the "low-rank temporal latent filter" formally. |
| **ESEK** | `too vague` | General architecture gating is common. | *Matryoshka Embeddings / MoE* | SNR of entropy to state size. | Specify the "State-Pressure" equation. |
| **HR-Mamba** | `speculative` | **Blocking:** Associativity of Riccati updates. | *Luis et al. (2024)* | Proof of $O(\log n)$ scan. | Derive the associative operator or fail. |
| **SelecLR** | `not actually novel` | Too close to Adam/Sophia per-parameter scaling. | *Sophia (2023) / Adafactor* | Why generic SNR isn't enough. | Target the specifically "Selective" matrices. |
| **DyG-Hybrid** | `survives` | "Surprise-meter" is known; "dynamic gating" is well-explored. | *Mixture of Depths (2024)* | Correlation of entropy to selection. | Test if entropy signal originates from the SSM state. |

## Approval Verdict
**APPROVE-WITH-RESERVATIONS**

The investigators have surfaced high-quality "frontier" citations (DeltaNet, UnHiPPO, SCBench). However, the proposals lean heavily on "Math Magic" (H-infinity associative scans) or "Structure Slapping" (Hierarchy + TTR) without addressing the underlying computational complexity ($O(d^2)$) or existing 2025 SOTA (VGamba). The HR-Mamba proposal is a high-risk/high-reward theory that requires immediate mathematical validation before further investment.