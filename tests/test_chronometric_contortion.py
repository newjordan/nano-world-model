import importlib.util
import math
import sys
import unittest
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))


def _load_chrono_module():
    module_path = SRC / "models" / "chronometric_contortion.py"
    spec = importlib.util.spec_from_file_location("chronometric_contortion_direct", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


chrono = _load_chrono_module()


class ChronometricContortionTests(unittest.TestCase):
    def test_log_time_phase_scale_cycle(self):
        tau = torch.tensor([3.0])
        theta = chrono.log_time_phase(tau, tau_c=0.0)
        theta_next = chrono.log_time_phase(tau * chrono.LOG_PHASE_LAMBDA, tau_c=0.0)

        self.assertTrue(torch.allclose(theta_next - theta, torch.tensor([2.0 * math.pi]), atol=1e-5))

    def test_projector_preserves_timelike_constraint_and_orthogonality(self):
        velocity = chrono.normalize_timelike_velocity(torch.tensor([[0.2, -0.1, 0.3]]), c=1.0)
        raw_response = torch.tensor([[0.7, 0.4, -0.2, 0.1]])
        projected = chrono.project_orthogonal_to_velocity(velocity, raw_response, c=1.0)

        invariant = chrono.minkowski_dot(velocity, velocity)
        orthogonality = chrono.minkowski_dot(velocity, projected)

        self.assertTrue(torch.allclose(invariant, torch.tensor([-1.0]), atol=1e-6))
        self.assertTrue(torch.allclose(orthogonality, torch.zeros_like(orthogonality), atol=1e-6))

    def test_chronometric_layer_updates_temporal_tokens_and_tracks_losses(self):
        layer = chrono.ChronometricContortionLayer(
            hidden_size=32,
            config=chrono.ChronometricConfig(residual_scale=0.05, potential_families=8),
        )
        tokens = torch.randn(2, 4, 32, requires_grad=True)

        out = layer(tokens)
        loss = out.square().mean() + layer.last_losses["invariant_norm"] + layer.last_losses["orthogonality"]
        loss.backward()

        self.assertEqual(out.shape, tokens.shape)
        self.assertTrue(torch.isfinite(out).all())
        self.assertTrue(torch.isfinite(tokens.grad).all())
        self.assertEqual(set(layer.last_losses), {"invariant_norm", "orthogonality"})
        self.assertIn("chronometric_outcome_y_mean", layer.last_metrics)

    def test_nanowm_uses_chronometric_layer_when_runtime_deps_are_available(self):
        try:
            from models.nanowm import NanoWM
        except ModuleNotFoundError as exc:
            self.skipTest(f"NanoWM runtime dependency missing: {exc.name}")

        model = NanoWM(
            input_size=8,
            patch_size=2,
            in_channels=4,
            hidden_size=64,
            depth=2,
            num_heads=4,
            num_frames=4,
            use_action=True,
            action_dim=7,
            causal=True,
            chronometric={
                "enabled": True,
                "residual_scale": 0.01,
                "potential_families": 8,
            },
        )
        x = torch.randn(1, 4, 4, 8, 8)
        t = torch.ones(1, 4)
        action = torch.zeros(1, 4, 7)

        out = model(x, t, action=action)

        self.assertEqual(out.shape, x.shape)
        self.assertTrue(model.use_chronometric)
        self.assertIn("chronometric_orthogonality_abs_mean", model.get_chronometric_metrics())


if __name__ == "__main__":
    unittest.main()
