# Global Evidence Map: Transformer Architectural Evolution & Limits

This map synthesizes all evidence gathered across the `investigator_01_experiments` run, linking specific papers to identified research gaps, subagent roles, and the resulting novelty proposals.

## 1. Research Landscape & Evidence Nodes

The evidence is organized into five functional buckets that track the evolution from foundational attention to current structural bottlenecks.

### Bucket A: Foundational Lineage (The "Ancestry" Base)
*Provides the baseline against which all architectural deviations are measured.*

| Paper ID | Year | Core Contribution | Relation to Research |
| :--- | :--- | :--- | :--- |
| `fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5` | 2014 | Original attention in RNNs | Baseline for sequential attention. |
| `204e3073870fae3d05bcbc2f6a8e263d9b72e776` | 2017 | Pure Transformer (Self-Attention) | The "Seed" architecture for all studies. |
| `Convolutional Seq2Seq` | 2017 | Convolutional alternatives to recurrence | Precursor to hybrid CNN-Transformer paths. |

### Bucket B: Inductive Bias & Scaling (The "Tension" Zone)
*Explores the conflict between pure attention scaling and the necessity of structural priors.*

| Paper ID | Year | Core Contribution | Relation to Research |
| :--- | :--- | :--- | :--- |
| `6edccbd83a9aae204785d4821f97855677c33866` | 2022 | Scaling laws vs. Architecture | Challenges the "scaling solves all" assumption. |
| `00604535b29dbb2ea2af9e3d49abb0d26b0a8c27` | 2022 | DMT-Net (CNN-Transformer Hybrid) | Proves CNN bias aids data-scarce training. |

### Bucket C: Hybridization & Domain Trends (The "Evolution" Zone)
*Documents the contemporary shift toward multi-component "glue" architectures.*

| Paper ID | Year | Core Contribution | Relation to Research |
| :--- | :--- | :--- | :--- |
| `00796ad8bd3a7eb0bfa39085bc9b3c2e3a82dc07` | 2025 | ECViT (Local Inductive Bias) | Current SOTA for efficient hybridization. |
| `0572ee725c139b07cd02695751d641c26b068ae8` | 2025 | CTLE (Triple-Hybrid) | Trend of CNN-Transformer-LSTM fusion. |
| `838e911ebe009dbadb87e6f78b654460c1cddd3a` | 2025 | TransXSSM (Hybrid SSM-Transformer) | Addresses positional encoding in hybrids. |
| `00459840cecd4a8b520e95fdb22d89af06583cc2` | 2026 | FusionSegNet (Parallel Fusion) | Uses attention-guided fusion between branches. |

### Bucket D: Failure Modes & Gaps (The "Novelty" Triggers)
*Critical technical evidence identifying where current models fail.*

| Paper ID | Year | Identified Failure/Gap | Targeted Novelty |
| :--- | :--- | :--- | :--- |
| `31116ee2b039d1c2e5dc71b64b9a240b416e663b` | 2025 | **Semantic Misalignment** (DBAANet) | S3A (Alignment Framework) |
| `BGSC-Net` | 2026 | **Semantic Misalignment** | S3A (Alignment Framework) |
| `bbe0e4cc9b052e960362fdc18b6805043b81ca6b` | 2024 | **Compositionality Limits** (Peng et al.) | CFMA (Functional Manifold) |
| `e640c1ba69f268a7a1eaa19552dbbc78cdc4cc9f` | 2024 | **CoT Insufficiency** (Zubic et al.) | CFMA (Functional Manifold) |
| `669c7f363d9230263b29f8af58b195c8dbd11a15` | 2026 | **Statelessness** (Tang & Xie) | CFMA (Functional Manifold) |

### Bucket E: Technical Precedents (The "Mechanism" Sources)
*Existing methods that provide valid components for proposed spinoffs.*

| Paper ID | Year | Mechanism | Potential Transfer/Collision |
| :--- | :--- | :--- | :--- |
| `179237bc5fb46f34ef936b1552600bf3521c3c64` | 2023 | Differentiable Tree Operations | Collision for CFMA (Discrete vs. Continuous). |
| `cfa00f9997c4eef5caef44788e2bb88b4efb7240` | 2025 | Neuro-symbolic WFA (RetoMaton) | Collision for CFMA (Automata vs. Manifold). |
| `e05c8b2c7be4c39f1efb812fa9fc79135d73c93e2` | 2025 | Neural ODE / Differentiable Hidden State | Mechanism source for CFMA. |
| `cb22e431201f0753e058726fdf058e8f07404eed` | 2024 | Modular Differentiable Networks | Theoretical support for functional modularity. |

---

## 2. Synthesized Research Gaps

| Gap ID | Description | Primary Evidence | Lead Subagent |
| :--- | :--- | :--- | :--- |
| **GAP-01** | **Semantic Misalignment**: Incompatibility between local (CNN) and global (Transformer) feature spaces during fusion. | DBAANet (2025), BGSC-Net (2026) | `subagent_01` |
| **GAP-02** | **Compositionality Gap**: Inability to compose functions over large domains due to communication complexity/statelessness. | Peng (2024), Zubic (2024), Tang & Xie (2026) | `subagent_02` |
| **GAP-03** | **Scaling-Bias Tension**: Architectural efficiency vs. parameter scaling efficacy. | Tay et al. (2022) | Cross-investigator |

---

## 3. Subagent Contribution Matrix

| Subagent | Research Zone | Primary Role | Key Synthesis Output |
| :--- | :--- | :--- | :--- |
| `investigator_01_experiments_subagent_01` | `citation_ancestry` | Lineage Mapper | Identified **Semantic Misalignment** as the primary hybrid bottleneck. |
| `investigator_01_experiments_subagent_02` | `open_problem_discovery` | Opportunity Synthesizer | Identified **Function Compositionality** and **Statelessness** as fundamental limits. |

---

## 4. Spinoff Candidate Anchors

| Candidate Title | Primary Gap | Core Mechanism | Confidence |
| :--- | :--- | :--- | :--- |
| **Synchronous Semantic-Spatial Alignment (S3A)** | GAP-01 | Cross-scale contrastive learning for latent manifold synchronization. | Medium |
| **Continuous Functional Manifold Augmentation (CFMA)** | GAP-02 | Neural ODE-based continuous latent state for non-discrete function tracking. | Medium |