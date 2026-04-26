# Papers



## Paper: Vision Mamba: A Comprehensive Survey and Taxonomy

- Paper ID: cc142aa425bff39a9385154d34485dc13ce3cf95
- Year: 2024
- Source bucket: bulk_search
- Found by: "state space models" + "control theory" + "deep learning"
- Relation to seed: Follow-up/Survey on architectural shifts from Transformers to SSMs.
- Why it matters: Establishes the modern SOTA for SSMs (Mamba) as a hardware-aware alternative to Transformers, explicitly citing control theory roots.
- Caveat: Primarily focuses on vision; may gloss over pure signal processing inductive biases in favor of architectural performance.


## Paper: Uncertainty Representations in State-Space Layers for Deep Reinforcement Learning

- Paper ID: b10e24c77899616e25c7033de4e8f474cd9b1b4e
- Year: 2024
- Source bucket: relevance_search
- Found by: "associative scan" Kalman Filter differentiable "state space model"
- Relation to seed: Direct collision/corroboration for DK-Mamba proposal.
- Why it matters: Demonstrates that the Kalman Filter update can be formulated as a parallel scan (associative operator), enabling logarithmic scaling with sequence length. This preserves the hardware efficiency of modern SSMs while adding probabilistic filtering. It validates that uncertainty reasoning improves performance in partially observable environments.
- Caveat: Focused on Reinforcement Learning; the transfer to Large Language Models or purely generative sequence tasks remains a high-value gap.
