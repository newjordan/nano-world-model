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
        self.assertEqual(set(layer.last_losses), {"invariant_norm", "orthogonality", "raw_orthogonality"})
        self.assertIn("chronometric_outcome_y_mean", layer.last_metrics)

    def test_action_context_changes_external_force(self):
        layer = chrono.ChronometricContortionLayer(hidden_size=16)
        tokens = torch.randn(2, 4, 16)
        branch = torch.tensor([[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]])

        without_action = layer.score_branch(tokens, branch)
        with_action = layer.score_branch(tokens, branch, action_context=torch.ones_like(tokens))

        self.assertFalse(torch.allclose(without_action.external_force, with_action.external_force))
        self.assertIn("chronometric_external_force_rms", layer.last_metrics)

    def test_supplied_branch_direction_controls_branch_path(self):
        layer = chrono.ChronometricContortionLayer(hidden_size=16)
        tokens = torch.randn(1, 4, 16)
        branch_x = torch.tensor([[0.0, 1.0, 0.0, 0.0]])
        branch_y = torch.tensor([[0.0, 0.0, 1.0, 0.0]])

        out_x = layer.score_branch(tokens, branch_x)
        out_y = layer.score_branch(tokens, branch_y)

        self.assertFalse(torch.allclose(out_x.branch_direction, out_y.branch_direction))
        self.assertTrue(torch.isfinite(out_x.outcome_y).all())
        self.assertTrue(torch.isfinite(out_y.outcome_y).all())

    def test_branch_library_hotload_adjusts_score_branch_outcome(self):
        layer = chrono.ChronometricContortionLayer(hidden_size=16)
        tokens = torch.randn(2, 4, 16)
        branch = torch.tensor([[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]])
        contexts = [
            {
                "action_id": "ACTION6",
                "control_label": "dominant_group:time_phase",
                "action_context": [0.6, 1.0, 0.4375, 0.46875, 0.0, 0.0, 0.0, 0.0],
                "potential_family_names": ["time_phase.repeated_effect_size"],
                "potential_family_vector": [0.25],
            },
            {
                "action_id": "ACTION5",
                "control_label": "dominant_group:translation",
                "action_context": [0.5, 1.0, 0.4375, 0.46875, 0.0, 0.0, 0.0, 0.0],
                "potential_family_names": ["time_phase.repeated_effect_size"],
                "potential_family_vector": [0.25],
            },
        ]
        library = {
            "ACTION6|dominant_group:time_phase|x:28|y:30": chrono.BranchLibraryEntry(
                key="ACTION6|dominant_group:time_phase|x:28|y:30",
                records=1,
                signed_y_mean=0.25,
            )
        }

        raw = layer.score_branch(tokens, branch)
        adjusted = layer.score_branch(
            tokens,
            branch,
            branch_library=library,
            branch_library_contexts=contexts,
            branch_library_blend=1.0,
        )

        self.assertTrue(torch.allclose(adjusted.outcome_y[0].mean(), torch.tensor(0.25), atol=1e-6))
        self.assertTrue(torch.allclose(adjusted.outcome_y[1], raw.outcome_y[1], atol=1e-6))
        self.assertEqual(float(layer.last_metrics["chronometric_branch_library_applied"].item()), 1.0)

    def test_branch_library_translation_fallback_adjusts_score_branch_outcome(self):
        layer = chrono.ChronometricContortionLayer(hidden_size=16)
        tokens = torch.randn(1, 4, 16)
        branch = torch.tensor([[0.0, 1.0, 0.0, 0.0]])
        contexts = [
            {
                "action_id": "ACTION5",
                "control_label": "dominant_group:translation",
                "action_context": [0.5, 0.0, 0.0, 0.0, 0.0234375, 0.0, 0.0, 1.0],
                "changed_cells": 96,
                "potential_family_names": ["transition.changed_cells"],
                "potential_family_vector": [0.0234375],
            }
        ]

        adjusted = layer.score_branch(
            tokens,
            branch,
            branch_library={},
            branch_library_contexts=contexts,
            branch_library_blend=1.0,
            branch_library_fallback_scope="dominant_translation_potential",
        )

        self.assertTrue(torch.allclose(adjusted.outcome_y[0].mean(), torch.tensor(0.0234375), atol=1e-6))
        self.assertEqual(float(layer.last_metrics["chronometric_branch_library_applied"].item()), 1.0)
        self.assertEqual(float(layer.last_metrics["chronometric_branch_library_fallback_applied"].item()), 1.0)

    def test_nanowm_audit_mode_tracks_metrics_without_changing_output_when_runtime_deps_are_available(self):
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
                "mode": "audit",
                "residual_scale": 0.01,
                "potential_families": 8,
            },
        )
        model.eval()
        x = torch.randn(1, 4, 4, 8, 8)
        t = torch.ones(1, 4)
        action = torch.zeros(1, 4, 7)
        branch_direction = torch.tensor([[[0.0, 1.0, 0.0, 0.0]]]).expand(1, 4, 4)

        with torch.no_grad():
            out_audit = model(x, t, action=action, branch_direction=branch_direction)
            metrics = dict(model.get_chronometric_metrics())
            losses = model.get_chronometric_losses()
            model.use_chronometric = False
            out_disabled = model(x, t, action=action)

        self.assertEqual(out_audit.shape, x.shape)
        self.assertTrue(torch.allclose(out_audit, out_disabled))
        self.assertEqual(losses, {})
        self.assertIn("chronometric_orthogonality_abs_mean", metrics)

    def test_nanowm_residual_mode_exposes_chronometric_losses_when_runtime_deps_are_available(self):
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
                "mode": "residual_once",
                "residual_scale": 0.01,
                "potential_families": 8,
            },
        )
        x = torch.randn(1, 4, 4, 8, 8)
        t = torch.ones(1, 4)
        action = torch.zeros(1, 4, 7)

        _ = model(x, t, action=action)

        self.assertTrue(model.use_chronometric)
        self.assertIn("raw_orthogonality", model.get_chronometric_losses())


if __name__ == "__main__":
    unittest.main()
