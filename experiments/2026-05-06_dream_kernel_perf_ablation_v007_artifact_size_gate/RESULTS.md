# Dream Kernel Ablation V001 Results

Status: deterministic posthoc value/overhead analysis. No training data promoted.

## Condition

- run label: `dream_kernel_perf_ablation_v007_artifact_size_gate`
- run kind: `deterministic_dream_kernel_value_ablation_no_training`
- run label semantics: `new_experiment`
- git commit: `f7c19b0041516fccdf54234b4e58fa3298c9aef9`
- git dirty at run: `True`
- training_data_promoted: `False`
- script: `scripts/run_dream_kernel_ablations.py`
- sequence: `experiments/2026-05-06_chronometric_sensory_smattering_v034_human_eval/dream_sequence.json`
- sequence sha256: `3f312595416f493e86b56b114470b58ecec10832e7078917df72348c595c19e9`
- metric: `proxy_rank_preservation_and_value_density`

## Source

- schema: `dream_kernel.sequence.v003`
- sequence hash: `a8427cc307f07ffe`
- sequence bytes: `314628`
- frames: `7`
- ray count: `56`
- potential datapoints: `84`
- objects: `19`
- branches: `6`
- branch potentials: `73`
- object links: `144`
- max object links per branch: `24` of bound `24`
- object-link bound policy: stable branch-local sort by absolute chrono_y_correlation, retain top 24
- Nemo open questions: `38`
- Nemo confirmations: `6`
- Nemo reviews: `0`

## Layer Value Density

| layer | kind | items | bytes | value | density/kB | spearman | sign acc | top match | object coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| branch_matrix | score_layer | 6 | 2641 | 1 | 0.387732 | 1 | 1 | True | 1 |
| nemo_confirmations | semantic_sidecar | 6 | 9957 | 0.9525 | 0.0979572 |  |  | None |  |
| rays | score_layer | 56 | 18465 | 0.879082 | 0.0487506 | 0.885365 | 0.833333 | True | 0.947368 |
| object_registry_categories | metadata_layer | 19 | 27035 | 1 | 0.0378768 |  |  | None | 1 |
| nemo_relay_questions | metadata_layer | 38 | 24913 | 0.705263 | 0.0289885 |  |  | None | 0.157895 |
| chrono_datapoints | score_layer | 84 | 40271 | 0.978805 | 0.0248888 | 0.941124 | 1 | True | 1 |
| branch_potentials | score_layer | 73 | 76653 | 0.978805 | 0.0130758 | 0.941124 | 1 | True | 1 |
| object_links | score_layer | 144 | 104244 | 0.466667 | 0.00458412 | -0.637536 | 0.833333 | False | 1 |

## Drop-Ablation Proxy

| ablation | bytes removed | preservation | compression candidate | spearman | sign acc | top match | norm MAE |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |
| full_proxy_all_score_layers | 0 | 0.843367 | False | 0.880406 | 0.666667 | True | 0.165025 |
| drop_branch_matrix | 2641 | 0.833816 | False | 0.880406 | 0.666667 | True | 0.224719 |
| drop_rays | 18465 | 0.840849 | False | 0.880406 | 0.666667 | True | 0.180758 |
| drop_chrono_datapoints | 40271 | 0.835406 | False | 0.880406 | 0.666667 | True | 0.214779 |
| drop_branch_potentials | 76653 | 0.835406 | False | 0.880406 | 0.666667 | True | 0.214779 |
| drop_object_links | 104244 | 0.855425 | False | 0.880406 | 0.666667 | True | 0.0896582 |
| drop_semantic_relay_sidecars | 34870 | 0.843367 | False | 0.880406 | 0.666667 | True | 0.165025 |
| drop_object_registry_categories | 27035 | 0.843367 | False | 0.880406 | 0.666667 | True | 0.165025 |

## Compression Readout

- high-value layers: `['branch_matrix', 'nemo_confirmations', 'rays', 'object_registry_categories', 'chrono_datapoints', 'branch_potentials']`
- low-density layers for sparse/gated attention: `['branch_potentials', 'object_links']`
- object compression candidates: `['wall:0:3:0', 'wall:5:3:0']`
- recommended policy: Keep deterministic branch_matrix/object_registry as integrity anchors. Use sparse/gated attention first on low-density semantic or relation layers, and only skip low-value structural walls until a branch becomes stuck or uncertain.

### High-Value Evidence

- `branch_matrix`: value `1`, spearman `1`, sign `1`, top match `True`, critical coverage `1`, terminal coverage `1`
- `nemo_confirmations`: value `0.9525`, spearman ``, sign ``, top match `None`, critical coverage ``, terminal coverage `1`
- `rays`: value `0.879082`, spearman `0.885365`, sign `0.833333`, top match `True`, critical coverage `0.666667`, terminal coverage `1`
- `object_registry_categories`: value `1`, spearman ``, sign ``, top match `None`, critical coverage `1`, terminal coverage ``
- `chrono_datapoints`: value `0.978805`, spearman `0.941124`, sign `1`, top match `True`, critical coverage `1`, terminal coverage `1`
- `branch_potentials`: value `0.978805`, spearman `0.941124`, sign `1`, top match `True`, critical coverage `1`, terminal coverage `1`

## Interpretation

- This is a proxy analysis against the deterministic full branch score, not ground-truth human preference.
- A layer can be system-critical even if it is low-density; the compression pass should gate it, not delete it.
- Use human reviews to decide which Nemo semantic outputs become training targets.
