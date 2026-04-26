# Proposal Seeds



## Proposal Seed: Mechanistic Investigation of Attention-driven Denoising in Transformers

## Proposal Seed: Mechanistic Investigation of Attention-driven Denoising in Transformers

- Status: promising
- Originating taste: protocol_forensics
- Seed-paper hook: Transformer-LSTM hybrid robustness in fNIRS noise conditions.
- Evidence trigger: ded071c5a90e82d5e1c81602f7dfb37350353812 showing Transformer (80.09%) significantly outperforms SVM (45.2%) under noise; Tiberi et al. (2024) theoretical 'denoising paths'.
- Candidate novelty: Bridging the gap between the theoretical 'denoising paths' (statistical mechanics/GP limit) and the practical, adaptive behavior of attention heads in real-world noisy signals. Specifically, testing if attention heads act as adaptive, frequency- or segment-selective filters that track the signal's instantaneous SNR, rather than relying on explicit momentum-based augmentations (Maitra, 2026).
- Technical mechanism: Controlled signal perturbation experiments (varying SNR, frequency shifts, and additive Gaussian noise) paired with attention weight saliency analysis to determine if attention heads 'mask' noisy frequencies/segments by quantifying the correlation between attention saliency and ground-truth signal SNR.
- Closest prior-work collision: Tiberi et al. (2024) (theoretical denoising paths); Maitra (2026) (momentum-based filtering).
- Closest future-work collision: Hybrid architectures that explicitly integrate signal processing filters with attention.
- Minimum validation: Synthetic signal generation (e.g., sinusoids + noise) + Transformer training/inference + correlation analysis between attention maps and ground-truth signal components.
- Falsification risk: If attention weights are found to be invariant to noise levels or if performance gains are purely due to the LSTM component's temporal smoothing/integration.
- Why this is not generic: It targets the specific *mechanism* of attention-based filtering and seeks to map theoretical 'denoising paths' to empirical, adaptive filter behavior in standard architectures.
- Confidence: medium
- Required next search: 'attention saliency signal-to-noise ratio' or 'empirical attention denoising mechanism'
- Status: promising
- Originating taste: protocol_forensics
- Seed-paper hook: Transformer-LSTM hybrid robustness in fNIRS noise conditions.
- Evidence trigger: ded071c5a90e82d5e1c81602f7dfb37350353812 showing Transformer (80.09%) significantly outperforms SVM (45.2%) under noise; Tiberi et al. (2024) theoretical 'denoising paths'.
- Candidate novelty: Bridging the gap between the theoretical 'denoising paths' (statistical mechanics/GP limit) and the practical, adaptive behavior of attention heads in real-world noisy signals. Specifically, testing if attention heads act as adaptive, frequency- or segment-selective filters that track the signal's instantaneous SNR.
- Technical mechanism: Controlled signal perturbation experiments (varying SNR, frequency shifts, and additive Gaussian noise) paired with attention weight saliency analysis to determine if attention heads 'mask' noisy frequencies/segments by quantifying the correlation between attention saliency and ground-truth signal SNR.
- Closest prior-work collision: Tiberi et al. (2024) (theoretical denoising paths); standard adversarial robustness papers for Transformers.
- Closest future-work collision: Hybrid architectures that explicitly integrate signal processing filters with attention.
- Minimum validation: Synthetic signal generation (e.g., sinusoids + noise) + Transformer training/inference + correlation analysis between attention maps and ground-truth signal components.
- Falsification risk: If attention weights are found to be invariant to noise levels or if performance gains are purely due to the LSTM component's temporal smoothing/integration.
- Why this is not generic: It targets the specific *mechanism* of attention-based filtering and seeks to map theoretical 'denoising paths' to empirical, adaptive filter behavior.
- Confidence: medium
- Required next search: 'attention saliency signal-to-noise ratio' or 'empirical attention denoising mechanism'
