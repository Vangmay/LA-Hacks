# Findings

## Finding: Associative Recall Optimization and Scaling Friction in SSMs
- Claim: Modern recurrent models (SSMs) like Mamba suffer from high sensitivity to learning rate and width/depth scaling ratios compared to Transformers on Associative Recall (AR) tasks.
- Confidence: high
- Evidence:
  - 91fd141738858eff0f31ae5db208f269e4d3f982 (Revisiting associative recall in modern recurrent models, 2025)
- Why it matters: This suggests that the 'inductive bias' of SSMs isn't necessarily absent, but it is significantly harder to activate via standard SGD. Hybrid research should focus on 'restoration' of this inductive bias through stabilized token-mixing strategies or specialized LR schedules rather than just structural attention.
- Caveat: The paper is extremely recent (2025); the findings on Mamba's scaling benefits in width vs depth may still be undergoing larger-scale verification.

## Finding: Local-Attention as a Necessary 'Bandage' for Linear Recurrences
- Claim: Current state-of-the-art linear recurrences (e.g., Hawk) require the re-introduction of local attention (e.g., Griffin) to match Transformer performance on downstream tasks and achieve robust sequence extrapolation.
- Confidence: high
- Evidence:
  - d53fe76bd2795a19ddf52d012917782f6f6f2c1e (Griffin, 2024)
- Why it matters: This confirms a persistent technical disagreement: while pure SSMs are theoretically sufficient for long-range tasks, empirical results suggest they still lack the 'extrapolation' and 'precision' inductive bias found in attention mechanisms. This 'hybrid bandage' approach is currently the dominant fix for scaling hurdles.
- Caveat: The necessity of attention might be tied to our current optimization methods (SGD) rather than architectural impossibility, as suggested by the optimization friction finding.

## Finding: Coverage-Selection Disconnect in SSM Reasoning
- Claim: While Mamba-2 hybrids can improve candidate coverage (pass@k) in recursive reasoning tasks, they do not necessarily improve top-1 selection (pass@1) relative to Transformers, suggesting an inductive bias gap in 'final selection' logic.
- Confidence: medium
- Evidence:
  - 45ecf6033663a38e661c2ceb9c1225413a6aba71 (Tiny Recursive Reasoning with Mamba-2 Attention Hybrid, 2026)
- Why it matters: It challenges the assumption that 'more reasoning capacity' equals better results. SSM-hybrids may be better at exploration/recall-like reasoning but lack the sharp 'point-selection' bias of global attention layers, identifying a specific architectural ceiling.
- Caveat: The study context is 'latent recursion' and 'tiny networks' (7M parameters), so results may vary with parameter scaling.
