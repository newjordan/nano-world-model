# Chronometric Goal Test Results

Status: rolling result ledger. Newest result first.

## V021 Branch-Library Scoring Integration

Artifacts:

- `src/chronometric_branch_library.py`
- `scripts/apply_chronometric_branch_library.py`
- `src/models/chronometric_contortion.py`
- `src/models/nanowm.py`
- `tests/test_chronometric_branch_library.py`
- `tests/test_chronometric_contortion.py`

Condition:

- no new calibration run
- implementation moves V020 branch-library adjustment into planner-facing
  scoring
- normal residual forward passes are unchanged
- branch-library scoring requires caller-supplied row-like branch contexts
- heldout labels used: `False`
- training data promoted: `False`

Verification:

- `python -m pytest tests/test_chronometric_contortion.py tests/test_chronometric_branch_library.py tests/test_chronometric_calibration.py`
- result: `22 passed`
- `python -m py_compile src/models/chronometric_contortion.py src/models/nanowm.py`

Decision:

V021 is a harness integration checkpoint. The branch library is no longer only
a posthoc JSON operation; NanoWM chronometric branch scoring can apply it during
planner scoring. Next work should broaden library keys beyond
`ACTION6|time_phase`, starting with the V020 top residual
`ACTION5|time_phase`.

## V020 Branch-Library Hotload

Artifacts:

- `experiments/2026-05-05_chronometric_branch_library_v020_v018_geometry_predictions/`
- `experiments/2026-05-05_chronometric_bucket_eval_v020_branch_library_v018_geometry_predictions/`
- `experiments/2026-05-05_chronometric_feature_coverage_v020_branch_library_v018_geometry_predictions/`

Condition:

- source predictions:
  `experiments/2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu/predictions.jsonl`
- manifest:
  `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/arc_bridge_manifest.jsonl`
- branch library source split: `train`
- branch library source field: `target_signed_y`
- blend: `1.0`
- min records per key: `1`
- heldout labels used: `False`
- training data promoted: `False`

Metrics:

- library entries: `4`
- adjusted records: `8`
- heldout adjusted records: `2`
- heldout signed-Y MAE: `0.018027649731448037`
- heldout progress accuracy: `1.0`
- heldout `ACTION6|time_phase` signed-Y MAE: `0.0`
- V016 heldout ka59 raw prediction: `-0.5890800952911377`
- V016 heldout ka59 branch-library prediction: `0.250244140625`
- top heldout bucket moved to `ACTION5|time_phase` at
  `0.22145648300647736`

Decision:

V020 converts the V019B transductive consistency finding into a non-transductive
inference mechanism: the branch library is built from train targets and applied
by geometry key at prediction time. This should be promoted as a harness
component candidate, pending integration into NanoWM chronometric branch
scoring and broader non-ACTION6 coverage.

## V019 Branch Consistency Objective

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v019_train_branch_consistency_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v019_train_branch_consistency_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v019_train_branch_consistency_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v019b_transductive_branch_consistency_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v019b_transductive_branch_consistency_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v019b_transductive_branch_consistency_v016_holdout_cpu/`

Condition:

- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/`
- heldout family:
  `experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md`
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- narrow dominant `ACTION6|time_phase` signed balance enabled, max weight
  `256`
- branch-consistency weight: `1.0`
- V019: train-only consistency pairs
- V019B: transductive diagnostic using heldout features for consistency pairs
  but recording `heldout_labels_used: False`
- training data promoted: `False`

Metrics:

- V019 branch pairs: `3`, all train-to-train, all tn36 key `x:61|y:1`
- V019 heldout signed-Y MAE: `0.02018224261701107`
- V019 heldout `ACTION6|time_phase` signed-Y MAE: `0.43091824650764465`
- V019 heldout V016 ka59 prediction: target `0.250244140625`, predicted
  `-0.5890800952911377`
- V019B branch pairs: `7`, with `4` train-to-heldout pairs and ka59 key
  `x:28|y:30`
- V019B heldout signed-Y MAE: `0.01702019013464451`
- V019B heldout `ACTION6|time_phase` signed-Y MAE:
  `0.013691052794456482`
- V019B train V015 ka59 prediction: target `0.250244140625`, predicted
  `0.23214775323867798`
- V019B heldout V016 ka59 prediction: target `0.250244140625`, predicted
  `0.23041227459907532`
- V019B top heldout bucket moved to `ACTION5|time_phase` at
  `0.2172355316579342`

Decision:

V019 train-only consistency is clean but cannot solve ka59 without matched train
pairs. V019B validates the branch-consistency mechanism: the heldout labels are
not used, but heldout features are used, so it is transductive diagnostic
evidence rather than a clean heldout promotion. Next work should make the same
pairing available non-transductively through planner-generated candidate
branches or a hotloaded branch library.

## V018 Coordinate Geometry Features

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v018_geometry_v015_support_v016_holdout_balance_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v018_geometry_v015_support_v016_holdout_balance_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v018_geometry_v015_support_v016_holdout_balance_cpu/`

Condition:

- manifest: `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/`
- heldout family:
  `experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md`
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- narrow dominant `ACTION6|time_phase` signed balance enabled, max weight
  `256`
- changed input representation only versus V017B: added coordinate-centered,
  radial, wall-distance, movement-magnitude, movement-alignment, and
  ACTION6/time-phase geometry interaction features
- training data promoted: `False`

Metrics:

- heldout total: `0.1835705190896988`
- heldout signed-Y MAE: `0.02018224261701107`
- heldout progress accuracy: `1.0`
- top heldout bucket: `ACTION6|time_phase`
- top heldout bucket signed-Y MAE: `0.43091824650764465`
- train V015 ka59 prediction: target `0.250244140625`, predicted
  `0.225009948015213`
- heldout V016 ka59 prediction: target `0.250244140625`, predicted
  `-0.5890800952911377`

Decision:

V018 improves aggregate heldout signed-Y and moves the heldout ka59 row in the
right direction versus V017B, but does not flip it positive. Passive geometry
features are useful but insufficient. Next work should test an explicit
branch-consistency or paired-family objective over matched coordinate-family
rows.

## V017 V015 Support With V016 Holdout

Artifacts:

- `experiments/2026-05-05_arc_bridge_manifest_v017_v015_support_v016_holdout/`
- `experiments/2026-05-05_chronometric_calibration_v017_v015_support_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v017_v015_support_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v017_v015_support_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v017b_v015_support_v016_holdout_dominant_balance_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v017b_v015_support_v016_holdout_dominant_balance_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v017b_v015_support_v016_holdout_dominant_balance_cpu/`

Condition:

- base manifest: V012 ACTION6 ten-task holdout
- added support family:
  `experiments/2026-05-04_v015_object_relative_movement_scout/CONDITION.md`
- heldout family:
  `experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md`
- merged manifest rows: `7732`
- train rows: `7332`
- heldout rows: `400`
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- V017: no signed balancing
- V017B: dominant `ACTION6|time_phase` signed balancing, max weight `256`
- training data promoted: `False`

Metrics:

- V017 heldout signed-Y MAE: `0.023165112361311913`
- V017 heldout progress accuracy: `1.0`
- V017 `ACTION6|time_phase` signed-Y MAE: `0.6599542051553726`
- V017 train V015 ka59 prediction: target `0.250244140625`, predicted
  `-0.9720876216888428`
- V017 heldout V016 ka59 prediction: target `0.250244140625`, predicted
  `-0.9651800394058228`
- V017B heldout signed-Y MAE: `0.034029360860586166`
- V017B heldout progress accuracy: `1.0`
- V017B `ACTION6|time_phase` signed-Y MAE: `0.46518605202436447`
- V017B train V015 ka59 prediction: target `0.250244140625`, predicted
  `0.23078583180904388`
- V017B heldout V016 ka59 prediction: target `0.250244140625`, predicted
  `-0.6703770160675049`

Decision:

V017 rejects plain support expansion as sufficient. V017B shows support plus
narrow balancing can fit the support ka59 row and partially transfer, but the
heldout controllability ka59 row remains negative. Next work should add
geometry abstraction across object-relative and controllability coordinate
families, not simply add more weight.

## V014-V016 ACTION6 Time-Phase Feature And Balance Iterations

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v014_action6_time_phase_features_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v014b_action6_time_phase_features_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v014_action6_time_phase_features_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v014b_action6_time_phase_features_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v015_action6_time_phase_signed_balance_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v016_action6_dominant_time_phase_balance_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v016_action6_dominant_time_phase_balance_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v016b_action6_dominant_time_phase_balance_v016_holdout_cpu/`

Condition:

- base comparators: V013 with V015 held out, and V012 with V016 held out
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- V014 changed input representation only: added safe coordinate/ACTION6/time
  interaction features; direct outcome fields stayed excluded
- V015 changed objective only: broad ACTION6 time-phase signed balancing,
  later recorded as a failed mask scout
- V016 changed objective only from V014: dominant
  `ACTION6|time_phase` signed balancing, max weight `256`
- training data promoted: `False`

Metrics:

- V014 V015-heldout signed-Y MAE: `0.016086839139461517`
- V014 V015-heldout `ACTION6|time_phase` signed-Y MAE: `0.6634646356105804`
- V014B V016-heldout signed-Y MAE: `0.03931467607617378`
- V014B V016-heldout `ACTION6|time_phase` signed-Y MAE: `0.6844081915915012`
- V015 broad balance selected `484` train rows and worsened V015-heldout
  signed-Y MAE to `0.028554601594805717`
- V016 dominant balance selected `6` train rows and `2` heldout rows on the
  V015-heldout condition; V015-heldout signed-Y MAE was
  `0.023143382743000984`
- V016 improved V015-heldout `ACTION6|time_phase` signed-Y MAE to
  `0.22553975135087967`; the top heldout error moved to
  `ACTION5|time_phase` at `0.26319148298352957`
- V016B selected only `4` train rows for the V016-heldout condition and failed
  the missing ka59-like heldout branch: `ACTION6|time_phase` signed-Y MAE
  `0.6336235329508781`

Decision:

V014 features are useful and should stay. V015 broad balancing is not promoted.
V016 narrow balancing proves the model can learn the rare time-phase sign when
the coordinate family has matching support, but V016B proves this does not
generalize when the ka59-like family is absent from train. Next work should
target coordinate-family coverage or a geometry-aware coordinate abstraction,
not stronger scalar loss weighting.

## V013 ACTION6 Support With V015 Heldout

Artifacts:

- `experiments/2026-05-05_arc_bridge_manifest_v013_v015_action6_holdout_family/`
- `experiments/2026-05-05_arc_bridge_manifest_v013_action6_support_v015_holdout/`
- `experiments/2026-05-05_chronometric_calibration_v013_action6_support_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v013_action6_support_v015_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v013_action6_support_v015_holdout_cpu/`

Condition:

- base manifest: V012 ACTION6 ten-task holdout manifest
- added heldout family:
  `experiments/2026-05-04_v015_object_relative_movement_scout/CONDITION.md`
- V016 is in train as ACTION6/time-phase support
- merged manifest rows: `7732`
- train rows: `7332`
- heldout rows: `400`
- heldout ACTION6 rows: `99`
- heldout progress-positive rows: `0`
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

Metrics:

- heldout total: `0.012371068820357323`
- heldout signed-Y MAE: `0.027918638661503792`
- heldout progress accuracy: `1.0`
- heldout top false-progress probability: `0.0008116625249385834`
- heldout ACTION6 signed-Y MAE: `0.051316857916500536`
- heldout stasis/no-change signed-Y MAE: `0.00007406903094932681`
- heldout stasis-loop signed-Y MAE: `0.025686474615021757`
- heldout time-phase signed-Y MAE: `0.15913675703546581`
- heldout translation signed-Y MAE: `0.026444879888625043`

Decision:

V013 improves ACTION6 aggregate transfer versus V012, but does not fix the
time-phase polarity residual. Next work should be feature-level or targeted
time-phase support, not generic data expansion.

## V012 ACTION6 Ten-Task Holdout

Artifacts:

- `experiments/2026-05-05_arc_bridge_manifest_v012_v016_action6_holdout_family/`
- `experiments/2026-05-05_arc_bridge_manifest_v012_action6_ten_task_holdout/`
- `experiments/2026-05-05_chronometric_calibration_v012_action6_ten_task_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v012_action6_ten_task_v016_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v012_action6_ten_task_v016_holdout_cpu/`

Condition:

- base manifest: V011 nonlocal second-family manifest
- added heldout family:
  `experiments/2026-05-04_v016_controllability_movement_scout/CONDITION.md`
- merged manifest rows: `7332`
- train rows: `6932`
- heldout rows: `400`
- heldout ACTION6 rows: `103`
- heldout progress-positive rows: `0`
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

Metrics:

- heldout total: `0.03148259222507477`
- heldout signed-Y MAE: `0.04510998725891113`
- heldout progress accuracy: `1.0`
- heldout top false-progress probability: `0.0015080823795869946`
- heldout ACTION6 signed-Y MAE: `0.11062070680330101`
- heldout stasis/no-change signed-Y MAE: `0.00016286648236788235`
- heldout stasis-loop signed-Y MAE: `0.017676929894246553`
- heldout time-phase signed-Y MAE: `0.12458408767865463`
- heldout translation signed-Y MAE: `0.058857012541698416`

Decision:

V012 confirms the V010 ACTION6 time-phase residual repeats on a separate
ACTION6-bearing ten-task family. Progress and stasis remain safe; the error is
signed-Y polarity for coordinate-bearing ACTION6 time/translation rows.

## V011 Nonlocal Second-Family Holdout

Artifacts:

- `experiments/2026-05-05_arc_bridge_manifest_v011_v033_nonlocal_holdout_family/`
- `experiments/2026-05-05_arc_bridge_manifest_v011_nonlocal_second_family/`
- `experiments/2026-05-05_chronometric_calibration_v011_nonlocal_second_family_v033_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v011_nonlocal_second_family_v033_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v011_nonlocal_second_family_v033_holdout_cpu/`

Condition:

- base manifest: V010 coordinate-action coverage
- added heldout family:
  `experiments/2026-05-05_v033_post_progress_nonlocal_replay/CONDITION.md`
- merged manifest rows: `6932`
- train rows: `3820`
- heldout rows: `3112`
- heldout progress-positive rows: `25`
- heldout split key: `source_condition_artifact`
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

Metrics:

- heldout total: `0.02222723700106144`
- heldout loss reduction vs baseline: `5.747143318876624`
- heldout signed-Y MAE: `0.01057388260960579`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- heldout positive mean rank: `13.0`
- heldout top false-progress probability: `0.00019551934383343905`
- heldout stasis/no-change signed-Y MAE: `0.0007385778427124024`
- heldout time-phase signed-Y MAE: `0.03205674101940143`
- heldout translation signed-Y MAE: `0.008579632027232642`
- heldout goal-progress signed-Y MAE: `0.004302263259887695`

Feature coverage findings:

- top heldout bucket: `action:ACTION4|control_label:dominant_group:time_phase`
- rows: `154`
- signed-Y MAE: `0.04311674078563591`
- same-label train rows: `62`
- same-label distance: `0.06919068110400774`

Decision:

V011 validates progress/nonlocal transfer on a second heldout family. It is not
an ACTION6 residual gate because V033 has no ACTION6 rows. Next step is an
ACTION6-bearing ten-task heldout family.

## V010 Coordinate-Action Coverage With V023 Heldout

Artifacts:

- `experiments/2026-05-05_arc_bridge_manifest_v010_ft09_action6_affordance/`
- `experiments/2026-05-05_arc_bridge_manifest_v010_ft09_targeted_coordinate/`
- `experiments/2026-05-05_arc_bridge_manifest_v010_tn36_action6_heatmap/`
- `experiments/2026-05-05_arc_bridge_manifest_v010_v023_mirror_hazard_holdout_family/`
- `experiments/2026-05-05_arc_bridge_manifest_v010_coordinate_action_coverage/`
- `experiments/2026-05-05_chronometric_calibration_v010_coordinate_action_coverage_v023_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v010_coordinate_action_coverage_v023_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v010_coordinate_action_coverage_v023_holdout_cpu/`

Condition:

- manifest rows: `3820`
- train rows: `3420`
- heldout rows: `400`
- heldout split key: `source_condition_artifact`
- heldout family:
  `experiments/2026-05-04_v023_mirror_hazard_current_state_scout/CONDITION.md`
- added train coverage:
  V009 ft09 ACTION6 affordance, V010 ft09 targeted coordinate, and V011 tn36
  ACTION6 coordinate heatmap
- requested device: `cpu`
- seed: `20260505`
- steps: `800`
- training data promoted: `False`

Metrics:

- heldout total: `0.012320181354880333`
- heldout loss reduction vs baseline: `1.839367488399148`
- heldout signed-Y MAE: `0.015096906572580338`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- heldout top false-progress probability: `0.0012611246202141047`
- heldout ACTION6 signed-Y MAE: `0.023567314073443413`
- heldout stasis/no-change signed-Y MAE: `0.0007162117958068848`
- heldout stasis-loop signed-Y MAE: `0.016637922901856273`
- heldout time-phase signed-Y MAE: `0.08845959440805018`
- heldout translation signed-Y MAE: `0.012906181446642611`

Feature coverage findings:

- ACTION6 stasis-loop is now supported by `419` same-label train rows and
  transfers to V023 at bucket signed-Y MAE `0.02959994265907689`.
- ACTION6 translation has same-label train support but still has one heldout
  row at signed-Y MAE `0.15824070572853088`.
- ACTION6 time-phase has `3` same-label train rows but one heldout edge remains
  the top error at signed-Y MAE `0.5810495018959045`.

Decision:

V010 validates the V009 coverage-gap hypothesis under a cleaner separate-family
heldout. It is a strong coordinate-action transfer checkpoint, not ARC solve
evidence. Next step is second-family validation; if the same residual repeats,
add a tiny time-phase support batch or feature check before changing losses.

## V009 ACTION6 Coverage Proxy

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_ft09_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v009_action6_coverage_ft09_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v009_action6_coverage_ft09_holdout_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v009_action6_coverage_tn36_holdout_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v009_action6_coverage_tn36_holdout_cpu/`
- `experiments/2026-05-05_chronometric_feature_coverage_v009_action6_coverage_tn36_holdout_cpu/`

Condition:

- same V006/V007 cross-family manifest
- split key: `source_artifact_path`
- ft09 probe: held out ft09 ACTION6 `stasis_no_change` plus m0r0 progress row;
  trained with tn36 ACTION6 in train
- tn36 probe: held out tn36 ACTION6 `dominant_group:stasis_loop` plus m0r0
  progress row; trained with ft09 ACTION6 in train
- requested device: `cpu`
- training data promoted: `False`
- run kind: coverage proxy, not clean cross-family promotion

Metrics:

- ft09 heldout total: `0.05827900767326355`
- ft09 heldout signed-Y MAE: `0.008341473527252674`
- ft09 heldout progress accuracy: `1.0`
- ft09 heldout positive best rank: `1`
- ft09 heldout ACTION6 signed-Y MAE: `0.00453176349401474`
- ft09 heldout stasis/no-change signed-Y MAE: `0.004146914590488781`
- ft09 top heldout false-progress probability: `0.00024259850033558905`
- tn36 heldout total: `0.08591418713331223`
- tn36 heldout signed-Y MAE: `0.04159923642873764`
- tn36 heldout progress accuracy: `1.0`
- tn36 heldout positive best rank: `1`
- tn36 heldout ACTION6 signed-Y MAE: `0.06988269835710526`
- tn36 heldout stasis-loop signed-Y MAE: `0.014360490598176656`
- tn36 top heldout false-progress probability: `0.0014863506658002734`

Feature coverage findings:

- ft09 ACTION6 `stasis_no_change` bucket had no same-label train rows but still
  transferred from the sibling coordinate-action coverage with signed-Y MAE
  `0.00453176349401474`.
- tn36 main stasis-loop block transferred well: `38` rows at signed-Y MAE
  `0.014360490598176656`.
- tn36 still has two tiny ACTION6 coordinate buckets outside same-label train
  coverage: one `dominant_group:time_phase` row at signed-Y MAE
  `1.2501307129859924` and one `dominant_group:translation` row at signed-Y MAE
  `0.9994785785675049`.

Decision:

V009 validates the coverage-gap hypothesis behind the V008 ACTION6 regression,
but it is not promoted as the clean cross-family best because the split includes
a sibling V019B ACTION6 artifact in train. V007 remains the current best clean
cross-family checkpoint. Next step: build broader coordinate-action coverage
with a separate heldout family.

## V008 Temporal Loop Context Line

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v008_temporal_loop_context_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v008_temporal_loop_context_cross_family/`
- `experiments/2026-05-05_chronometric_feature_coverage_v008_temporal_loop_context/`
- `experiments/2026-05-05_chronometric_calibration_v008b_negative_control_temporal_loop_context_cpu_comparable/`
- `experiments/2026-05-05_chronometric_bucket_eval_v008b_negative_control_temporal_loop_context_cpu/`
- `experiments/2026-05-05_chronometric_calibration_v008c_gated_temporal_context_cpu/`
- `experiments/2026-05-05_chronometric_bucket_eval_v008c_gated_temporal_context_cpu/`

Condition:

- same V006/V007 cross-family manifest
- train family: V031B post-progress avoidance replay
- heldout family: V019B ten-task target-discriminated scout
- split key: `source_condition_artifact`
- seed: `20260505`
- comparable CPU reads recorded for V008, V008B, and V008C
- training data promoted: `False`

Findings:

- V008 temporal context fixed ACTION5 heldout signed-Y MAE:
  V007 `0.972137` to V008 `0.0199724`.
- V008 regressed ACTION6 heldout signed-Y MAE:
  V007 `0.0343842` to V008 `1.96562`.
- V008B negative-control objective did not restore ACTION6 under CPU:
  ACTION6 MAE `1.81562`, heldout total `2.1029090881347656`.
- V008C coordinate-action gating did not change the V008 aggregate:
  heldout total `0.8733570575714111`, ACTION6 MAE `1.96562`.

Decision:

Do not promote V008/V008B/V008C. V007 remains current best. The next step is
ACTION6 coordinate-action coverage, not stronger scalar weighting.

## V007B Feature Coverage Diagnostic

Artifacts:

- `experiments/2026-05-05_chronometric_feature_coverage_v007b_safe_potential_inputs/`

Condition:

- diagnostic over V007 predictions
- no new training
- manifest: `experiments/2026-05-05_arc_bridge_manifest_v006_cross_family/arc_bridge_manifest.jsonl`
- predictions: `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/predictions.jsonl`
- training data promoted: `False`

Findings:

- worst heldout action/control bucket:
  `action:ACTION5|control_label:dominant_group:stasis_loop`
- rows: `38`
- signed-Y MAE: `1.3801347401581312`
- signed bias: `1.3801347401581312`
- nearest train bucket:
  `action:ACTION4|control_label:dominant_group:translation`
- nearest distance: `0.09656388286876233`
- same-label train rows: `3`
- same-label distance: `0.13204518981801616`

Decision:

V008 should not be a scalar knob change. The next issue is loop/stasis
representation and data coverage: heldout ACTION5/stasis-loop has sparse
same-label training support and aliases toward translation-like features.

## V007 Safe Potential Inputs

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v007_safe_potential_inputs_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v007_safe_potential_inputs_cross_family/`

Condition:

- train family: V031B post-progress avoidance replay
- heldout family: V019B ten-task target-discriminated scout
- split key: `source_condition_artifact`
- seed: `20260505`
- steps: `800`
- requested device: `auto`
- resolved device: `cpu`
- fallback: CUDA OOM due local GPU pressure
- training data promoted: `False`

Metrics:

- heldout final total: `0.26092466711997986`
- heldout loss reduction vs baseline: `1.1071387827396393`
- heldout signed-Y MAE: `0.18368175625801086`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- heldout top false-progress probability: `0.000129215550259687`

Bucket findings:

- ACTION6 signed-Y MAE improved to `0.0343842`.
- `stasis_no_change` signed-Y MAE improved to `0.000478867`.
- ACTION5/stasis-loop is now the main weakness:
  ACTION5 signed-Y MAE `0.972137`, stasis-loop signed-Y MAE `0.69665`.

Decision:

V007 is a real stabilization and feature-coverage gain. Next work should target
loop/repeated-action semantics, not learning-rate tuning.

## V006B Bounded Cross-Family Holdout

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v006b_bounded_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v006b_bounded_cross_family/`

Metrics:

- heldout final total: `1.0726784467697144`
- heldout signed-Y MAE: `0.7257595658302307`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- ACTION6 signed-Y MAE: `1.50313`

Decision:

Bounding signed-Y and family outputs stopped the V006 numerical explosion, but
the model still lacked the input surface needed to recognize stasis and loop
potentials across family holdout.

## V006 Cross-Family Holdout

Artifacts:

- `experiments/2026-05-05_chronometric_calibration_v006_cross_family_holdout/`
- `experiments/2026-05-05_chronometric_bucket_eval_v006_cross_family/`

Metrics:

- heldout final total: `306464768.0`
- heldout progress accuracy: `1.0`
- heldout positive best rank: `1`
- heldout signed-Y MAE: `6074.74`
- ACTION6 signed-Y MAE: `30371`

Decision:

Progress classification transferred, but unbounded signed-Y/family outputs made
the calibration numerically invalid on heldout ACTION6 rows.
