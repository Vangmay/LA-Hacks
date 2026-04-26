"""Offline checks for atom-grounded PoC scaffold generation.

Run with:
PYTHONPATH=backend python backend/scripts/test_poc_scaffold_generator.py
"""
from __future__ import annotations

import asyncio
import ast
from types import SimpleNamespace

from agents.base import AgentContext
from config import settings
from models import AtomImportance, ResearchAtom, ResearchAtomType, SourceSpan
from poc.agents.scaffold_generator import ScaffoldGeneratorAgent


class _FakeScaffoldClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        system = kwargs["messages"][0]["content"]
        content = "# fallback\n"
        if "research paper's method" in system:
            content = """```python
# Implements algorithm atom_002: Pseudocode for stochastic gradient computation using a custom estimator
import torch


def stochastic_gradient_estimator(phi, dataset, eps_sampler, zeta_sampler, f_phi, g_phi, h_phi, L=1):
    # See selected atom source excerpt: initialize and average stochastic gradients.
    grad = torch.zeros_like(phi)
    for _ in range(L):
        x = dataset[_ % len(dataset)]
        eps = eps_sampler()
        zeta = zeta_sampler()
        z = g_phi(eps, x)
        theta = h_phi(zeta)
        objective = f_phi(x, z, theta)
        (step_grad,) = torch.autograd.grad(objective, phi, retain_graph=True)
        grad = grad + step_grad / L
    return grad


def main():
    phi = torch.tensor(1.0, requires_grad=True)
    data = [torch.tensor(2.0)]
    sampler = lambda: torch.tensor(0.0)
    f_phi = lambda x, z, theta: phi * (x + z + theta)
    identity = lambda noise, x=None: noise if x is None else x + noise
    print(stochastic_gradient_estimator(phi, data, sampler, sampler, f_phi, identity, lambda noise: noise))


if __name__ == "__main__":
    main()
```"""
        elif "pytest test file" in system:
            content = """```python
import torch
from implementation import stochastic_gradient_estimator
from results_logger import save_results


def test_estimator_returns_gradient_tensor():
    phi = torch.tensor(1.0, requires_grad=True)
    data = [torch.tensor(2.0)]
    sampler = lambda: torch.tensor(0.0)
    f_phi = lambda x, z, theta: phi * (x + z + theta)
    identity = lambda noise, x=None: noise if x is None else x + noise
    grad = stochastic_gradient_estimator(phi, data, sampler, sampler, f_phi, identity, lambda noise: noise)
    assert grad.shape == phi.shape
    save_results({"claim_id": "atom_002", "gradient_value": float(grad)})
```"""
        elif "requirements.txt" in system:
            content = "```text\ntorch\npytest\n```"
        elif "README" in system or "README" in kwargs["messages"][1]["content"]:
            content = "# PoC Scaffold\n\nTests atom_002 directly.\n"

        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


async def _run() -> None:
    atom = ResearchAtom(
        atom_id="atom_002",
        paper_id="1312.6114",
        atom_type=ResearchAtomType.ALGORITHM,
        text="Pseudocode for stochastic gradient computation using a custom estimator",
        section_id="sec_full_vb",
        section_heading="Full VB",
        source_span=SourceSpan(
            paper_id="1312.6114",
            section_id="sec_full_vb",
            raw_excerpt=(
                "Require phi. g <- 0. For l is 1 to L: x <- random draw from dataset X; "
                "eps <- random draw from p(eps); zeta <- random draw from p(zeta); "
                "g <- g + 1/L grad_phi f_phi(x, g_phi(eps, x), h_phi(zeta)). Return g."
            ),
            match_confidence=1.0,
        ),
        extraction_confidence=0.95,
        importance=AtomImportance.HIGH,
    )
    paper_metadata = {
        "title": "Auto-Encoding Variational Bayes",
        "abstract": "We introduce stochastic variational inference and learning.",
        "sections": [
            {"title": "Abstract", "content": "Variational auto-encoder overview."},
            {"title": "Introduction", "content": "AEVB and VAE motivation."},
            {"title": "Method", "content": "General lower-bound derivation."},
            {
                "title": "Full VB",
                "content": (
                    "The estimator only depends on samples from p(eps) and p(zeta). "
                    "Pseudocode for computing a stochastic gradient using our estimator: "
                    "Require phi; g <- 0; sample x, eps, zeta; accumulate grad_phi f_phi."
                ),
            },
        ],
    }
    poc_spec = {
        "claim_id": "atom_002",
        "success_criteria": [],
        "failure_criteria": [],
    }

    client = _FakeScaffoldClient()
    result = await ScaffoldGeneratorAgent(client=client).run(
        AgentContext(
            job_id="test",
            atom=atom,
            extra={"poc_spec": poc_spec, "paper_metadata": paper_metadata},
        )
    )

    assert result.status == "success", result.error
    files = result.output["scaffold_files"]
    assert "```" not in files["implementation.py"]
    assert "```" not in files["test_harness.py"]
    assert "```" not in files["requirements.txt"]
    assert "stochastic_gradient_estimator" in files["implementation.py"]
    assert "class VAE" not in files["implementation.py"]
    ast.parse(files["implementation.py"])
    ast.parse(files["test_harness.py"])

    impl_call = client.calls[0]
    impl_system = impl_call["messages"][0]["content"]
    impl_user = impl_call["messages"][1]["content"]
    assert impl_call["model"] == settings.poc_scaffold_model
    assert impl_call["extra_body"]["reasoning_effort"] == settings.poc_scaffold_reasoning_effort
    assert "selected research atom is the implementation target" in impl_system
    assert "not a full VAE class" in impl_system
    assert "Selected atom source excerpt" in impl_user
    assert "g <- g + 1/L" in impl_user
    assert "## Full VB" in impl_user

    print("poc scaffold generator prompt checks ok")


if __name__ == "__main__":
    asyncio.run(_run())
