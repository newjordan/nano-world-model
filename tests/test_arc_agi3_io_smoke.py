import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts" / "run_arc_agi3_io_smoke.py"
    spec = importlib.util.spec_from_file_location("run_arc_agi3_io_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeFrame:
    shape = (64, 64)

    def tobytes(self):
        return bytes([3]) * (64 * 64)

    def min(self):
        return 0

    def max(self):
        return 12


class FakeAction:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class FakeInfo:
    game_id = "ls20-9607627b"


class FakeEnv:
    info = FakeInfo()
    action_space = [FakeAction("ACTION1", 1), FakeAction("ACTION2", 2)]


class FakeObs:
    game_id = "ls20-9607627b"
    guid = "obs-1"
    state = "NOT_FINISHED"
    levels_completed = 0
    win_levels = 7
    full_reset = True
    frame = [FakeFrame()]


def test_normalize_games_selects_requested_short_name():
    module = _load_module()
    games = module.normalize_games([type("Game", (), {"game_id": "ls20-9607627b", "title": "LS20"})()])

    assert module.select_game(games, "ls20")["game_id"] == "ls20-9607627b"


def test_observation_row_records_frame_digest_and_action_space():
    module = _load_module()
    row = module.observation_row(FakeObs(), env=FakeEnv(), game_name="ls20", phase="reset", step_index=0, executed_action=None)

    assert row["schema"] == module.ROW_SCHEMA
    assert row["latest_frame_shape"] == [64, 64]
    assert row["latest_frame_min"] == 0
    assert row["latest_frame_max"] == 12
    assert row["available_action_values"] == [1, 2]
    assert row["training_data_promoted"] is False
    assert row["arc_solve_claim"] is False


def test_candidate_action_packets_are_non_submission_packets():
    module = _load_module()
    packets = module.candidate_action_packets(
        env=FakeEnv(),
        game_name="ls20",
        observation_guid="obs-1",
        phase="reset",
        max_actions=8,
    )

    assert [packet["action_value"] for packet in packets] == [1, 2]
    assert all(packet["reasoning"]["submit_online"] is False for packet in packets)
    assert all(packet["arc_solve_claim"] is False for packet in packets)


def test_summarize_passes_only_with_64x64_frames_and_candidate_packets():
    module = _load_module()
    condition = {
        "selected_game": {"game_id": "ls20-9607627b", "name": "ls20"},
        "training_data_promoted": False,
        "arc_solve_claim": False,
        "online_submission": False,
    }
    row = module.observation_row(FakeObs(), env=FakeEnv(), game_name="ls20", phase="reset", step_index=0, executed_action=None)
    packets = module.candidate_action_packets(
        env=FakeEnv(),
        game_name="ls20",
        observation_guid="obs-1",
        phase="reset",
        max_actions=8,
    )
    metrics = module.summarize(condition=condition, games=[condition["selected_game"]], observation_rows=[row], candidate_packets=packets, executed_steps=0)

    assert metrics["valid_io_smoke"] is True
    assert metrics["frame_shapes"] == [[64, 64]]
    assert metrics["candidate_action_packets"] == 2
