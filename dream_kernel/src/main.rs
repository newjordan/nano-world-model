use dream_kernel::{
    compass_directions, demo_sequence, sequence_to_json, Action, Coord, DreamKernel, DreamSequence,
    SimState,
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
        _ => {
            eprintln!("usage: dream-kernel demo [--out PATH] | solve-suite --out-dir PATH");
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

fn run_scenario(scenario: Scenario, out_dir: &PathBuf) -> Result<ScenarioResult, String> {
    let state = SimState::from_ascii_layer(scenario.lines)?;
    let initial_state = state.clone();
    let mut kernel = DreamKernel::new(state);
    let directions = compass_directions();
    let mut actions = Vec::new();
    let mut planned_actions = Vec::new();
    let mut visited = vec![agent_position(&kernel)?];
    for _ in 0..scenario.max_steps {
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
    let final_outcome = sequence.frames.last().and_then(|frame| frame.outcome.as_ref());
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
    let sequence_file = format!("{}.dream_sequence.json", scenario.name);
    let sequence_json = sequence_to_json(&sequence);
    std::fs::write(out_dir.join(&sequence_file), format!("{sequence_json}\n"))
        .map_err(|error| format!("write {sequence_file}: {error}"))?;

    Ok(ScenarioResult {
        name: scenario.name.to_string(),
        solved: terminal && (final_reward - scenario.expected_reward).abs() < 0.0001,
        final_reward,
        terminal,
        steps: actions.len(),
        planned_actions,
        final_reason,
        sequence_file,
        sequence_hash: sequence.integrity.sequence_hash,
        branch_rank_top_match,
        accepted_steps,
        rejected_steps,
        invariant_passed: sequence.integrity.invariant_passed,
    })
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
        let outcome = sequence.frames.last().and_then(|frame| frame.outcome.as_ref());
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
