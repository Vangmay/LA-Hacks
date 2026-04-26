# Critique Report: Scaling and Inductive Bias in SSMs

- **Critique ID**: `novelty_critic`
- **Lens**: Novelty and closest-prior-work pressure
- **Workspace**: `C:\Users\ishur\OneDrive\Desktop\VS_Code_Projects\LA-Hacks\backend\outputs\research_deepdives\critique\novelty_critic`
- **Research objective**: `novelty_ideation`

---

## Blocking Issues

1.  **Associative Scan Mathematical Compatibility (Proposal HR-Mamba)**:
    - **Affected Artifact**: `Proposal Candidate: HR-Mamba (Investigator 02)`
    - **Failure Mode**: The proposal claims to integrate $H_\infty$ robust estimation into an associative scan framework. This is a potential mathematical impossibility or extremely high-risk claim. Traditional $H_\infty$ controllers require solving the Algebraic Riccati Equation (ARE) or differential Riccati equations, which are inherently sequential and non-linear in their state-update.
    - **Evidence Weakness**: The synthesis cites `Luis et al. (2024)` for Kalman scans, but Kalman filters (L2-optimal) have a linear update that allows for the parallel prefix sum (associative scan) trick. $H_\infty$ (L-$\infty$ optimal) usually involves a "skeptical" gain that depends on the current state-error bound, which makes the operator non-associative.
    - **Concrete Repair**: Perform a targeted derivation check. Specifically, can the $H_\infty$ filter be formulated as a group operation? If not, the proposal must pivot to a "Local $H_\infty$ Update" or a "Linearized $H_\infty$ Approximation" that preserves associativity.

2.  **Unresolved SOTA Collision: VGamba/Mamba-Video (Proposal BQTL)**:
    - **Affected Artifact**: `Proposal Candidate 2: BQTL (Investigator 01)`
    - **Failure Mode**: The proposal suggests the "First non-causal bidirectional mixer for video diffusion." This likely ignores contemporaneous 2024-2025 work like `VGamba` (Haruna et al.) or `Video-Mamba`.
    - **Evidence Weakness**: Subagent 02 identifies the risk in the "Recommended Next Searches" but the investigator promotes it to a "surviving candidate" anyway.
    - **Concrete Repair**: Use `google_scholar_search` with the query `"VGamba" video diffusion "matrix mixer"` to determine if BQTL's use of *quasiseparable matrices* is the distinguishing factor, or if it has already been superseded by simple bidirectional SSM scans.

---

## Major Issues

3.  **Vague Improvement over Adaptive Computation (Proposal ESEK)**:
    - **Affected Artifact**: `Proposal Candidate 3: ESEK (Investigator 01)`
    - **Failure Mode**: "Entropy-Steered Elastic Kernels" is fundamentally similar to "Adaptive Computation Time" (ACT), Mixture-of-Experts (MoE), or `AdaTape` (2023). 
    - **Evidence Weakness**: There is no explanation of why *kernel expansion* is the right mechanism versus just adding more layers or experts (MoE) when entropy is high. The "technical mechanism" is a "controller sub-network," which is a standard MoE gate.
    - **Concrete Repair**: Contrast ESEK specifically against *Mixture of Depths* (Google, 2024). Does changing the kernel dimension $\phi$ offer a better VRAM/Expressivity frontier than skipping layers? If not, reject as "not actually novel."

4.  **Optimization Trick vs. Architecture Spinoff (Proposal SelecLR)**:
    - **Affected Artifact**: `Proposal Candidate: SelecLR (Investigator 02)`
    - **Failure Mode**: This is a training schedule/optimizer tweak rather than a research spinoff proposal for a new model or theory. 
    - **Evidence Weakness**: While it builds on `Okpekpe (2025)`, it doesn't provide a long-term architectural contribution. In `novelty_ideation` mode, we seek structural or mechanistic changes.
    - **Concrete Repair**: Reframework `SelecLR` as a **Signal-Aware SSM Layer**. Instead of a fixed schedule, can the architecture itself perform a "normalization" that scales gradients based on SNR? This moves it from a training script to a new model class.

---

## Minor Issues

5.  **Hardware Efficiency Omission**:
    - **Affected Artifact**: `Section: Scaling Beyond Quadratic Complexity (Investigator 01)`
    - **Issue**: Both Hydra (2024) and DeltaNet (2026) are praised for $O(n)$, but neither synthesis addresses the *constant factors* on modern H100/Blackwell GPUs. $O(n^2)$ FlashAttention-3 is often faster than $O(n)$ recurrent scans until $n > 32k$.
    - **Repair**: Add a benchmark requirement to the "Minimum validation" of HPR and BQTL to measure "Time-to-First-Token" against FlashAttention.

6.  **Redundancy in Subagent Coverage**:
    - **Affected Artifact**: `Investigator 02 Table`
    - **Issue**: Subagent 01 and 02 both rely heavily on identifying the "Recall failure." There is a lack of coverage on the *reproducibility* of these claims (e.g., have the 2025 results been replicated on diverse datasets?).
    - **Repair**: Targeted search for "reproduction of Mamba recall failures" to ensure we aren't building proposals on top of a single-dataset fluke.

---

## Targeted Follow-Up Searches

1.  **Search Family: Riccati Associative Scan**
    - `query`: "parallel prefix sum" OR "associative scan" AND "Riccati equation" OR "H-infinity filter"
    - `goal`: Verify if Proposal Candidate: HR-Mamba is mathematically sound for GPU acceleration.
2.  **Search Family: DeltaNet Hierarchy**
    - `query`: "DeltaNet" OR "Test-Time Regression" AND "Hierarchical" OR "Segment-Tree"
    - `goal`: Check if the "Delta-Segment-Tree" in HPR is already being developed by the DeltaNet authors (collision check).
3.  **Search Family: Elastic SSMs**
    - `query`: "adaptive state size" SSM OR "elastic hidden state" Mamba
    - `goal`: Identify collisions for ESEK.

---

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
|---|---|---|---|---|---|
| **HPR** | `survives but needs more search` | DeltaNet authors likely already considering hierarchy. | *DeltaNet (2026)* follow-ups | Proof of VRAM savings vs. SWA. | Search for "Hierarchical TTR". |
| **BQTL** | `speculative` | Implementation of QMM in 3D volumes is unproven. | *VGamba (2025)* / *Hydra (2024)* | Hardware benchmarks for 3D QMM. | Compare QMM to 3D-SSM scans. |
| **ESEK** | `not actually novel` | Overlap with Adaptive Computation/MoE. | *AdaTape (2023)* / *Mixture of Depths* | Evidence that kernel expansion > MoE. | Reformulate as "State-MoE". |
| **HR-Mamba**| `survives` | High risk of being non-parallelizable. | *Luis et al. (2024)* (Kalman focus) | Lemma proving $H_\infty$ associativity. | Derive the associative operator. |
| **SelecLR** | `too vague` | It's an optimizer setting, not a spinoff model. | *AdaFactor* / *SNR-based weighting* | SNR distribution across SSM params. | Pivot to "Signal-Gate SSM Layer". |
| **DyG-Hybrid**| `survives` | Gating criteria might be noisy. | *Jamba (2024)* / *Griffin (2024)* | Proof of "Surprise" vs "Reasoning". | Test 'Surprise' on GSM8K/MATH. |

---

## Approval Verdict

**`APPROVE WITH RESERVATIONS`**

The syntheses are excellent in terms of 2025-2026 literature awareness (DeltaNet, SCOUT, UnHiPPO). However, the "Novelty Ideation" layer is currently leaning on a few high-risk mathematical assumptions (specifically the $H_\infty$ scan) and potential collisions in the video-SSM space.

**Required actions before finalization**:
1.  Verify the associativity of the $H_\infty$ Riccati update.
2.  Check for "Hierarchical DeltaNet" to protect the novelty of HPR.
3.  Pivot SelecLR from an optimizer tweak to an architectural component.