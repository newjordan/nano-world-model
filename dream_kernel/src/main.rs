use dream_kernel::{
    Action, Coord, DreamKernel, DreamSequence, SimState, compass_directions, demo_sequence,
    sequence_to_json,
};
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
        _ => {
            eprintln!(
                "usage: dream-kernel demo [--out PATH] | solve-suite --out-dir PATH | {}",
                solve_map_usage()
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
    let mut visited = vec![agent_position(&kernel)?];
    for _ in 0..max_steps {
        if kernel.state.terminal {
            break;
        }
        let best = choose_action(&kernel, &directions, &visited)?;
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
        },
    ))
}

fn choose_action(
    kernel: &DreamKernel,
    directions: &[Coord],
    visited: &[Coord],
) -> Result<Action, String> {
    let candidates = [
        Action::move_agent(Coord::new(1, 0, 0)),
        Action::move_agent(Coord::new(0, 1, 0)),
        Action::move_agent(Coord::new(0, -1, 0)),
        Action::move_agent(Coord::new(-1, 0, 0)),
        Action::Wait,
    ];
    let mut best: Option<(f32, Action)> = None;
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
        if let Some(outcome) = outcome {
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
        if matches!(action, Action::Wait) {
            score -= 0.45;
        }
        let next_position = sequence
            .frames
            .last()
            .and_then(|frame| frame.rays.first().map(|ray| ray.origin));
        if let Some(position) = next_position {
            if visited.contains(&position) {
                score -= 0.35;
            }
        }
        match best {
            None => best = Some((score, action)),
            Some((best_score, _)) if score > best_score => best = Some((score, action)),
            _ => {}
        }
    }
    best.map(|row| row.1)
        .ok_or_else(|| "no candidate action scored".to_string())
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
        "{{\"name\":\"{}\",\"solved\":{},\"final_reward\":{},\"terminal\":{},\"steps\":{},\"planned_actions\":{},\"final_reason\":\"{}\",\"sequence_file\":\"{}\",\"sequence_hash\":\"{}\",\"branch_rank_top_match\":{},\"accepted_steps\":{},\"rejected_steps\":{},\"invariant_passed\":{}}}",
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
        row.invariant_passed
    )
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
