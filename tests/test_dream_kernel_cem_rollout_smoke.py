import torch
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_dream_kernel_cem_rollout_smoke.py"
    spec = importlib.util.spec_from_file_location("run_dream_kernel_cem_rollout_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_decode_action_vector_maps_continuous_actions_to_policy_ids():
    module = _load_module()

    assert module.decode_action_vector(torch.tensor([0.9, 0.1])).action_id == "move_entity_0_dx1_dy0_dz0"
    assert module.decode_action_vector(torch.tensor([-0.9, 0.1])).action_id == "move_entity_0_dx-1_dy0_dz0"
    assert module.decode_action_vector(torch.tensor([0.1, 0.9])).action_id == "move_entity_0_dx0_dy1_dz0"
    assert module.decode_action_vector(torch.tensor([0.1, -0.9])).action_id == "move_entity_0_dx0_dy-1_dz0"
    assert module.decode_action_vector(torch.tensor([0.01, 0.02])).action_id == "wait"


def test_map_world_model_rollout_reaches_goal_and_reports_safe_distance():
    module = _load_module()
    world = module.DreamKernelMapWorldModel(["#####", "#A.G#", "#...#", "#####"], horizon=4, device="cpu")
    actions = torch.tensor(
        [
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ]
    )

    result = world.evaluate_actions(actions)

    assert result["solved"] is True
    assert result["steps_to_goal"] == 2
    assert result["final_reward"] == 1.0
    assert result["final_safe_path_steps"] == 0
    assert result["planned_actions"][:2] == [
        "move_entity_0_dx1_dy0_dz0",
        "move_entity_0_dx1_dy0_dz0",
    ]


def test_cem_objective_prefers_goal_over_near_miss():
    module = _load_module()
    objective = module.create_cem_objective()
    pred = {
        "visual": torch.tensor(
            [
                [[0.5, 0.5, 1.0, 0.0, 0.0, 0.0]],
                [[0.5, 0.5, 0.0, 0.0, 0.0, 0.1]],
            ]
        )
    }
    loss = objective(pred, {"visual": pred["visual"]})

    assert loss[0] < loss[1]


def test_cem_planner_defaults_to_best_sample_return_policy():
    module = _load_module()
    world = module.DreamKernelMapWorldModel(["#####", "#A.G#", "#...#", "#####"], horizon=4, device="cpu")
    planner = module.CEMPlanner(
        world_model=world,
        objective_fn=module.create_cem_objective(),
        action_dim=module.ACTION_DIM,
        horizon=4,
        num_samples=2,
        topk=2,
        opt_steps=1,
        var_scale=0.0,
        eval_every=99,
        device="cpu",
    )
    warm_start = torch.tensor(
        [
            [
                [1.0, 0.0],
                [1.0, 0.0],
                [0.0, 0.0],
                [0.0, 0.0],
            ]
        ]
    )

    actions, info = planner.plan({"visual": world.start_obs()}, {"visual": world.goal_obs()}, actions=warm_start)
    result = world.evaluate_actions(actions[0])

    assert info["return_policy"] == "best_sample"
    assert info["best_loss"] == 0.0
    assert result["solved"] is True
