# Findings



## Finding: Structural Vulnerabilities and Trustworthiness Risks in Transformers

- Claim: Transformer architectures exhibit recurring structural vulnerabilities that impact their reliability in safety-critical domains such as medicine, robotics, and scientific computing.
- Confidence: medium
- Evidence:
  - 96c6404f0f38b50299017be181a50d6c51e6480d: "In Transformer We Trust? A Perspective on Transformer Architecture Failure Modes" (2026)
- Why it matters: This identifies a shift from purely performance-driven metrics to reliability-driven requirements. It suggests that Transformer failure modes are not just task-specific but are tied to the architecture's structural properties, affecting interpretability, robustness, and fairness across diverse domains.
- Caveat: The evidence stems from a review paper; specific mechanistic causes for these vulnerabilities require further empirical or theoretical investigation.


## Finding: Differentiation of Attention Stability from Existing XAI and Training Methods

- Claim: The proposed 'Attention Stability Score' is distinct from current 'Attention Importance' (XAI) and 'Attention Entropy' (Training Stability) research.
- Confidence: high
- Evidence:
  - f88c5105e8806105d792d077527ad32bcdd973e7: Focuses on word *importance* for interpretability.
  - 385c363ea8e450f362d389f401beaeb5b42a0022: Focuses on attention *entropy* to prevent collapse during *training*.
- Why it matters: This clarifies the research gap. While current literature uses attention properties to explain *what* the model does or *how* to train it, there is a lack of research using attention *fluctuation/variance* as a real-time diagnostic tool to assess model *reliability* under environmental/domain-specific noise during deployment.
- Caveat: Further empirical validation is needed to ensure that attention weight variance is a reliable proxy for task-level error in the presence of specific noise models.
