# Chronometric Contortion Foundation

This repo now treats the Chronometric Lorentz-Contortion scaffold as a NanoWM
model primitive, not as an ARC-side planning note.

The implementation lives in `src/models/chronometric_contortion.py` and is
enabled from the model configs under `model.chronometric`.

## Installed Equations

The layer maps temporal hidden tokens into a learned 4D event system:

- event state: `x^mu = (t, x, y, z)`
- time-like velocity: `u^mu = (gamma c, v_x, v_y, v_z)`
- momentum: `p^mu = m u^mu`
- phase-locked tensor: `K(tau) = K0 + eps Kc cos(theta) + xi Ks sin(theta)`
- log-time phase: `theta(tau) = 2pi / ln(3722/2705) * ln((tau + tau_c) / T0) + beta`
- raw response: `r^alpha = K^alpha_beta n^beta`
- projected contortion: `F_cont^mu = m |v|^2 P^mu_alpha(u) r^alpha`
- projector: `P = I + u u_lower / c^2`

The velocity construction hard-normalizes `u_mu u^mu = -c^2`, and the projector
hard-enforces `u_mu F_cont^mu = 0` up to numerical precision.

## NanoWM Integration

NanoWM applies the chronometric layer to temporal token streams shaped
`[batch * spatial_patches, frames, hidden_size]` before each temporal transformer
block. The residual update is intentionally small but nonzero:

- `residual_scale: 0.01`
- `potential_families: 16`
- `loss_weights.invariant_norm: 1.0`
- `loss_weights.orthogonality: 1.0`

The learned potential-family basis is the first implementation hook for the
positive/negative Y outcome axis and future monster-group family clustering.

## Current Limits

This is the foundation pass. It does not yet implement ARC-specific labels,
human-in-the-loop correction, or hot-loaded conceptual rule injection. Those
belong downstream of this primitive.
