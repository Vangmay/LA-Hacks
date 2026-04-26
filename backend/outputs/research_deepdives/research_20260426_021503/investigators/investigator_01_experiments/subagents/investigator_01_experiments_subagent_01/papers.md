# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (This is the seed paper)
- Why it matters: Introduced the Transformer architecture, which relies entirely on self-attention mechanisms, dispensing with recurrence and convolutions. It is the foundational work for modern LLMs.
- Caveat: N/A


## Paper: Neural Machine Translation by Jointly Learning to Align and Translate

- Paper ID: fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5
- Year: 2014
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Provides the foundational attention mechanism that the Transformer refines and removes recurrence from.
- Why it matters: One of the earliest works to introduce an attention mechanism to bridge encoder and decoder in NMT.
- Caveat: Uses RNNs for the core sequence processing, unlike the Transformer.


## Paper: Efficient Seizure Detection by Complementary Integration of Convolutional Neural Network and Vision Transformer

- Paper ID: 23a109f0e58029f7a69694f2ff795129095cdc5b
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Represents the modern trend of hybridizing CNNs with Transformers to compensate for lack of local inductive bias in pure attention models.
- Why it matters: Demonstrates that CNNs capture local inductive bias (crucial for EEG/signal signals) while ViT handles long-range dependencies.
- Caveat: Specific to EEG signal processing.


## Paper: Dynamic Multi-Scale Network for Dual-Pixel Images Defocus Deblurring with Transformer

- Paper ID: 00604535b29dbb2ea2af9e3d49abb0d26b0a8c27
- Year: 2022
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Supports the hypothesis that CNN inductive biases can improve Transformer performance in data-scarce scenarios.
- Why it matters: Explicitly claims that 'the inductive bias of CNN enables transformer to extract more robust features without relying on a large amount of data.'
- Caveat: Application is specific to defocus deblurring.


## Paper: ECViT: Efficient Convolutional Vision Transformer with Local-Attention and Multi-scale Stages

- Paper ID: 00796ad8bd3a7eb0bfa39085bc9b3c2e3a82dc07
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Represents the state-of-the-art trend of incorporating CNN inductive biases (locality, translation invariance) into Transformers to improve efficiency and data requirements.
- Why it matters: Directly addresses the 'inductive bias gap' by using convolutional operations to extract low-level features before transformer processing.
- Caveat: Focus is on vision tasks.


## Paper: Scaling Laws vs Model Architectures: How does Inductive Bias Influence Scaling?

- Paper ID: 6edccbd83a9aae204785d4821f97855677c33866
- Year: 2022
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Directly addresses the interplay between architecture/inductive bias and scaling laws.
- Why it matters: Shows that architecture choice is critical for scaling and that the 'best' architecture can change depending on the scale (data/parameter size). This challenges the notion that one architecture (like the Transformer) is universally optimal across all scales.
- Caveat: Studies a specific set of ten architectures; results may not generalize to all possible architectural paradigms.


## Paper: CTLE: A Hybrid CNN-Transformer-LSTM Equalizer with Multi-Head Attention for Low-BER Signal Recovery in Multipath Fading Channel

- Paper ID: 0572ee725c139b07cd02695751d641c26b068ae8
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Shows the evolution into triple-hybrid architectures (CNN + Transformer + LSTM) to address diverse temporal and spatial dependencies.
- Why it matters: Demonstrates that the 'hybridization' trend is moving beyond binary (CNN-Transformer) to multi-component models to capture local, sequential, and global features simultaneously.
- Caveat: Domain-specific to signal processing/equalization.


## Paper: FUSIONSEGNET: A Deep Learning Framework For Accurate And Explainable Skin Disease Classification Using Multi-Model Integration

- Paper ID: 00459840cecd4a8b520e95fdb22d89af06583cc2
- Year: 2026
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Represents a 'parallel branch' hybrid approach where multiple feature extraction branches (ResNet50 and ViT) are run in parallel and fused via attention.
- Why it matters: It uses 'attention-guided fusion' to combine multi-scale features from CNN and Transformer branches, demonstrating how attention can act as the 'integrator' between disparate inductive biases.
- Caveat: Focused on medical image classification.


## Paper: DBAANet: Dual-Branch Attention Aggregation Network for Medical Image Segmentation

- Paper ID: 31116ee2b039d1c2e5dc71b64b9a240b416e663b
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Provides direct evidence of a critical technical failure mode in hybrid architectures.
- Why it matters: Explicitly identifies 'semantic misalignment between local CNN features and global Transformer representations' as a primary cause of inefficient fusion and boundary detail loss.
- Caveat: Context is medical image segmentation.
