# Chronometric Mechanics Smoke Results

Status: recorded mechanics smoke for the chronometric NanoWM foundation.

This is not a training run and not ARC model-quality evidence. It uses synthetic tokens and a synthetic bridge manifest.

## Condition

- run label: `mechanics_smoke`
- run kind: `new_experiment`
- git commit: `7c3691f843faccc576418e9cdfd2cdfaac1c92fc`
- git dirty at run: `True`
- git dirty excluding output dir: `False`
- seed: `20260505`
- device: `cuda`
- ARC data used: `False`

## Gates

| Gate | Pass | Key Metric |
| --- | --- | --- |
| `phase_log_cycle` | `True` | `phase_delta_error=1.430511474609375e-06` |
| `projector_constraint` | `True` | `orthogonality_max_abs=4.76837158203125e-07` |
| `layer_constraints` | `True` | `orthogonality_max_abs=7.450580596923828e-09` |
| `branch_direction_distinction` | `True` | `branch_force_pairwise_max=0.026731830090284348` |
| `action_context_changes_external_force` | `True` | `external_force_abs_mean_delta=0.1436905562877655` |
| `residual_update_nonzero` | `True` | `residual_abs_mean_delta=0.0017147973412647843` |
| `bridge_manifest_schema` | `True` | `records=2` |
| `nanowm_audit_forward` | `True` | `output_delta_max_abs=0.0` |

Overall pass: `True`

## Bridge Manifest

- synthetic manifest: `experiments/2026-05-05_chronometric_mechanics_smoke/synthetic_bridge_manifest.jsonl`
- quarantine/control status is preserved in every record
- no quarantined ARC Sprint 0 data was ingested
