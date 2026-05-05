"""Chronometric Lorentz-contortion layer for NanoWM.

This is a constrained latent-dynamics primitive, not a physics claim. It turns
temporal token streams into a 4D event manifold, applies a learned phase-locked
4x4 response tensor, projects the contortion force orthogonal to the time-like
velocity, and maps the integrated event update back into model hidden space.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict

import torch
import torch.nn as nn


LOG_PHASE_LAMBDA = 3722.0 / 2705.0
CHRONOMETRIC_MODES = {"audit", "residual_once", "residual_each", "branch_rollout"}


@dataclass(frozen=True)
class ChronometricConfig:
    mode: str = "audit"
    c: float = 1.0
    mass: float = 1.0
    dtau: float = 1.0
    tau_c: float = 1.0
    t0: float = 1.0
    beta: float = 0.0
    phase_eps: float = 1.0
    phase_xi: float = 1.0
    residual_scale: float = 0.01
    potential_families: int = 16
    init_std: float = 0.02


@dataclass(frozen=True)
class ChronometricOutput:
    update: torch.Tensor
    event: torch.Tensor
    velocity: torch.Tensor
    external_force: torch.Tensor
    contortion_force: torch.Tensor
    total_force: torch.Tensor
    next_event: torch.Tensor
    outcome_y: torch.Tensor
    family_probs: torch.Tensor
    branch_direction: torch.Tensor
    k_tensor: torch.Tensor
    theta: torch.Tensor
    invariant: torch.Tensor
    orthogonality: torch.Tensor
    raw_orthogonality: torch.Tensor


def log_time_phase(
    tau: torch.Tensor,
    *,
    tau_c: float = 1.0,
    t0: float = 1.0,
    beta: float = 0.0,
) -> torch.Tensor:
    """Scale-periodic phase used by the chronometric tensor modulation."""
    if tau_c < 0:
        raise ValueError("tau_c must be non-negative")
    if t0 <= 0:
        raise ValueError("t0 must be positive")
    if torch.any(tau + tau_c <= 0):
        raise ValueError("tau + tau_c must be positive")
    return (2.0 * math.pi / math.log(LOG_PHASE_LAMBDA)) * torch.log((tau + tau_c) / t0) + beta


def minkowski_dot(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Dot product with signature (-,+,+,+)."""
    return -a[..., 0] * b[..., 0] + (a[..., 1:] * b[..., 1:]).sum(dim=-1)


def normalize_spatial_branch(n: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """Normalize only the spatial branch components and preserve n_time."""
    spatial = n[..., 1:]
    spatial_norm = torch.linalg.vector_norm(spatial, dim=-1, keepdim=True).clamp_min(eps)
    return torch.cat([n[..., :1], spatial / spatial_norm], dim=-1)


def normalize_timelike_velocity(raw_spatial: torch.Tensor, c: float = 1.0) -> torch.Tensor:
    """Create u=(gamma*c, v_x, v_y, v_z) with Minkowski norm -c^2."""
    spatial = torch.tanh(raw_spatial) * c
    spatial_sq = (spatial * spatial).sum(dim=-1, keepdim=True)
    gamma_c = torch.sqrt(c * c + spatial_sq)
    return torch.cat([gamma_c, spatial], dim=-1)


def project_orthogonal_to_velocity(
    velocity: torch.Tensor,
    response: torch.Tensor,
    *,
    c: float = 1.0,
) -> torch.Tensor:
    """Apply P = I + u u_lower / c^2 to enforce u_mu F^mu = 0."""
    dot = minkowski_dot(velocity, response).unsqueeze(-1)
    return response + (dot / (c * c)) * velocity


class ChronometricContortionLayer(nn.Module):
    """Differentiable 4D event-geometry module for temporal NanoWM tokens."""

    def __init__(self, hidden_size: int, config: ChronometricConfig | None = None):
        super().__init__()
        self.config = config or ChronometricConfig()
        if self.config.mode not in CHRONOMETRIC_MODES:
            raise ValueError(f"chronometric mode must be one of {sorted(CHRONOMETRIC_MODES)}, got {self.config.mode}")
        if self.config.potential_families <= 0:
            raise ValueError("potential_families must be positive")

        self.event_head = nn.Linear(hidden_size, 4)
        self.velocity_head = nn.Linear(hidden_size, 3)
        self.external_force_head = nn.Linear(hidden_size, 4)
        self.context_force_head = nn.Linear(hidden_size, 4)
        self.k_head = nn.Linear(hidden_size, 3 * 4 * 4)
        self.branch_head = nn.Linear(hidden_size, 4)
        self.family_head = nn.Linear(hidden_size, self.config.potential_families)
        self.family_basis = nn.Parameter(torch.empty(self.config.potential_families, 4))
        self.outcome_head = nn.Linear(4, 1)
        self.update_proj = nn.Linear(4 + 4 + 4 + 4 + self.config.potential_families + 1, hidden_size)
        self.last_metrics: Dict[str, torch.Tensor] = {}
        self.last_losses: Dict[str, torch.Tensor] = {}

        self.reset_parameters()

    def reset_parameters(self) -> None:
        std = self.config.init_std
        for module in (
            self.event_head,
            self.velocity_head,
            self.external_force_head,
            self.context_force_head,
            self.k_head,
            self.branch_head,
            self.family_head,
            self.outcome_head,
            self.update_proj,
        ):
            nn.init.normal_(module.weight, std=std)
            nn.init.zeros_(module.bias)
        nn.init.normal_(self.family_basis, std=std)

    def _check_context(self, tokens: torch.Tensor, context: torch.Tensor | None) -> torch.Tensor | None:
        if context is None:
            return None
        if context.shape != tokens.shape:
            raise ValueError(
                f"action_context must match tokens shape {tuple(tokens.shape)}, got {tuple(context.shape)}"
            )
        return context.to(device=tokens.device, dtype=tokens.dtype)

    def _check_branch_direction(
        self,
        tokens: torch.Tensor,
        branch_direction: torch.Tensor | None,
    ) -> torch.Tensor | None:
        if branch_direction is None:
            return None
        batch, frames, _ = tokens.shape
        if branch_direction.ndim == 2:
            branch_direction = branch_direction.unsqueeze(1).expand(batch, frames, 4)
        if branch_direction.shape != (batch, frames, 4):
            raise ValueError(
                f"branch_direction must be [B,T,4] or [B,4], got {tuple(branch_direction.shape)}"
            )
        return branch_direction.to(device=tokens.device, dtype=tokens.dtype)

    def _compute_geometry(
        self,
        tokens: torch.Tensor,
        *,
        action_context: torch.Tensor | None = None,
        branch_direction: torch.Tensor | None = None,
    ) -> ChronometricOutput:
        if tokens.ndim != 3:
            raise ValueError(f"expected [B,T,D] tokens, got shape {tuple(tokens.shape)}")

        action_context = self._check_context(tokens, action_context)
        supplied_branch = self._check_branch_direction(tokens, branch_direction)

        cfg = self.config
        batch, frames, _ = tokens.shape
        dtype = tokens.dtype
        device = tokens.device

        event = self.event_head(tokens)
        velocity = normalize_timelike_velocity(self.velocity_head(tokens), c=cfg.c)
        external_force = self.external_force_head(tokens)
        if action_context is not None:
            external_force = external_force + self.context_force_head(action_context)

        k0, kc, ks = self.k_head(tokens).reshape(batch, frames, 3, 4, 4).unbind(dim=2)
        tau = torch.arange(frames, device=device, dtype=torch.float32).add_(1.0)
        theta = log_time_phase(tau, tau_c=cfg.tau_c, t0=cfg.t0, beta=cfg.beta).to(dtype=dtype)
        theta = theta.view(1, frames, 1, 1)
        k_tensor = k0 + cfg.phase_eps * kc * torch.cos(theta) + cfg.phase_xi * ks * torch.sin(theta)

        family_logits = self.family_head(tokens)
        family_probs = torch.softmax(family_logits, dim=-1)
        family_direction = torch.matmul(family_probs, self.family_basis.to(dtype=dtype))
        if supplied_branch is None:
            branch_direction = normalize_spatial_branch(self.branch_head(tokens) + family_direction)
        else:
            branch_direction = normalize_spatial_branch(supplied_branch)

        raw_response = torch.einsum("btij,btj->bti", k_tensor, branch_direction)
        speed_sq = (velocity[..., 1:] * velocity[..., 1:]).sum(dim=-1, keepdim=True)
        raw_contortion = cfg.mass * speed_sq * raw_response
        raw_orthogonality = minkowski_dot(velocity, raw_contortion)
        contortion_force = project_orthogonal_to_velocity(
            velocity,
            raw_contortion,
            c=cfg.c,
        )
        total_force = external_force + contortion_force
        momentum = cfg.mass * velocity
        next_momentum = momentum + cfg.dtau * total_force
        next_event = event + cfg.dtau * (next_momentum / cfg.mass)
        outcome_y = self.outcome_head(next_event)
        invariant = minkowski_dot(velocity, velocity) + cfg.c * cfg.c
        orthogonality = minkowski_dot(velocity, contortion_force)

        update_features = torch.cat(
            [
                next_event - event,
                velocity,
                external_force,
                contortion_force,
                family_probs,
                outcome_y,
            ],
            dim=-1,
        )
        update = self.update_proj(update_features)

        return ChronometricOutput(
            update=update,
            event=event,
            velocity=velocity,
            external_force=external_force,
            contortion_force=contortion_force,
            total_force=total_force,
            next_event=next_event,
            outcome_y=outcome_y,
            family_probs=family_probs,
            branch_direction=branch_direction,
            k_tensor=k_tensor,
            theta=theta,
            invariant=invariant,
            orthogonality=orthogonality,
            raw_orthogonality=raw_orthogonality,
        )

    def _store_diagnostics(self, output: ChronometricOutput) -> None:
        self.last_losses = {
            "invariant_norm": output.invariant.square().mean(),
            "orthogonality": output.orthogonality.square().mean(),
            "raw_orthogonality": output.raw_orthogonality.square().mean(),
        }

        with torch.no_grad():
            entropy = -(output.family_probs * output.family_probs.clamp_min(1e-8).log()).sum(dim=-1)
            self.last_metrics = {
                "chronometric_invariant_abs_mean": output.invariant.abs().mean().detach(),
                "chronometric_orthogonality_abs_mean": output.orthogonality.abs().mean().detach(),
                "chronometric_raw_orthogonality_abs_mean": output.raw_orthogonality.abs().mean().detach(),
                "chronometric_external_force_rms": output.external_force.square().mean().sqrt().detach(),
                "chronometric_contortion_force_rms": output.contortion_force.square().mean().sqrt().detach(),
                "chronometric_force_rms": output.total_force.square().mean().sqrt().detach(),
                "chronometric_outcome_y_mean": output.outcome_y.mean().detach(),
                "chronometric_potential_entropy": entropy.mean().detach(),
                "chronometric_theta_mean": output.theta.mean().detach(),
            }

    def score_branch(
        self,
        tokens: torch.Tensor,
        branch_direction: torch.Tensor,
        *,
        action_context: torch.Tensor | None = None,
    ) -> ChronometricOutput:
        """Score a supplied branch direction without applying a token residual."""
        output = self._compute_geometry(
            tokens,
            action_context=action_context,
            branch_direction=branch_direction,
        )
        self._store_diagnostics(output)
        return output

    def forward(
        self,
        tokens: torch.Tensor,
        *,
        action_context: torch.Tensor | None = None,
        branch_direction: torch.Tensor | None = None,
        apply_residual: bool = True,
    ) -> torch.Tensor:
        """Apply event-space contortion to temporal tokens.

        Args:
            tokens: [B, T, D] temporal hidden states. In NanoWM this is usually
                [batch * spatial_patches, frames, hidden_size].
            action_context: optional shifted action/context embedding [B, T, D].
            branch_direction: optional planner-supplied branch direction [B,T,4].
            apply_residual: when false, only diagnostics are updated.

        Returns:
            Tokens with a small residual chronometric update applied.
        """
        output = self._compute_geometry(
            tokens,
            action_context=action_context,
            branch_direction=branch_direction,
        )
        self._store_diagnostics(output)
        if not apply_residual:
            return tokens
        return tokens + self.config.residual_scale * output.update
