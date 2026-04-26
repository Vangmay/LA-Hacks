# Papers

## Seed Paper
- ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Title: Attention is All you Need
- Year: 2017
- Source: arXiv:1706.03762
- Note: Foundational Transformer paper. Replaces recurrence/convolutions with pure attention.

## Foundational Ancestry

- **LSTM** (1997, `2e9d221c206e9503ceb452302d68d10e293f2a10`): Core recurrent mechanism that Transformer aims to replace.
- **Attention-based NMT** (2014, `fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5`): Introduced attention as an auxiliary mechanism to RNNs; Transformer makes it the primary mechanism.
- **Convolutional Seq2Seq** (2017, `43428880d75b3a14257c3ee9bda054e61eb869c0`): An alternative to recurrence using convolutions; Transformer dispenses with these too.
- **Layer Normalization** (2016, `97fb4e3d45bb098e27e0071448b6152217bd35a5`): Essential stability mechanism used in Transformer architectures.


## Efficient Mechanism Evolutions

- **SAMSA** (2024, `bca796f85c77f21df1d8c9c48c9b24cc94bc895f`): Uses differentiable sampling without replacement to select important tokens, achieving linear complexity.
- **Resformer** (2023, `4abbfa53ac8f5e408806a415dc462676f25e2fa5`): Combines quadratic linear transformation (LT module) with fully sparse self-attention for $O(n)$ complexity.
- **Raptor-T** (2024, `c3c469b8d3392aa1117e1d82bd3357d2c12d87ce`): Focuses on system-level efficiency (fused MHA, asynchronous processing) for variable-length sparse attention.
- **TianXing** (2024, `dc6d1ad3d2fbcd354be83f71164ce0b36bae9ba1`): Linear complexity with explicit attention decay.
- **Hybrid MixLayer** (2025, `500cb23dfd9a5c898ae9d465d6f655f839882268`): Uses interpolation-based MixLayer to enhance unimodal features before sparse cross-modal interaction.


## Mechanism-level Equivalences & Hybrids

- **Unified Framework (Head-Count Theorem)** (2025, `83485e76d4cfebcdbb277b5c4f6044285b58b41c`): Proves that $H$ heads in a factorized framework can represent a linear SSM whose lag operators span a $k$-dimensional subspace where $H=k$.
- **A2Mamba** (2025, `db1c43397c000b35fe172c67bb20fe8102777dab`): Uses attention maps to spatially aggregate SSM hidden states (cross-attention variant).
- **CrossMamba** (2024, `51b3291dd8250b8e70142ec5330cde50aee9cbc5`): Uses clues to generate queries for Mamba's hidden attention, emulating cross-attention.
- **GFSSM/Attention Sink** (2024, `1c80e8bf4606c7a4b7a91a10faaab3fb82a3ed91`): Incorporates attention-sink mechanisms into SSMs to bridge the architectural gap.
- **FAST** (2026, `0c604713a9bd3839a8cb385cfdd20ad1a00e4ba0`): Synergistic temporal attention + Mamba-based spatial modeling.
