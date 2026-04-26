# Proposal Seeds



## Proposal Seed: Windowed-Attention for Local-Global Scaling

- Status: speculative
- Originating taste: disagreement_detector
- Seed-paper hook: f1a19290eb68ae169a2fd86e279e5025f71ffc8a (Bridging local and global representations)
- Evidence trigger: The existence of work specifically focused on 'bridging' local and global representations for depth completion implies that standard self-attention mechanisms fail to adequately capture scale-invariant spatial features needed for dense prediction.
- Candidate novelty: A mechanism that explicitly models the tension between intra-window (local/high-frequency) and inter-window (global/semantic) attention to improve spatial precision in dense tasks.
- Technical mechanism: A dual-scale attention module with a learnable gating mechanism that dynamically weights high-resolution intra-window attention against low-resolution inter-window global context.
- Closest prior-work collision: Swin Transformer (uses shifted windows, but focuses on hierarchical scaling rather than the specific local-global representation trade-off for dense prediction).
- Closest future-work collision: Unified scale-aware attention models.
- Minimum validation: Evaluate on NYU Depth V2 or KITTI depth completion benchmarks against Swin and standard ViT.
- Falsification risk: If the gating mechanism does not improve performance on tasks requiring fine-grained spatial detail compared to standard global attention.
- Why this is not generic: It targets a specific identified failure mode (representation bridging) in spatial transduction tasks rather than just 'making attention better'.
- Confidence: low
- Required next search: 'limitations of Swin Transformer in spatial precision' and 'Transformer local-global representation trade-offs'
