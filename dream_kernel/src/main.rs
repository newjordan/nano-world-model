use dream_kernel::{
    Action, CellKind, Coord, DreamKernel, DreamSequence, SimState, compass_directions,
    demo_sequence, sequence_to_json,
};
use std::collections::{BTreeMap, BTreeSet, HashSet, VecDeque};
use std::path::PathBuf;

fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    let command = args.get(1).map(String::as_str).unwrap_or("demo");
    match command {
        "demo" => match demo_sequence() {
            Ok(sequence) => {
                let json = sequence_to_json(&sequence);
                if let Some(path) = output_path(&args[2..]) {
                    if let Err(error) = std::fs::write(&path, format!("{json}\n")) {
                        eprintln!("dream-kernel write failed for {}: {error}", path.display());
                        std::process::exit(1);
                    }
                } else {
                    println!("{json}");
                }
            }
            Err(error) => {
                eprintln!("dream-kernel demo failed: {error}");
                std::process::exit(1);
            }
        },
        "solve-suite" => {
            let Some(out_dir) = output_dir(&args[2..]) else {
                eprintln!("usage: dream-kernel solve-suite --out-dir PATH");
                std::process::exit(2);
            };
            if let Err(error) = solve_suite(&out_dir) {
                eprintln!("dream-kernel solve-suite failed: {error}");
                std::process::exit(1);
            }
        }
        "solve-map" => {
            let parsed = match solve_map_args(&args[2..]) {
                Ok(parsed) => parsed,
                Err(error) => {
                    eprintln!("{error}");
                    eprintln!("{}", solve_map_usage());
                    std::process::exit(2);
                }
            };
            if let Err(error) = solve_map(parsed) {
                eprintln!("dream-kernel solve-map failed: {error}");
                std::process::exit(1);
            }
        }
        "arc-grid-scout" => {
            let parsed = match arc_grid_scout_args(&args[2..]) {
                Ok(parsed) => parsed,
                Err(error) => {
                    eprintln!("{error}");
                    eprintln!("{}", arc_grid_scout_usage());
                    std::process::exit(2);
                }
            };
            if let Err(error) = arc_grid_scout(parsed) {
                eprintln!("dream-kernel arc-grid-scout failed: {error}");
                std::process::exit(1);
            }
        }
        "ls20-plan-verify" => {
            let parsed = match ls20_plan_verify_args(&args[2..]) {
                Ok(parsed) => parsed,
                Err(error) => {
                    eprintln!("{error}");
                    eprintln!("{}", ls20_plan_verify_usage());
                    std::process::exit(2);
                }
            };
            if let Err(error) = ls20_plan_verify(parsed) {
                eprintln!("dream-kernel ls20-plan-verify failed: {error}");
                std::process::exit(1);
            }
        }
        _ => {
            eprintln!(
                "usage: dream-kernel demo [--out PATH] | solve-suite --out-dir PATH | {} | {} | {}",
                solve_map_usage(),
                arc_grid_scout_usage(),
                ls20_plan_verify_usage()
            );
            std::process::exit(2);
        }
    }
}

fn output_path(args: &[String]) -> Option<PathBuf> {
    match args {
        [] => None,
        [flag, path] if flag == "--out" => Some(PathBuf::from(path)),
        _ => {
            eprintln!("usage: dream-kernel demo [--out PATH]");
            std::process::exit(2);
        }
    }
}

fn output_dir(args: &[String]) -> Option<PathBuf> {
    match args {
        [flag, path] if flag == "--out-dir" => Some(PathBuf::from(path)),
        _ => None,
    }
}

fn solve_map_usage() -> &'static str {
    "solve-map --map PATH --sequence-out PATH --summary-out PATH [--name NAME] [--max-steps N] [--expected-reward VALUE]"
}

fn arc_grid_scout_usage() -> &'static str {
    "arc-grid-scout --grid PATH --summary-out PATH --state-id ID --game NAME --grid-sha256 SHA --actions 1,2,3,4 [--agent-label N --goal-label N --wall-labels N,N --hazard-labels N,N --max-steps N]"
}

fn ls20_plan_verify_usage() -> &'static str {
    "ls20-plan-verify --manifest PATH --summary-out PATH [--review-out PATH]"
}

fn solve_map_args(args: &[String]) -> Result<SolveMapArgs, String> {
    let mut map_path = None;
    let mut sequence_out = None;
    let mut summary_out = None;
    let mut name = "curriculum_map".to_string();
    let mut max_steps = 16usize;
    let mut expected_reward = 1.0f32;
    let mut index = 0usize;
    while index < args.len() {
        let flag = args[index].as_str();
        let Some(value) = args.get(index + 1) else {
            return Err(format!("missing value for {flag}"));
        };
        match flag {
            "--map" => map_path = Some(PathBuf::from(value)),
            "--sequence-out" => sequence_out = Some(PathBuf::from(value)),
            "--summary-out" => summary_out = Some(PathBuf::from(value)),
            "--name" => name = value.clone(),
            "--max-steps" => {
                max_steps = value
                    .parse::<usize>()
                    .map_err(|error| format!("invalid --max-steps {value:?}: {error}"))?;
            }
            "--expected-reward" => {
                expected_reward = value
                    .parse::<f32>()
                    .map_err(|error| format!("invalid --expected-reward {value:?}: {error}"))?;
            }
            other => return Err(format!("unknown solve-map flag: {other}")),
        }
        index += 2;
    }
    Ok(SolveMapArgs {
        map_path: map_path.ok_or_else(|| "missing --map".to_string())?,
        sequence_out: sequence_out.ok_or_else(|| "missing --sequence-out".to_string())?,
        summary_out: summary_out.ok_or_else(|| "missing --summary-out".to_string())?,
        name,
        max_steps,
        expected_reward,
    })
}

#[derive(Clone, Debug)]
struct Scenario {
    name: &'static str,
    lines: &'static [&'static str],
    max_steps: usize,
    expected_reward: f32,
}

#[derive(Clone, Debug)]
struct ScenarioResult {
    name: String,
    solved: bool,
    final_reward: f32,
    terminal: bool,
    steps: usize,
    planned_actions: Vec<String>,
    final_reason: String,
    sequence_file: String,
    sequence_hash: String,
    branch_rank_top_match: bool,
    accepted_steps: usize,
    rejected_steps: usize,
    invariant_passed: bool,
    decision_trace: Vec<DecisionTrace>,
}

#[derive(Clone, Debug)]
struct DecisionTrace {
    tick_before: u32,
    agent_position: Coord,
    selected_action_id: String,
    candidates: Vec<CandidateTrace>,
}

#[derive(Clone, Debug)]
struct CandidateTrace {
    action: Action,
    action_id: String,
    policy_score: f32,
    branch_chrono_y_net: f32,
    outcome_accepted: bool,
    outcome_reward: f32,
    outcome_terminal: bool,
    outcome_reason: String,
    next_position: Option<Coord>,
    safe_path_progress_delta: Option<i32>,
    safe_path_progress_bonus: f32,
    revisit_penalty_applied: bool,
    wait_penalty_applied: bool,
    selected: bool,
}

#[derive(Clone, Debug)]
struct SolveMapArgs {
    map_path: PathBuf,
    sequence_out: PathBuf,
    summary_out: PathBuf,
    name: String,
    max_steps: usize,
    expected_reward: f32,
}

#[derive(Clone, Debug)]
struct ArcGridScoutArgs {
    grid_path: PathBuf,
    summary_out: PathBuf,
    state_id: String,
    game: String,
    grid_sha256: String,
    actions: Vec<i32>,
    agent_label: Option<i32>,
    goal_label: Option<i32>,
    wall_labels: HashSet<i32>,
    hazard_labels: HashSet<i32>,
    max_steps: usize,
}

#[derive(Clone, Debug)]
struct Ls20PlanVerifyArgs {
    manifest_path: PathBuf,
    summary_out: PathBuf,
    review_out: Option<PathBuf>,
}

#[derive(Clone, Debug)]
struct Ls20SimulationTraceRow {
    review_step_index: usize,
    global_step_before: usize,
    global_step_after: usize,
    round_index: i32,
    round_step_index: usize,
    action_value: i32,
    action_name: String,
    x_before: i32,
    y_before: i32,
    z_before: i32,
    x_after: i32,
    y_after: i32,
    z_after: i32,
    shape_before: i32,
    color_before: i32,
    rotation_before: i32,
    shape_after: i32,
    color_after: i32,
    rotation_after: i32,
    goals_completed_after: i32,
    goal_count: i32,
    steps_remaining_after: i32,
    lives_after: i32,
    transition_reason: String,
    round_completed_after_step: bool,
    win_after_step: bool,
    state_after_sha256: String,
}

fn arc_grid_scout_args(args: &[String]) -> Result<ArcGridScoutArgs, String> {
    let mut grid_path = None;
    let mut summary_out = None;
    let mut state_id = None;
    let mut game = None;
    let mut grid_sha256 = None;
    let mut actions = None;
    let mut agent_label = None;
    let mut goal_label = None;
    let mut wall_labels = HashSet::new();
    let mut hazard_labels = HashSet::new();
    let mut max_steps = 32usize;
    let mut index = 0usize;
    while index < args.len() {
        let flag = args[index].as_str();
        let Some(value) = args.get(index + 1) else {
            return Err(format!("missing value for {flag}"));
        };
        match flag {
            "--grid" => grid_path = Some(PathBuf::from(value)),
            "--summary-out" => summary_out = Some(PathBuf::from(value)),
            "--state-id" => state_id = Some(value.clone()),
            "--game" => game = Some(value.clone()),
            "--grid-sha256" => grid_sha256 = Some(value.clone()),
            "--actions" => actions = Some(parse_i32_list(value)?),
            "--agent-label" => {
                agent_label = Some(
                    value
                        .parse::<i32>()
                        .map_err(|error| format!("invalid --agent-label {value:?}: {error}"))?,
                );
            }
            "--goal-label" => {
                goal_label = Some(
                    value
                        .parse::<i32>()
                        .map_err(|error| format!("invalid --goal-label {value:?}: {error}"))?,
                );
            }
            "--wall-labels" => wall_labels = parse_i32_list(value)?.into_iter().collect(),
            "--hazard-labels" => hazard_labels = parse_i32_list(value)?.into_iter().collect(),
            "--max-steps" => {
                max_steps = value
                    .parse::<usize>()
                    .map_err(|error| format!("invalid --max-steps {value:?}: {error}"))?;
            }
            other => return Err(format!("unknown arc-grid-scout flag: {other}")),
        }
        index += 2;
    }
    Ok(ArcGridScoutArgs {
        grid_path: grid_path.ok_or_else(|| "missing --grid".to_string())?,
        summary_out: summary_out.ok_or_else(|| "missing --summary-out".to_string())?,
        state_id: state_id.ok_or_else(|| "missing --state-id".to_string())?,
        game: game.ok_or_else(|| "missing --game".to_string())?,
        grid_sha256: grid_sha256.ok_or_else(|| "missing --grid-sha256".to_string())?,
        actions: actions.ok_or_else(|| "missing --actions".to_string())?,
        agent_label,
        goal_label,
        wall_labels,
        hazard_labels,
        max_steps,
    })
}

fn ls20_plan_verify_args(args: &[String]) -> Result<Ls20PlanVerifyArgs, String> {
    let mut manifest_path = None;
    let mut summary_out = None;
    let mut review_out = None;
    let mut index = 0usize;
    while index < args.len() {
        let flag = args[index].as_str();
        let Some(value) = args.get(index + 1) else {
            return Err(format!("missing value for {flag}"));
        };
        match flag {
            "--manifest" => manifest_path = Some(PathBuf::from(value)),
            "--summary-out" => summary_out = Some(PathBuf::from(value)),
            "--review-out" => review_out = Some(PathBuf::from(value)),
            other => return Err(format!("unknown ls20-plan-verify flag: {other}")),
        }
        index += 2;
    }
    Ok(Ls20PlanVerifyArgs {
        manifest_path: manifest_path.ok_or_else(|| "missing --manifest".to_string())?,
        summary_out: summary_out.ok_or_else(|| "missing --summary-out".to_string())?,
        review_out,
    })
}

fn solve_suite(out_dir: &PathBuf) -> Result<(), String> {
    std::fs::create_dir_all(out_dir)
        .map_err(|error| format!("create {}: {error}", out_dir.display()))?;
    let scenarios = [
        Scenario {
            name: "direct_goal_two_step",
            lines: &["#####", "#A.G#", "#...#", "#####"],
            max_steps: 4,
            expected_reward: 1.0,
        },
        Scenario {
            name: "hazard_detour_goal",
            lines: &["######", "#A.HG#", "#....#", "######"],
            max_steps: 8,
            expected_reward: 1.0,
        },
        Scenario {
            name: "wall_detour_goal",
            lines: &["######", "#A#.G#", "#....#", "######"],
            max_steps: 8,
            expected_reward: 1.0,
        },
        Scenario {
            name: "object_detour_goal",
            lines: &["######", "#AO.G#", "#....#", "######"],
            max_steps: 8,
            expected_reward: 1.0,
        },
    ];

    let mut rows = Vec::new();
    for scenario in scenarios {
        let row = run_scenario(scenario, out_dir)?;
        rows.push(row);
    }
    let solved = rows.iter().filter(|row| row.solved).count();
    let summary = format!(
        "{{\"schema\":\"dream_kernel.small_solve_suite.v001\",\"scenario_count\":{},\"solved\":{},\"failed\":{},\"pass_rate\":{},\"scenarios\":[{}]}}\n",
        rows.len(),
        solved,
        rows.len() - solved,
        number_to_json(solved as f32 / rows.len().max(1) as f32),
        rows.iter()
            .map(scenario_result_to_json)
            .collect::<Vec<_>>()
            .join(",")
    );
    std::fs::write(out_dir.join("solver_summary.json"), summary)
        .map_err(|error| format!("write solver summary: {error}"))?;
    Ok(())
}

fn solve_map(args: SolveMapArgs) -> Result<(), String> {
    let map_text = std::fs::read_to_string(&args.map_path)
        .map_err(|error| format!("read {}: {error}", args.map_path.display()))?;
    let lines_owned = map_text
        .lines()
        .map(str::trim_end)
        .filter(|line| !line.trim().is_empty())
        .map(str::to_string)
        .collect::<Vec<_>>();
    if lines_owned.is_empty() {
        return Err(format!(
            "{} did not contain map rows",
            args.map_path.display()
        ));
    }
    let line_refs = lines_owned.iter().map(String::as_str).collect::<Vec<_>>();
    if let Some(parent) = args.sequence_out.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|error| format!("create {}: {error}", parent.display()))?;
    }
    if let Some(parent) = args.summary_out.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|error| format!("create {}: {error}", parent.display()))?;
    }
    let sequence_label = args
        .sequence_out
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("dream_sequence.json")
        .to_string();
    let (sequence, row) = solve_lines(
        &args.name,
        &line_refs,
        args.max_steps,
        args.expected_reward,
        sequence_label,
    )?;
    let sequence_json = sequence_to_json(&sequence);
    std::fs::write(&args.sequence_out, format!("{sequence_json}\n"))
        .map_err(|error| format!("write {}: {error}", args.sequence_out.display()))?;
    let summary = format!(
        "{{\"schema\":\"dream_kernel.solve_map.v001\",\"map_path\":\"{}\",\"sequence_out\":\"{}\",\"scenario\":{}}}\n",
        json_escape(&args.map_path.display().to_string()),
        json_escape(&args.sequence_out.display().to_string()),
        scenario_result_to_json(&row)
    );
    std::fs::write(&args.summary_out, summary)
        .map_err(|error| format!("write {}: {error}", args.summary_out.display()))?;
    Ok(())
}

fn arc_grid_scout(args: ArcGridScoutArgs) -> Result<(), String> {
    if let Some(parent) = args.summary_out.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|error| format!("create {}: {error}", parent.display()))?;
    }
    let grid = read_label_grid(&args.grid_path)?;
    let unsupported_reason = arc_grid_support_reason(&args, &grid);
    let summary = if let Some(reason) = unsupported_reason {
        arc_grid_unsupported_json(&args, &reason)
    } else {
        arc_grid_supported_json(&args, &grid)?
    };
    std::fs::write(&args.summary_out, format!("{summary}\n"))
        .map_err(|error| format!("write {}: {error}", args.summary_out.display()))?;
    Ok(())
}

fn ls20_plan_verify(args: Ls20PlanVerifyArgs) -> Result<(), String> {
    if let Some(parent) = args.summary_out.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|error| format!("create {}: {error}", parent.display()))?;
    }
    let manifest = read_kv_manifest(&args.manifest_path)?;
    let state_id = manifest_value(&manifest, "state_id")?.to_string();
    let game = manifest_value(&manifest, "game")?.to_string();
    let grid_sha256 = manifest_value(&manifest, "grid_sha256")?.to_string();
    let candidate_actions = parse_i32_list(manifest_value(&manifest, "candidate_action_values")?)?;
    let planned_actions = parse_i32_list(manifest_value(&manifest, "planned_action_values")?)?;
    let completion_steps = parse_i32_list(manifest_value(&manifest, "level_completion_steps")?)?;
    let manifest_supported = parse_bool(manifest_value(&manifest, "supported")?)?;
    let manifest_solved = parse_bool(manifest_value(&manifest, "solved")?)?;
    let source_model_verified = parse_bool(manifest_value(&manifest, "source_model_verified")?)?;
    let matched_known_plan = parse_bool(manifest_value(&manifest, "matched_known_plan")?)?;
    let planned_rollout_steps = parse_usize(
        manifest_value(&manifest, "planned_rollout_steps")?,
        "planned_rollout_steps",
    )?;
    let total_plan_steps = parse_usize(
        manifest_value(&manifest, "total_plan_steps")?,
        "total_plan_steps",
    )?;
    let current_prefix_index = parse_usize(
        manifest_value(&manifest, "current_prefix_index")?,
        "current_prefix_index",
    )?;
    let levels_completed_start = parse_i32(
        manifest_value(&manifest, "levels_completed_start")?,
        "levels_completed_start",
    )?;
    let final_levels_completed = parse_i32(
        manifest_value(&manifest, "final_levels_completed")?,
        "final_levels_completed",
    )?;
    let win_levels = parse_i32(manifest_value(&manifest, "win_levels")?, "win_levels")?;
    let final_state = manifest_value(&manifest, "final_state")?.to_string();
    let source_simulation_trace_artifact = manifest
        .get("source_simulation_trace_artifact")
        .map(String::as_str);
    let source_simulation_trace_sha256 = manifest
        .get("source_simulation_trace_sha256")
        .map(String::as_str);
    let simulation_trace_tsv = manifest.get("simulation_trace_tsv").map(String::as_str);
    let expected_trace_rows = manifest
        .get("simulation_trace_rows")
        .map(|value| parse_usize(value, "simulation_trace_rows"))
        .transpose()?;
    let (trace_rows, trace_read_failure) = match simulation_trace_tsv {
        Some(path_value) => {
            let path = resolve_manifest_path(&args.manifest_path, path_value);
            match read_ls20_simulation_trace_tsv(&path) {
                Ok(rows) => (rows, None),
                Err(error) => (
                    Vec::new(),
                    Some(format!("simulation_trace_read_failed:{error}")),
                ),
            }
        }
        None => (Vec::new(), Some("missing_simulation_trace_tsv".to_string())),
    };

    let mut failures = Vec::new();
    if let Some(error) = trace_read_failure {
        failures.push(error);
    }
    if game != "ls20" {
        failures.push(format!("unsupported_game_{game}"));
    }
    if candidate_actions.is_empty() {
        failures.push("missing_candidate_action_values".to_string());
    }
    if planned_actions.len() != planned_rollout_steps {
        failures.push("planned_rollout_steps_mismatch".to_string());
    }
    if current_prefix_index + planned_actions.len() != total_plan_steps {
        failures.push("prefix_plus_remaining_does_not_match_total_plan_steps".to_string());
    }
    if completion_steps.len() != win_levels.max(0) as usize {
        failures.push("level_completion_steps_count_mismatch".to_string());
    }
    if completion_steps.windows(2).any(|pair| pair[0] >= pair[1]) {
        failures.push("level_completion_steps_not_strictly_increasing".to_string());
    }
    if completion_steps.last().copied().unwrap_or_default() != total_plan_steps as i32 {
        failures.push("final_completion_step_does_not_match_total_plan_steps".to_string());
    }
    if planned_actions
        .iter()
        .any(|action| !matches!(*action, 1 | 2 | 3 | 4))
    {
        failures.push("planned_action_outside_ls20_action_space".to_string());
    }
    if candidate_actions
        .iter()
        .any(|action| !matches!(*action, 1 | 2 | 3 | 4))
    {
        failures.push("candidate_action_outside_ls20_action_space".to_string());
    }
    let first_planned_action = planned_actions.first().copied();
    if let Some(selected_action) = first_planned_action {
        if !candidate_actions.contains(&selected_action) {
            failures.push("selected_action_not_in_candidate_actions".to_string());
        }
    } else if manifest_solved {
        failures.push("solved_manifest_has_no_planned_actions".to_string());
    }
    if final_state != "WIN" {
        failures.push("final_state_not_win".to_string());
    }
    if final_levels_completed != win_levels {
        failures.push("final_levels_completed_does_not_equal_win_levels".to_string());
    }
    if levels_completed_start < 0 || levels_completed_start > win_levels {
        failures.push("levels_completed_start_out_of_range".to_string());
    }
    if !manifest_supported {
        failures.push("manifest_not_supported".to_string());
    }
    if !manifest_solved {
        failures.push("manifest_not_solved".to_string());
    }
    if !source_model_verified {
        failures.push("source_model_not_verified".to_string());
    }
    if !matched_known_plan {
        failures.push("current_state_not_matched_to_source_plan".to_string());
    }
    if manifest_solved && trace_rows.is_empty() {
        failures.push("missing_simulation_trace_rows".to_string());
    }
    if let Some(expected) = expected_trace_rows {
        if trace_rows.len() != expected {
            failures.push("simulation_trace_rows_count_mismatch".to_string());
        }
    }
    if manifest_solved && trace_rows.len() != planned_actions.len() {
        failures.push("simulation_trace_rows_do_not_match_planned_rollout_steps".to_string());
    }
    if let Some(first_row) = trace_rows.first() {
        if first_row.global_step_before != current_prefix_index {
            failures.push("simulation_trace_first_step_does_not_match_current_prefix".to_string());
        }
    }
    if let Some(last_row) = trace_rows.last() {
        if manifest_solved && last_row.global_step_after != total_plan_steps {
            failures.push("simulation_trace_last_step_does_not_match_total_plan".to_string());
        }
        if manifest_solved && !last_row.win_after_step {
            failures.push("simulation_trace_final_frame_not_win".to_string());
        }
    }
    for (index, action_value) in planned_actions.iter().enumerate() {
        let Some(row) = trace_rows.get(index) else {
            break;
        };
        if row.review_step_index != index {
            failures.push("simulation_trace_review_step_index_mismatch".to_string());
        }
        if row.action_value != *action_value {
            failures.push("simulation_trace_action_sequence_mismatch".to_string());
        }
        if row.global_step_before + 1 != row.global_step_after {
            failures.push("simulation_trace_global_step_not_contiguous".to_string());
        }
        if index > 0 && row.global_step_before != trace_rows[index - 1].global_step_after {
            failures.push("simulation_trace_has_gap".to_string());
        }
        let completion_expected = completion_steps
            .iter()
            .any(|step| *step == row.global_step_after as i32);
        if row.round_completed_after_step != completion_expected {
            failures.push("simulation_trace_completion_flag_mismatch".to_string());
        }
    }
    failures.sort();
    failures.dedup();

    let supported = failures.is_empty();
    let solved = supported && manifest_solved;
    let support_reason = if supported {
        "ls20_source_plan_manifest_verified".to_string()
    } else {
        failures.join("|")
    };
    let planned_action_ids = planned_actions
        .iter()
        .map(|value| format!("ACTION{value}"))
        .collect::<Vec<_>>();
    let planned_sequence_hash = format!("fnv1a64:{:016x}", fnv1a64_i32s(&planned_actions));
    let candidate_rows = candidate_actions
        .iter()
        .map(|action_value| {
            ls20_candidate_rollout_json(
                *action_value,
                first_planned_action,
                supported,
                solved,
                planned_actions.len(),
                current_prefix_index,
                &completion_steps,
                total_plan_steps,
                &planned_sequence_hash,
                &support_reason,
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    let simulation_review_schema = "dream_kernel.ls20_3d_simulation_review.v001";
    if let Some(review_out) = &args.review_out {
        if let Some(parent) = review_out.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|error| format!("create {}: {error}", parent.display()))?;
        }
        let review_json = ls20_simulation_review_json(
            simulation_review_schema,
            &state_id,
            &game,
            &grid_sha256,
            supported,
            solved,
            &support_reason,
            current_prefix_index,
            total_plan_steps,
            levels_completed_start,
            final_levels_completed,
            win_levels,
            &final_state,
            source_simulation_trace_artifact,
            source_simulation_trace_sha256,
            simulation_trace_tsv,
            &completion_steps,
            &trace_rows,
        );
        std::fs::write(review_out, format!("{review_json}\n"))
            .map_err(|error| format!("write {}: {error}", review_out.display()))?;
    }
    let simulation_review_artifact = args
        .review_out
        .as_ref()
        .map(|path| path.display().to_string());
    let simulation_review_round_count = ls20_trace_round_count(&trace_rows);
    let summary = format!(
        "{{\"schema\":\"dream_kernel.ls20_plan_verify.v001\",\"state_id\":\"{}\",\"game\":\"{}\",\"grid_sha256\":\"{}\",\"supported\":{},\"support_reason\":\"{}\",\"solved\":{},\"selected_action_value\":{},\"planned_action_values\":{},\"planned_action_ids\":{},\"planned_rollout_steps\":{},\"planned_sequence_hash\":\"{}\",\"source_model_verified\":{},\"matched_known_plan\":{},\"current_prefix_index\":{},\"total_plan_steps\":{},\"level_completion_steps\":{},\"levels_completed_start\":{},\"final_levels_completed\":{},\"win_levels\":{},\"final_state\":\"{}\",\"simulation_review_schema\":\"{}\",\"simulation_review_artifact\":{},\"simulation_review_frame_count\":{},\"simulation_review_round_count\":{},\"source_simulation_trace_artifact\":{},\"source_simulation_trace_sha256\":{},\"simulation_trace_tsv\":{},\"candidate_rollouts\":[{}]}}",
        json_escape(&state_id),
        json_escape(&game),
        json_escape(&grid_sha256),
        supported,
        json_escape(&support_reason),
        solved,
        optional_i32_to_json(first_planned_action),
        i32_vec_to_json(&planned_actions),
        string_vec_to_json(&planned_action_ids),
        planned_actions.len(),
        json_escape(&planned_sequence_hash),
        source_model_verified,
        matched_known_plan,
        current_prefix_index,
        total_plan_steps,
        i32_vec_to_json(&completion_steps),
        levels_completed_start,
        final_levels_completed,
        win_levels,
        json_escape(&final_state),
        json_escape(simulation_review_schema),
        string_option_to_json(simulation_review_artifact.as_deref()),
        trace_rows.len(),
        simulation_review_round_count,
        string_option_to_json(source_simulation_trace_artifact),
        string_option_to_json(source_simulation_trace_sha256),
        string_option_to_json(simulation_trace_tsv),
        candidate_rows
    );
    std::fs::write(&args.summary_out, format!("{summary}\n"))
        .map_err(|error| format!("write {}: {error}", args.summary_out.display()))?;
    Ok(())
}

fn arc_grid_support_reason(args: &ArcGridScoutArgs, grid: &[Vec<i32>]) -> Option<String> {
    if args.actions.is_empty() {
        return Some("missing_candidate_actions".to_string());
    }
    let Some(agent_label) = args.agent_label else {
        return Some("missing_agent_label_mapping".to_string());
    };
    let Some(goal_label) = args.goal_label else {
        return Some("missing_goal_label_mapping".to_string());
    };
    if args.wall_labels.contains(&agent_label)
        || args.wall_labels.contains(&goal_label)
        || args.hazard_labels.contains(&agent_label)
        || args.hazard_labels.contains(&goal_label)
        || agent_label == goal_label
    {
        return Some("overlapping_label_roles".to_string());
    }
    let agent_count = grid
        .iter()
        .flatten()
        .filter(|value| **value == agent_label)
        .count();
    if agent_count != 1 {
        return Some(format!("expected_one_agent_cell_found_{agent_count}"));
    }
    let goal_count = grid
        .iter()
        .flatten()
        .filter(|value| **value == goal_label)
        .count();
    if goal_count == 0 {
        return Some("missing_goal_cells".to_string());
    }
    None
}

fn arc_grid_unsupported_json(args: &ArcGridScoutArgs, reason: &str) -> String {
    let candidate_rows = args
        .actions
        .iter()
        .map(|action_value| {
            format!(
                "{{\"action_value\":{},\"action_name\":\"ACTION{}\",\"action_id\":{},\"kernel_supported\":false,\"prediction_supported\":false,\"predicted_next_frame_sha256\":null,\"predicted_next_state\":\"UNKNOWN\",\"predicted_level_delta\":null,\"predicted_solved\":false,\"predicted_solved_by_plan\":false,\"rollout_steps\":0,\"rollout_reason\":\"{}\",\"one_step_accepted\":null,\"one_step_reward\":null,\"on_planned_solution_prefix\":false}}",
                action_value,
                action_value,
                string_option_to_json(action_id_for_arc_action(*action_value).as_deref()),
                json_escape(reason)
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "{{\"schema\":\"dream_kernel.arc_grid_scout.v001\",\"state_id\":\"{}\",\"game\":\"{}\",\"grid_sha256\":\"{}\",\"supported\":false,\"support_reason\":\"{}\",\"solved\":false,\"selected_action_value\":null,\"planned_action_values\":[],\"planned_action_ids\":[],\"planned_rollout_steps\":0,\"planned_sequence_hash\":null,\"candidate_rollouts\":[{}]}}",
        json_escape(&args.state_id),
        json_escape(&args.game),
        json_escape(&args.grid_sha256),
        json_escape(reason),
        candidate_rows
    )
}

fn arc_grid_supported_json(args: &ArcGridScoutArgs, grid: &[Vec<i32>]) -> Result<String, String> {
    let lines = grid_to_ascii_lines(args, grid)?;
    let line_refs = lines.iter().map(String::as_str).collect::<Vec<_>>();
    let (sequence, row) = solve_lines(
        &args.game,
        &line_refs,
        args.max_steps,
        1.0,
        "arc_grid_internal_rollout.dream_sequence.json".to_string(),
    )?;
    let planned_action_values = row
        .planned_actions
        .iter()
        .filter_map(|action_id| arc_action_for_action_id(action_id))
        .collect::<Vec<_>>();
    let first_planned_action = planned_action_values.first().copied();
    let candidate_rows = args
        .actions
        .iter()
        .map(|action_value| {
            candidate_rollout_json(*action_value, first_planned_action, row.solved, &line_refs)
        })
        .collect::<Result<Vec<_>, _>>()?
        .join(",");
    Ok(format!(
        "{{\"schema\":\"dream_kernel.arc_grid_scout.v001\",\"state_id\":\"{}\",\"game\":\"{}\",\"grid_sha256\":\"{}\",\"supported\":true,\"support_reason\":\"label_roles_supported\",\"solved\":{},\"selected_action_value\":{},\"planned_action_values\":{},\"planned_action_ids\":{},\"planned_rollout_steps\":{},\"planned_sequence_hash\":\"{}\",\"candidate_rollouts\":[{}]}}",
        json_escape(&args.state_id),
        json_escape(&args.game),
        json_escape(&args.grid_sha256),
        row.solved,
        first_planned_action
            .map(|value| value.to_string())
            .unwrap_or_else(|| "null".to_string()),
        i32_vec_to_json(&planned_action_values),
        string_vec_to_json(&row.planned_actions),
        row.steps,
        json_escape(&sequence.integrity.sequence_hash),
        candidate_rows
    ))
}

fn candidate_rollout_json(
    action_value: i32,
    first_planned_action: Option<i32>,
    solved: bool,
    line_refs: &[&str],
) -> Result<String, String> {
    let action_id = action_id_for_arc_action(action_value);
    let Some(action) = action_for_arc_action(action_value) else {
        return Ok(format!(
            "{{\"action_value\":{},\"action_name\":\"ACTION{}\",\"action_id\":null,\"kernel_supported\":true,\"prediction_supported\":false,\"predicted_next_frame_sha256\":null,\"predicted_next_state\":\"UNKNOWN\",\"predicted_level_delta\":null,\"predicted_solved\":false,\"predicted_solved_by_plan\":false,\"rollout_steps\":0,\"rollout_reason\":\"unknown_action_mapping\",\"one_step_accepted\":null,\"one_step_reward\":null,\"on_planned_solution_prefix\":false}}",
            action_value, action_value
        ));
    };
    let state = SimState::from_ascii_layer(line_refs)?;
    let directions = compass_directions();
    let mut kernel = DreamKernel::new(state);
    let sequence = kernel.rollout(&[action], &directions, 16, "agent")?;
    let next_frame_hash = sequence.frames.get(1).and_then(|frame| {
        frame
            .integrity
            .as_ref()
            .map(|integrity| integrity.frame_hash.clone())
    });
    let outcome = sequence
        .frames
        .get(1)
        .and_then(|frame| frame.outcome.as_ref());
    let one_step_accepted = outcome.map(|row| row.accepted).unwrap_or(false);
    let one_step_reward = outcome.map(|row| row.reward).unwrap_or(0.0);
    let one_step_terminal = outcome.map(|row| row.terminal).unwrap_or(false);
    let predicted_next_state = if one_step_terminal && one_step_reward > 0.0 {
        "WIN"
    } else if one_step_terminal && one_step_reward < 0.0 {
        "LOSS"
    } else {
        "NOT_FINISHED"
    };
    let predicted_level_delta = if one_step_terminal && one_step_reward > 0.0 {
        1
    } else {
        0
    };
    let on_plan = first_planned_action == Some(action_value);
    Ok(format!(
        "{{\"action_value\":{},\"action_name\":\"ACTION{}\",\"action_id\":{},\"kernel_supported\":true,\"prediction_supported\":true,\"predicted_next_frame_sha256\":{},\"predicted_next_state\":\"{}\",\"predicted_level_delta\":{},\"predicted_solved\":{},\"predicted_solved_by_plan\":{},\"rollout_steps\":1,\"rollout_reason\":\"one_step_transition_predicted_by_dream_kernel\",\"one_step_accepted\":{},\"one_step_reward\":{},\"on_planned_solution_prefix\":{}}}",
        action_value,
        action_value,
        string_option_to_json(action_id.as_deref()),
        string_option_to_json(next_frame_hash.as_deref()),
        predicted_next_state,
        predicted_level_delta,
        one_step_terminal && one_step_reward > 0.0,
        solved && on_plan,
        one_step_accepted,
        number_to_json(one_step_reward),
        on_plan
    ))
}

fn read_label_grid(path: &PathBuf) -> Result<Vec<Vec<i32>>, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|error| format!("read {}: {error}", path.display()))?;
    let rows = text
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .map(|line| {
            line.split_whitespace()
                .map(|token| {
                    token
                        .parse::<i32>()
                        .map_err(|error| format!("invalid grid token {token:?}: {error}"))
                })
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?;
    if rows.is_empty() {
        return Err(format!("{} did not contain grid rows", path.display()));
    }
    let width = rows[0].len();
    if width == 0 || rows.iter().any(|row| row.len() != width) {
        return Err("label grid rows must be non-empty and rectangular".to_string());
    }
    Ok(rows)
}

fn grid_to_ascii_lines(args: &ArcGridScoutArgs, grid: &[Vec<i32>]) -> Result<Vec<String>, String> {
    let agent_label = args
        .agent_label
        .ok_or_else(|| "agent label missing after support check".to_string())?;
    let goal_label = args
        .goal_label
        .ok_or_else(|| "goal label missing after support check".to_string())?;
    Ok(grid
        .iter()
        .map(|row| {
            row.iter()
                .map(|value| {
                    if *value == agent_label {
                        'A'
                    } else if *value == goal_label {
                        'G'
                    } else if args.wall_labels.contains(value) {
                        '#'
                    } else if args.hazard_labels.contains(value) {
                        'H'
                    } else {
                        '.'
                    }
                })
                .collect::<String>()
        })
        .collect())
}

fn read_kv_manifest(path: &PathBuf) -> Result<BTreeMap<String, String>, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|error| format!("read {}: {error}", path.display()))?;
    let mut manifest = BTreeMap::new();
    for (line_index, line) in text.lines().enumerate() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        let Some((key, value)) = trimmed.split_once('=') else {
            return Err(format!("manifest line {} is missing '='", line_index + 1));
        };
        let key = key.trim();
        if key.is_empty() {
            return Err(format!("manifest line {} has empty key", line_index + 1));
        }
        manifest.insert(key.to_string(), value.trim().to_string());
    }
    Ok(manifest)
}

fn manifest_value<'a>(
    manifest: &'a BTreeMap<String, String>,
    key: &str,
) -> Result<&'a str, String> {
    manifest
        .get(key)
        .map(String::as_str)
        .ok_or_else(|| format!("manifest missing {key}"))
}

fn resolve_manifest_path(manifest_path: &PathBuf, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() || path.exists() {
        return path;
    }
    if let Some(parent) = manifest_path.parent() {
        let sibling = parent.join(value);
        if sibling.exists() {
            return sibling;
        }
    }
    path
}

fn read_ls20_simulation_trace_tsv(path: &PathBuf) -> Result<Vec<Ls20SimulationTraceRow>, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|error| format!("read {}: {error}", path.display()))?;
    let mut lines = text.lines();
    let Some(header) = lines.next() else {
        return Err(format!("{} did not contain a header", path.display()));
    };
    let columns = header.split('\t').collect::<Vec<_>>();
    let index = |name: &str| {
        columns
            .iter()
            .position(|column| *column == name)
            .ok_or_else(|| format!("{} missing column {name}", path.display()))
    };
    let review_step_index = index("review_step_index")?;
    let global_step_before = index("global_step_before")?;
    let global_step_after = index("global_step_after")?;
    let round_index = index("round_index")?;
    let round_step_index = index("round_step_index")?;
    let action_value = index("action_value")?;
    let action_name = index("action_name")?;
    let x_before = index("x_before")?;
    let y_before = index("y_before")?;
    let z_before = index("z_before")?;
    let x_after = index("x_after")?;
    let y_after = index("y_after")?;
    let z_after = index("z_after")?;
    let shape_before = index("shape_before")?;
    let color_before = index("color_before")?;
    let rotation_before = index("rotation_before")?;
    let shape_after = index("shape_after")?;
    let color_after = index("color_after")?;
    let rotation_after = index("rotation_after")?;
    let goals_completed_after = index("goals_completed_after")?;
    let goal_count = index("goal_count")?;
    let steps_remaining_after = index("steps_remaining_after")?;
    let lives_after = index("lives_after")?;
    let transition_reason = index("transition_reason")?;
    let round_completed_after_step = index("round_completed_after_step")?;
    let win_after_step = index("win_after_step")?;
    let state_after_sha256 = index("state_after_sha256")?;
    let mut rows = Vec::new();
    for (line_index, line) in lines.enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let cells = line.split('\t').collect::<Vec<_>>();
        let get = |column: usize| {
            cells.get(column).copied().ok_or_else(|| {
                format!(
                    "{} line {} missing column {}",
                    path.display(),
                    line_index + 2,
                    column
                )
            })
        };
        rows.push(Ls20SimulationTraceRow {
            review_step_index: parse_usize(get(review_step_index)?, "review_step_index")?,
            global_step_before: parse_usize(get(global_step_before)?, "global_step_before")?,
            global_step_after: parse_usize(get(global_step_after)?, "global_step_after")?,
            round_index: parse_i32(get(round_index)?, "round_index")?,
            round_step_index: parse_usize(get(round_step_index)?, "round_step_index")?,
            action_value: parse_i32(get(action_value)?, "action_value")?,
            action_name: get(action_name)?.to_string(),
            x_before: parse_i32(get(x_before)?, "x_before")?,
            y_before: parse_i32(get(y_before)?, "y_before")?,
            z_before: parse_i32(get(z_before)?, "z_before")?,
            x_after: parse_i32(get(x_after)?, "x_after")?,
            y_after: parse_i32(get(y_after)?, "y_after")?,
            z_after: parse_i32(get(z_after)?, "z_after")?,
            shape_before: parse_i32(get(shape_before)?, "shape_before")?,
            color_before: parse_i32(get(color_before)?, "color_before")?,
            rotation_before: parse_i32(get(rotation_before)?, "rotation_before")?,
            shape_after: parse_i32(get(shape_after)?, "shape_after")?,
            color_after: parse_i32(get(color_after)?, "color_after")?,
            rotation_after: parse_i32(get(rotation_after)?, "rotation_after")?,
            goals_completed_after: parse_i32(get(goals_completed_after)?, "goals_completed_after")?,
            goal_count: parse_i32(get(goal_count)?, "goal_count")?,
            steps_remaining_after: parse_i32(get(steps_remaining_after)?, "steps_remaining_after")?,
            lives_after: parse_i32(get(lives_after)?, "lives_after")?,
            transition_reason: get(transition_reason)?.to_string(),
            round_completed_after_step: parse_bool(get(round_completed_after_step)?)?,
            win_after_step: parse_bool(get(win_after_step)?)?,
            state_after_sha256: get(state_after_sha256)?.to_string(),
        });
    }
    Ok(rows)
}

fn parse_bool(value: &str) -> Result<bool, String> {
    match value {
        "true" => Ok(true),
        "false" => Ok(false),
        other => Err(format!("invalid bool value {other:?}")),
    }
}

fn parse_usize(value: &str, label: &str) -> Result<usize, String> {
    value
        .parse::<usize>()
        .map_err(|error| format!("invalid {label} {value:?}: {error}"))
}

fn parse_i32(value: &str, label: &str) -> Result<i32, String> {
    value
        .parse::<i32>()
        .map_err(|error| format!("invalid {label} {value:?}: {error}"))
}

#[allow(clippy::too_many_arguments)]
fn ls20_candidate_rollout_json(
    action_value: i32,
    first_planned_action: Option<i32>,
    supported: bool,
    solved: bool,
    planned_remaining_steps: usize,
    current_prefix_index: usize,
    completion_steps: &[i32],
    total_plan_steps: usize,
    planned_sequence_hash: &str,
    support_reason: &str,
) -> String {
    let on_plan = supported && first_planned_action == Some(action_value);
    let next_prefix = current_prefix_index + 1;
    let next_completes_level = on_plan
        && completion_steps
            .iter()
            .any(|step| *step == next_prefix as i32);
    let next_wins = on_plan && next_prefix == total_plan_steps;
    let predicted_next_state = if next_wins { "WIN" } else { "NOT_FINISHED" };
    let predicted_level_delta = if next_completes_level { 1 } else { 0 };
    let next_frame_hash = if on_plan {
        Some(format!("{planned_sequence_hash}:next:{next_prefix}"))
    } else {
        None
    };
    format!(
        "{{\"action_value\":{},\"action_name\":\"ACTION{}\",\"action_id\":\"ACTION{}\",\"kernel_supported\":{},\"prediction_supported\":{},\"predicted_next_frame_sha256\":{},\"predicted_next_state\":\"{}\",\"predicted_level_delta\":{},\"predicted_solved\":{},\"predicted_solved_by_plan\":{},\"rollout_steps\":{},\"rollout_reason\":\"{}\",\"one_step_accepted\":{},\"one_step_reward\":{},\"on_planned_solution_prefix\":{}}}",
        action_value,
        action_value,
        action_value,
        supported,
        on_plan,
        string_option_to_json(next_frame_hash.as_deref()),
        predicted_next_state,
        predicted_level_delta,
        next_wins,
        solved && on_plan,
        if on_plan { planned_remaining_steps } else { 0 },
        json_escape(support_reason),
        on_plan,
        number_to_json(if next_completes_level { 1.0 } else { 0.0 }),
        on_plan
    )
}

#[allow(clippy::too_many_arguments)]
fn ls20_simulation_review_json(
    schema: &str,
    state_id: &str,
    game: &str,
    grid_sha256: &str,
    supported: bool,
    solved: bool,
    support_reason: &str,
    current_prefix_index: usize,
    total_plan_steps: usize,
    levels_completed_start: i32,
    final_levels_completed: i32,
    win_levels: i32,
    final_state: &str,
    source_simulation_trace_artifact: Option<&str>,
    source_simulation_trace_sha256: Option<&str>,
    simulation_trace_tsv: Option<&str>,
    completion_steps: &[i32],
    rows: &[Ls20SimulationTraceRow],
) -> String {
    format!(
        "{{\"schema\":\"{}\",\"state_id\":\"{}\",\"game\":\"{}\",\"grid_sha256\":\"{}\",\"review_scope\":\"remaining_plan_from_current_state\",\"projection_basis\":\"arc_frame_label_grid_3d_heightmap_with_ls20_state_channels\",\"supported\":{},\"solved\":{},\"support_reason\":\"{}\",\"current_prefix_index\":{},\"total_plan_steps\":{},\"levels_completed_start\":{},\"final_levels_completed\":{},\"win_levels\":{},\"final_state\":\"{}\",\"source_simulation_trace_artifact\":{},\"source_simulation_trace_sha256\":{},\"simulation_trace_tsv\":{},\"level_completion_steps\":{},\"round_count\":{},\"frame_count\":{},\"rounds\":{},\"frames\":{},\"completion_frames\":{}}}",
        json_escape(schema),
        json_escape(state_id),
        json_escape(game),
        json_escape(grid_sha256),
        supported,
        solved,
        json_escape(support_reason),
        current_prefix_index,
        total_plan_steps,
        levels_completed_start,
        final_levels_completed,
        win_levels,
        json_escape(final_state),
        string_option_to_json(source_simulation_trace_artifact),
        string_option_to_json(source_simulation_trace_sha256),
        string_option_to_json(simulation_trace_tsv),
        i32_vec_to_json(completion_steps),
        ls20_trace_round_count(rows),
        rows.len(),
        ls20_trace_rounds_to_json(rows),
        ls20_trace_frames_to_json(rows),
        ls20_completion_frames_to_json(rows)
    )
}

fn ls20_trace_round_count(rows: &[Ls20SimulationTraceRow]) -> usize {
    rows.iter()
        .map(|row| row.round_index)
        .collect::<BTreeSet<_>>()
        .len()
}

fn ls20_trace_rounds_to_json(rows: &[Ls20SimulationTraceRow]) -> String {
    let mut rounds = BTreeMap::<i32, Vec<&Ls20SimulationTraceRow>>::new();
    for row in rows {
        rounds.entry(row.round_index).or_default().push(row);
    }
    format!(
        "[{}]",
        rounds
            .iter()
            .map(|(round_index, rows)| ls20_trace_round_to_json(*round_index, rows))
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn ls20_trace_round_to_json(round_index: i32, rows: &[&Ls20SimulationTraceRow]) -> String {
    let Some(first) = rows.first().copied() else {
        return "{}".to_string();
    };
    let Some(last) = rows.last().copied() else {
        return "{}".to_string();
    };
    let action_values = rows.iter().map(|row| row.action_value).collect::<Vec<_>>();
    let action_names = rows
        .iter()
        .map(|row| row.action_name.clone())
        .collect::<Vec<_>>();
    format!(
        "{{\"round_index\":{},\"global_step_start\":{},\"global_step_end\":{},\"round_step_start\":{},\"round_step_end\":{},\"frame_start_index\":{},\"frame_count\":{},\"action_values\":{},\"action_names\":{},\"start_position_3d\":{},\"final_position_3d\":{},\"final_shape_color_rotation\":{},\"goals_completed_after\":{},\"goal_count\":{},\"round_completed_in_review\":{},\"win_after_round\":{},\"final_transition_reason\":\"{}\",\"final_state_sha256\":\"{}\"}}",
        round_index,
        first.global_step_before,
        last.global_step_after,
        first.round_step_index,
        last.round_step_index + 1,
        first.review_step_index,
        rows.len(),
        i32_vec_to_json(&action_values),
        string_vec_to_json(&action_names),
        coord_values_to_json(first.x_before, first.y_before, first.z_before),
        coord_values_to_json(last.x_after, last.y_after, last.z_after),
        i32_vec_to_json(&[last.shape_after, last.color_after, last.rotation_after]),
        last.goals_completed_after,
        last.goal_count,
        last.round_completed_after_step,
        last.win_after_step,
        json_escape(&last.transition_reason),
        json_escape(&last.state_after_sha256)
    )
}

fn ls20_trace_frames_to_json(rows: &[Ls20SimulationTraceRow]) -> String {
    format!(
        "[{}]",
        rows.iter()
            .map(ls20_trace_frame_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn ls20_completion_frames_to_json(rows: &[Ls20SimulationTraceRow]) -> String {
    format!(
        "[{}]",
        rows.iter()
            .filter(|row| row.round_completed_after_step || row.win_after_step)
            .map(ls20_trace_frame_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn ls20_trace_frame_to_json(row: &Ls20SimulationTraceRow) -> String {
    format!(
        "{{\"review_step_index\":{},\"global_step_before\":{},\"global_step_after\":{},\"round_index\":{},\"round_step_index\":{},\"action_value\":{},\"action_name\":\"{}\",\"transition_reason\":\"{}\",\"state_before\":{{\"position_3d\":{},\"shape_color_rotation\":{}}},\"state_after\":{{\"position_3d\":{},\"shape_color_rotation\":{},\"goals_completed\":{},\"goal_count\":{},\"steps_remaining\":{},\"lives\":{},\"signature_sha256\":\"{}\"}},\"round_completed_after_step\":{},\"win_after_step\":{}}}",
        row.review_step_index,
        row.global_step_before,
        row.global_step_after,
        row.round_index,
        row.round_step_index,
        row.action_value,
        json_escape(&row.action_name),
        json_escape(&row.transition_reason),
        coord_values_to_json(row.x_before, row.y_before, row.z_before),
        i32_vec_to_json(&[row.shape_before, row.color_before, row.rotation_before]),
        coord_values_to_json(row.x_after, row.y_after, row.z_after),
        i32_vec_to_json(&[row.shape_after, row.color_after, row.rotation_after]),
        row.goals_completed_after,
        row.goal_count,
        row.steps_remaining_after,
        row.lives_after,
        json_escape(&row.state_after_sha256),
        row.round_completed_after_step,
        row.win_after_step
    )
}

fn coord_values_to_json(x: i32, y: i32, z: i32) -> String {
    format!("[{x},{y},{z}]")
}

fn fnv1a64_i32s(values: &[i32]) -> u64 {
    let mut hash = 0xcbf29ce484222325u64;
    for value in values {
        for byte in value.to_le_bytes() {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3);
        }
    }
    hash
}

fn parse_i32_list(value: &str) -> Result<Vec<i32>, String> {
    if value.trim().is_empty() {
        return Ok(Vec::new());
    }
    value
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(|item| {
            item.parse::<i32>()
                .map_err(|error| format!("invalid integer list value {item:?}: {error}"))
        })
        .collect()
}

fn action_for_arc_action(action_value: i32) -> Option<Action> {
    match action_value {
        0 => Some(Action::Wait),
        1 => Some(Action::move_agent(Coord::new(1, 0, 0))),
        2 => Some(Action::move_agent(Coord::new(0, 1, 0))),
        3 => Some(Action::move_agent(Coord::new(0, -1, 0))),
        4 => Some(Action::move_agent(Coord::new(-1, 0, 0))),
        _ => None,
    }
}

fn action_id_for_arc_action(action_value: i32) -> Option<String> {
    action_for_arc_action(action_value).map(Action::action_id)
}

fn arc_action_for_action_id(action_id: &str) -> Option<i32> {
    match action_id {
        "wait" => Some(0),
        "move_entity_0_dx1_dy0_dz0" => Some(1),
        "move_entity_0_dx0_dy1_dz0" => Some(2),
        "move_entity_0_dx0_dy-1_dz0" => Some(3),
        "move_entity_0_dx-1_dy0_dz0" => Some(4),
        _ => None,
    }
}

fn run_scenario(scenario: Scenario, out_dir: &PathBuf) -> Result<ScenarioResult, String> {
    let sequence_file = format!("{}.dream_sequence.json", scenario.name);
    let (sequence, row) = solve_lines(
        scenario.name,
        scenario.lines,
        scenario.max_steps,
        scenario.expected_reward,
        sequence_file.clone(),
    )?;
    let sequence_json = sequence_to_json(&sequence);
    std::fs::write(out_dir.join(&sequence_file), format!("{sequence_json}\n"))
        .map_err(|error| format!("write {sequence_file}: {error}"))?;
    Ok(row)
}

fn solve_lines(
    name: &str,
    lines: &[&str],
    max_steps: usize,
    expected_reward: f32,
    sequence_file: String,
) -> Result<(DreamSequence, ScenarioResult), String> {
    let state = SimState::from_ascii_layer(lines)?;
    let initial_state = state.clone();
    let mut kernel = DreamKernel::new(state);
    let directions = compass_directions();
    let mut actions = Vec::new();
    let mut planned_actions = Vec::new();
    let mut decision_trace = Vec::new();
    let mut visited = vec![agent_position(&kernel)?];
    for _ in 0..max_steps {
        if kernel.state.terminal {
            break;
        }
        let candidates = score_action_candidates(&kernel, &directions, &visited)?;
        let best = choose_action_from_candidates(&candidates)?;
        decision_trace.push(mark_selected_candidate(
            kernel.state.tick,
            agent_position(&kernel)?,
            best,
            candidates,
        ));
        let outcome = kernel.step(best);
        actions.push(best);
        planned_actions.push(best.action_id());
        visited.push(agent_position(&kernel)?);
        if outcome.terminal {
            break;
        }
    }

    let mut replay = DreamKernel::new(initial_state);
    let sequence = replay.rollout(&actions, &directions, 16, "agent")?;
    let final_outcome = sequence
        .frames
        .last()
        .and_then(|frame| frame.outcome.as_ref());
    let final_reward = final_outcome.map(|row| row.reward).unwrap_or(0.0);
    let terminal = final_outcome.map(|row| row.terminal).unwrap_or(false);
    let final_reason = final_outcome
        .map(|row| row.reason.clone())
        .unwrap_or_else(|| "no outcome".to_string());
    let accepted_steps = sequence
        .frames
        .iter()
        .filter_map(|frame| frame.outcome.as_ref())
        .filter(|outcome| outcome.accepted)
        .count();
    let rejected_steps = sequence
        .frames
        .iter()
        .filter_map(|frame| frame.outcome.as_ref())
        .filter(|outcome| !outcome.accepted)
        .count();
    let branch_rank_top_match = branch_rank_top_match(&sequence);
    let sequence_hash = sequence.integrity.sequence_hash.clone();
    let invariant_passed = sequence.integrity.invariant_passed;
    Ok((
        sequence,
        ScenarioResult {
            name: name.to_string(),
            solved: terminal && (final_reward - expected_reward).abs() < 0.0001,
            final_reward,
            terminal,
            steps: actions.len(),
            planned_actions,
            final_reason,
            sequence_file,
            sequence_hash,
            branch_rank_top_match,
            accepted_steps,
            rejected_steps,
            invariant_passed,
            decision_trace,
        },
    ))
}

fn score_action_candidates(
    kernel: &DreamKernel,
    directions: &[Coord],
    visited: &[Coord],
) -> Result<Vec<CandidateTrace>, String> {
    let candidates = [
        Action::move_agent(Coord::new(1, 0, 0)),
        Action::move_agent(Coord::new(0, 1, 0)),
        Action::move_agent(Coord::new(0, -1, 0)),
        Action::move_agent(Coord::new(-1, 0, 0)),
        Action::Wait,
    ];
    let mut scored = Vec::with_capacity(candidates.len());
    let current_safe_distance =
        shortest_safe_path_to_positive_goal(&kernel.state, agent_position(kernel)?);
    for action in candidates {
        let mut clone = kernel.clone();
        let sequence = clone.rollout(&[action], directions, 16, "agent")?;
        let branch_score = sequence
            .branch_matrix
            .first()
            .map(|branch| branch.chrono_y_net)
            .unwrap_or(0.0);
        let outcome = sequence
            .frames
            .last()
            .and_then(|frame| frame.outcome.as_ref());
        let mut score = branch_score;
        let mut outcome_accepted = false;
        let mut outcome_reward = 0.0;
        let mut outcome_terminal = false;
        let mut outcome_reason = "no outcome".to_string();
        if let Some(outcome) = outcome {
            outcome_accepted = outcome.accepted;
            outcome_reward = outcome.reward;
            outcome_terminal = outcome.terminal;
            outcome_reason = outcome.reason.clone();
            score += outcome.reward * 3.0;
            if outcome.accepted {
                score += 0.05;
            } else {
                score -= 0.75;
            }
            if outcome.terminal && outcome.reward > 0.0 {
                score += 3.0;
            }
            if outcome.terminal && outcome.reward < 0.0 {
                score -= 3.0;
            }
        }
        let wait_penalty_applied = matches!(action, Action::Wait);
        if matches!(action, Action::Wait) {
            score -= 0.45;
        }
        let next_position = sequence
            .frames
            .last()
            .and_then(|frame| frame.rays.first().map(|ray| ray.origin));
        let mut safe_path_progress_delta = None;
        let mut safe_path_progress_bonus = 0.0;
        if outcome_accepted {
            if let (Some(current_distance), Some(position)) = (current_safe_distance, next_position)
            {
                if let Some(next_distance) =
                    shortest_safe_path_to_positive_goal(&kernel.state, position)
                {
                    let delta = current_distance as i32 - next_distance as i32;
                    safe_path_progress_delta = Some(delta);
                    safe_path_progress_bonus = 0.2 * delta as f32;
                    score += safe_path_progress_bonus;
                }
            }
        }
        let mut revisit_penalty_applied = false;
        if let Some(position) = next_position {
            if visited.contains(&position) {
                revisit_penalty_applied = true;
                score -= 0.35;
            }
        }
        scored.push(CandidateTrace {
            action,
            action_id: action.action_id(),
            policy_score: score,
            branch_chrono_y_net: branch_score,
            outcome_accepted,
            outcome_reward,
            outcome_terminal,
            outcome_reason,
            next_position,
            safe_path_progress_delta,
            safe_path_progress_bonus,
            revisit_penalty_applied,
            wait_penalty_applied,
            selected: false,
        });
    }
    Ok(scored)
}

fn choose_action_from_candidates(candidates: &[CandidateTrace]) -> Result<Action, String> {
    candidates
        .iter()
        .fold(None, |best: Option<(f32, Action)>, candidate| match best {
            None => Some((candidate.policy_score, candidate.action)),
            Some((best_score, _)) if candidate.policy_score > best_score => {
                Some((candidate.policy_score, candidate.action))
            }
            Some(best) => Some(best),
        })
        .map(|row| row.1)
        .ok_or_else(|| "no candidate action scored".to_string())
}

fn mark_selected_candidate(
    tick_before: u32,
    agent_position: Coord,
    selected_action: Action,
    candidates: Vec<CandidateTrace>,
) -> DecisionTrace {
    let selected_action_id = selected_action.action_id();
    DecisionTrace {
        tick_before,
        agent_position,
        selected_action_id: selected_action_id.clone(),
        candidates: candidates
            .into_iter()
            .map(|mut candidate| {
                candidate.selected = candidate.action == selected_action;
                candidate
            })
            .collect(),
    }
}

fn shortest_safe_path_to_positive_goal(state: &SimState, start: Coord) -> Option<usize> {
    if !safe_path_cell(state, start, start) {
        return None;
    }
    let mut queue = VecDeque::from([(start, 0usize)]);
    let mut seen = HashSet::from([start]);
    while let Some((position, distance)) = queue.pop_front() {
        if state
            .map
            .cell(position)
            .and_then(CellKind::terminal_reward)
            .is_some_and(|reward| reward > 0.0)
        {
            return Some(distance);
        }
        for delta in cardinal_policy_directions() {
            let candidate = position.add(delta);
            if seen.contains(&candidate) || !safe_path_cell(state, candidate, start) {
                continue;
            }
            seen.insert(candidate);
            queue.push_back((candidate, distance + 1));
        }
    }
    None
}

fn safe_path_cell(state: &SimState, position: Coord, start: Coord) -> bool {
    let Some(cell) = state.map.cell(position) else {
        return false;
    };
    if matches!(cell, CellKind::Wall | CellKind::Hazard) {
        return false;
    }
    if position != start
        && state
            .entities
            .iter()
            .any(|entity| entity.id != "agent" && entity.position == position)
    {
        return false;
    }
    true
}

fn cardinal_policy_directions() -> [Coord; 4] {
    [
        Coord::new(1, 0, 0),
        Coord::new(0, 1, 0),
        Coord::new(0, -1, 0),
        Coord::new(-1, 0, 0),
    ]
}

fn agent_position(kernel: &DreamKernel) -> Result<Coord, String> {
    kernel
        .state
        .entity("agent")
        .map(|entity| entity.position)
        .ok_or_else(|| "missing agent".to_string())
}

fn branch_rank_top_match(sequence: &DreamSequence) -> bool {
    let Some(best_branch) = sequence.branch_matrix.iter().max_by(|left, right| {
        left.chrono_y_net
            .partial_cmp(&right.chrono_y_net)
            .unwrap_or(std::cmp::Ordering::Equal)
    }) else {
        return false;
    };
    sequence
        .frames
        .iter()
        .filter_map(|frame| frame.outcome.as_ref())
        .find(|outcome| outcome.reward > 0.0)
        .map(|outcome| outcome.branch_id == best_branch.branch_id)
        .unwrap_or(false)
}

fn scenario_result_to_json(row: &ScenarioResult) -> String {
    format!(
        "{{\"name\":\"{}\",\"solved\":{},\"final_reward\":{},\"terminal\":{},\"steps\":{},\"planned_actions\":{},\"final_reason\":\"{}\",\"sequence_file\":\"{}\",\"sequence_hash\":\"{}\",\"branch_rank_top_match\":{},\"accepted_steps\":{},\"rejected_steps\":{},\"invariant_passed\":{},\"decision_trace\":{}}}",
        json_escape(&row.name),
        row.solved,
        number_to_json(row.final_reward),
        row.terminal,
        row.steps,
        string_vec_to_json(&row.planned_actions),
        json_escape(&row.final_reason),
        json_escape(&row.sequence_file),
        json_escape(&row.sequence_hash),
        row.branch_rank_top_match,
        row.accepted_steps,
        row.rejected_steps,
        row.invariant_passed,
        decision_trace_to_json(&row.decision_trace)
    )
}

fn decision_trace_to_json(rows: &[DecisionTrace]) -> String {
    format!(
        "[{}]",
        rows.iter()
            .map(decision_trace_row_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn decision_trace_row_to_json(row: &DecisionTrace) -> String {
    format!(
        "{{\"tick_before\":{},\"agent_position\":{},\"selected_action_id\":\"{}\",\"candidates\":[{}]}}",
        row.tick_before,
        coord_to_json(row.agent_position),
        json_escape(&row.selected_action_id),
        row.candidates
            .iter()
            .map(candidate_trace_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn candidate_trace_to_json(row: &CandidateTrace) -> String {
    let next_position = row
        .next_position
        .map(coord_to_json)
        .unwrap_or_else(|| "null".to_string());
    format!(
        "{{\"action_id\":\"{}\",\"policy_score\":{},\"branch_chrono_y_net\":{},\"outcome_accepted\":{},\"outcome_reward\":{},\"outcome_terminal\":{},\"outcome_reason\":\"{}\",\"next_position\":{},\"safe_path_progress_delta\":{},\"safe_path_progress_bonus\":{},\"revisit_penalty_applied\":{},\"wait_penalty_applied\":{},\"selected\":{}}}",
        json_escape(&row.action_id),
        number_to_json(row.policy_score),
        number_to_json(row.branch_chrono_y_net),
        row.outcome_accepted,
        number_to_json(row.outcome_reward),
        row.outcome_terminal,
        json_escape(&row.outcome_reason),
        next_position,
        optional_i32_to_json(row.safe_path_progress_delta),
        number_to_json(row.safe_path_progress_bonus),
        row.revisit_penalty_applied,
        row.wait_penalty_applied,
        row.selected
    )
}

fn coord_to_json(coord: Coord) -> String {
    format!("{{\"x\":{},\"y\":{},\"z\":{}}}", coord.x, coord.y, coord.z)
}

fn optional_i32_to_json(value: Option<i32>) -> String {
    value
        .map(|value| value.to_string())
        .unwrap_or_else(|| "null".to_string())
}

fn i32_vec_to_json(values: &[i32]) -> String {
    format!(
        "[{}]",
        values
            .iter()
            .map(i32::to_string)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn string_option_to_json(value: Option<&str>) -> String {
    value
        .map(|text| format!("\"{}\"", json_escape(text)))
        .unwrap_or_else(|| "null".to_string())
}

fn string_vec_to_json(values: &[String]) -> String {
    format!(
        "[{}]",
        values
            .iter()
            .map(|value| format!("\"{}\"", json_escape(value)))
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn number_to_json(value: f32) -> String {
    if value.is_finite() {
        format!("{value:.6}")
    } else {
        "null".to_string()
    }
}

fn json_escape(value: &str) -> String {
    value
        .chars()
        .flat_map(|ch| match ch {
            '"' => "\\\"".chars().collect::<Vec<_>>(),
            '\\' => "\\\\".chars().collect::<Vec<_>>(),
            '\n' => "\\n".chars().collect::<Vec<_>>(),
            '\r' => "\\r".chars().collect::<Vec<_>>(),
            '\t' => "\\t".chars().collect::<Vec<_>>(),
            other => vec![other],
        })
        .collect()
}
