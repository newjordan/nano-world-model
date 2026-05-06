# Documentation

Detailed reference for Nano World Model. The top-level [README](../README.md) covers install + a first training command; these docs go deeper.

## Layout

```
docs/
├── README.md             (this file — index)
├── config_system.md      (Hydra config: structure, overrides, paths, debugging)
├── training.md           (training workflow + design choices + ablation tables)
├── evaluation.md         (eval workflow + main result tables + sampling)
├── project_intent_and_boundaries.md
│                         (chronometric fork boundary + ARC quarantine rules)
├── chronometric_ab_qa_overlay_v030.md
│                         (A/B-centered open Q/A overlay for Nemo + NanoWM)
├── chronometric_map_perception_v031.md
│                         (labeled image/grid/3D geometry accuracy gate)
├── chronometric_sensory_alignment_v032.md
│                         (visual + temporal confirmation records)
├── chronometric_outcome_imagination_v033.md
│                         (pre-action imagined outcome vs observed outcome)
├── chronometric_sensory_smattering_v034.md
│                         (small human-eval probe batch)
├── chronometric_testing.md
│                         (first mechanics smoke and bridge-manifest gate)
├── datasets/
│   └── README.md         (DINO-WM, RT-1, CSGO formats and configs)
└── applications/
    ├── planning.md       (MPC + CEM model-predictive control)
    ├── long_rollout.md   (long-horizon autoregressive rollout)
    └── video_to_3d.md    (Depth Anything 3 → point cloud pipeline)
```

## Index

- **[Configuration system](config_system.md)** — Hydra layout, composition, environment variables, common overrides, debugging.
- **[Training](training.md)** — workflow + the four design axes (prediction target, action injection, model scale, EMA) with ablation tables and pretrained checkpoints.
- **[Project Intent And Boundaries](project_intent_and_boundaries.md)** — canonical split between this chronometric model body and the quarantined ARC scaffold/control repo.
- **[Chronometric Contortion Foundation](chronometric_contortion_foundation.md)** — installed 4D event-state, learned 4x4 K tensor, log-time phase, projector constraint, and potential-family hook.
- **[Chronometric Foundation Review V002](chronometric_foundation_review_v002.md)** — stricter audit of what is installed, what is still placeholder, and the staged path before ARC/data integration.
- **[Chronometric A/B Q/A Overlay V030](chronometric_ab_qa_overlay_v030.md)** — A/B-centered open question loop for Nemo-style semantic reasoning feeding NanoWM branch scoring.
- **[Chronometric Map Perception Gate V031](chronometric_map_perception_v031.md)** — palette-labeled image to grid, simple 3D geometry, object ray anchors, and strict accuracy gating before ray evidence is trusted.
- **[Chronometric Sensory Alignment V032](chronometric_sensory_alignment_v032.md)** — visual and temporal confirmation records linking 2D maps, 3D geometry, predicted transitions, observed transitions, and outcome imagination.
- **[Chronometric Outcome Imagination V033](chronometric_outcome_imagination_v033.md)** — corrected outcome channel: pre-action imagined signed-Y is available for planning, observed signed-Y is post-action calibration truth.
- **[Chronometric Sensory Smattering V034](chronometric_sensory_smattering_v034.md)** — deterministic human-eval probe batch over visual, temporal, and outcome-imagination cases.
- **[Chronometric Testing](chronometric_testing.md)** — dated mechanics smoke condition, gates, and the bridge-manifest schema used before ARC data can enter NanoWM tests.
- **[Evaluation](evaluation.md)** — `experiment=evaluate_only`, scheduling modes, metric definitions, headline numbers on each domain.
- **[Datasets](datasets/README.md)** — DINO-WM (5 envs), RT-1 fractal, CSGO. Download / split / format / config.
- **[Planning](applications/planning.md)** — MPC + CEM over the diffusion world model. point_maze and PushT recipes.
- **[Long rollout](applications/long_rollout.md)** — 50-frame autoregressive rollout with sliding context window. CSGO demo.
- **[Video → 3D point cloud](applications/video_to_3d.md)** — DA3 multi-view depth + viser viewer.

## Entrypoint

All training, evaluation, and planning runs go through `src/main.py`:

```bash
# Training
python src/main.py experiment=csgo dataset=game/csgo model=nanowm_l2_csgo

# Evaluation
python src/main.py experiment=evaluate_only dataset=dino_wm/pusht model=nanowm_b2 \
    resume_from_checkpoint=<path/to/checkpoint.ckpt>

# Planning
python src/main.py experiment=planning dataset=dino_wm/point_maze model=nanowm_b2 \
    ckpt_path=<path/to/checkpoint.ckpt>
```

See [config_system.md](config_system.md) for the full set of experiment / dataset / model options.
