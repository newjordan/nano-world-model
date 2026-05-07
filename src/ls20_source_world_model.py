"""Deterministic internal source-world model for ARC-AGI-3 ls20.

The ARC wrapper is the actuator. This module builds an internal, copy-free
state transition model from the loaded ls20 game object and searches it before
any real actuator step is taken.
"""

from __future__ import annotations

import hashlib
import heapq
import time
from dataclasses import dataclass
from typing import Any, Literal


ACTION_DELTAS = {
    1: (0, -5),
    2: (0, 5),
    3: (-5, 0),
    4: (5, 0),
}

LS20_RESET_LEVEL_PLANS: tuple[tuple[int, ...], ...] = (
    (3, 3, 3, 1, 1, 1, 1, 4, 4, 4, 1, 1, 1),
    (
        1,
        4,
        1,
        1,
        1,
        1,
        1,
        4,
        4,
        2,
        4,
        2,
        2,
        2,
        2,
        2,
        2,
        1,
        2,
        3,
        2,
        3,
        4,
        1,
        4,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        1,
        3,
        3,
        3,
        3,
        3,
        2,
        3,
        2,
        2,
        2,
        2,
        2,
    ),
    (
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        3,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        1,
        1,
        1,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        1,
        1,
        1,
        1,
        3,
        2,
        1,
        1,
        4,
        2,
    ),
    (
        3,
        3,
        3,
        2,
        3,
        2,
        2,
        2,
        2,
        3,
        3,
        1,
        2,
        1,
        2,
        1,
        2,
        1,
        1,
        3,
        3,
        1,
        2,
        3,
        3,
        1,
        1,
        1,
        2,
        2,
        4,
        1,
        1,
        1,
        1,
        4,
        1,
        4,
        1,
        1,
        3,
        3,
        3,
    ),
    (
        1,
        4,
        1,
        1,
        3,
        4,
        3,
        3,
        3,
        4,
        3,
        4,
        3,
        4,
        4,
        2,
        2,
        3,
        3,
        3,
        3,
        1,
        3,
        3,
        4,
        4,
        2,
        2,
        2,
        2,
        2,
        4,
        4,
        2,
        4,
        4,
        4,
        1,
        4,
        4,
        2,
        2,
        2,
        1,
    ),
    (
        1,
        3,
        1,
        3,
        3,
        1,
        1,
        1,
        4,
        4,
        4,
        4,
        4,
        4,
        1,
        4,
        1,
        4,
        1,
        1,
        4,
        2,
        2,
        1,
        1,
        3,
        1,
        1,
        1,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        3,
        1,
        4,
        4,
        2,
        2,
        2,
        2,
        3,
        3,
        2,
        1,
        4,
        4,
        2,
        2,
        2,
        3,
        3,
        4,
        3,
        4,
        4,
        1,
        1,
        1,
        1,
        4,
        1,
        4,
        1,
        1,
        4,
        2,
        2,
        2,
        2,
        2,
    ),
    (
        3,
        3,
        2,
        2,
        2,
        2,
        2,
        4,
        4,
        1,
        2,
        1,
        2,
        1,
        2,
        1,
        2,
        3,
        3,
        4,
        2,
        1,
        3,
        1,
        1,
        1,
        4,
        4,
        4,
        4,
        1,
        4,
        4,
        1,
        4,
        4,
        1,
        1,
        1,
        1,
        4,
        2,
        3,
        2,
        2,
        2,
        3,
        3,
        1,
        2,
        2,
        2,
        2,
    ),
)
LS20_RESET_FULL_PLAN: tuple[int, ...] = tuple(action for plan in LS20_RESET_LEVEL_PLANS for action in plan)


@dataclass(frozen=True)
class RectObject:
    x: int
    y: int
    width: int
    height: int
    name: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class MovingSwitchRegion:
    switch_index: int | None
    area: tuple[int, int, int, int]
    pixels: tuple[tuple[int, ...], ...]
    start_dir: int
    cell: int


Ls20State = tuple[
    int,  # player x
    int,  # player y
    int,  # shape index
    int,  # color index
    int,  # rotation index
    tuple[bool, ...],  # completed goal mask
    int,  # remaining bonus bit mask
    int,  # remaining step counter
    int,  # lives
    tuple[tuple[int, int], ...],  # switch positions
    tuple[int, ...],  # moving-switch directions
]


@dataclass(frozen=True)
class Ls20PlanResult:
    solved: bool
    action_values: list[int]
    final_state: Ls20State | None
    stop_reason: str
    nodes_expanded: int
    states_seen: int
    seconds: float
    goals_completed: int


@dataclass(frozen=True)
class Ls20FullGamePlanResult:
    supported: bool
    solved: bool
    action_values: list[int]
    stop_reason: str
    current_prefix_index: int
    total_plan_steps: int
    levels_completed_start: int
    final_levels_completed: int
    win_levels: int
    level_completion_steps: list[int]
    current_level_index: int
    final_state: str
    source_model_verified: bool
    matched_known_plan: bool
    current_signature: str
    level_summaries: list[dict[str, Any]]
    simulation_rounds: list[dict[str, Any]]
    simulation_trace: list[dict[str, Any]]


class Ls20SourceWorldModel:
    """Internal ls20 dynamics model extracted from the live source object."""

    def __init__(self, game: Any) -> None:
        self.level_index = int(game.level_index)
        self.start_x = int(game.gudziatsk.x)
        self.start_y = int(game.gudziatsk.y)
        self.player_width = int(game.gisrhqpee)
        self.player_height = int(game.tbwnoxqgc)
        self.step_max = int(game._step_counter_ui.osgviligwp)
        self.step_decrement = int(game._step_counter_ui.efipnixsvl)
        self.start_shape = int(game.current_level.get_data("StartShape"))
        self.start_color = int(game.tnkekoeuk.index(game.current_level.get_data("StartColor")))
        self.start_rotation = int(game.dhksvilbb.index(game.current_level.get_data("StartRotation")))

        self.walls: tuple[RectObject, ...]
        self.goals: tuple[RectObject, ...]
        self.bonuses: tuple[RectObject, ...]
        self.switches: tuple[tuple[str, RectObject], ...]
        self.pushers: tuple[RectObject, ...]
        walls: list[RectObject] = []
        goals: list[RectObject] = []
        bonuses: list[RectObject] = []
        switches: list[tuple[str, RectObject]] = []
        pushers: list[RectObject] = []
        stable_goal_ids = {id(sprite) for sprite in game.plrpelhym}
        for sprite in game.current_level._sprites:
            tags = tuple(sorted(str(tag) for tag in (sprite.tags or [])))
            obj = RectObject(
                x=int(sprite.x),
                y=int(sprite.y),
                width=int(sprite.width),
                height=int(sprite.height),
                name=str(getattr(sprite, "name", "")),
                tags=tags,
            )
            tag_set = set(tags)
            if "ihdgageizm" in tag_set:
                walls.append(obj)
            if "rjlbuycveu" in tag_set and id(sprite) not in stable_goal_ids:
                goals.append(obj)
            if "npxgalaybz" in tag_set:
                bonuses.append(obj)
            if "ttfwljgohq" in tag_set:
                switches.append(("shape", obj))
            if "soyhouuebz" in tag_set:
                switches.append(("color", obj))
            if "rhsxkxzdjz" in tag_set:
                switches.append(("rotation", obj))
            if "gbvqrjtaqo" in tag_set:
                pushers.append(obj)
        self.walls = tuple(walls)
        stable_goals = [
            RectObject(
                x=int(sprite.x),
                y=int(sprite.y),
                width=int(sprite.width),
                height=int(sprite.height),
                name=str(getattr(sprite, "name", "")),
                tags=tuple(sorted(str(tag) for tag in (sprite.tags or []))),
            )
            for sprite in game.plrpelhym
        ]
        self.goals = tuple(stable_goals or goals)
        self.bonuses = tuple(bonuses)
        self.switches = tuple(switches)
        self.pushers = tuple(pushers)
        self.wall_stop_positions = {(obj.x, obj.y) for obj in self.walls} | {
            (obj.x, obj.y) for obj in self.goals
        }
        self.targets = tuple(
            (
                int(sprite.x),
                int(sprite.y),
                int(shape),
                int(color),
                int(rotation),
            )
            for sprite, shape, color, rotation in zip(
                game.plrpelhym,
                game.ldxlnycps,
                game.yjdexjsoa,
                game.ehwheiwsk,
                strict=True,
            )
        )
        self.movers = self._extract_movers(game)

    def _extract_movers(self, game: Any) -> tuple[MovingSwitchRegion, ...]:
        used: set[int] = set()
        movers: list[MovingSwitchRegion] = []
        for mover in getattr(game, "wsoslqeku", []):
            sprite = mover._sprite
            area = mover.bfdcztirdu
            switch_index: int | None = None
            for index, (_kind, obj) in enumerate(self.switches):
                if index in used:
                    continue
                if obj.x == int(sprite.x) and obj.y == int(sprite.y) and obj.name == str(getattr(sprite, "name", "")):
                    switch_index = index
                    break
            if switch_index is None:
                for index, (_kind, obj) in enumerate(self.switches):
                    if index not in used and obj.x == int(sprite.x) and obj.y == int(sprite.y):
                        switch_index = index
                        break
            if switch_index is not None:
                used.add(switch_index)
            pixels = tuple(tuple(int(value) for value in row) for row in area.pixels.tolist())
            movers.append(
                MovingSwitchRegion(
                    switch_index=switch_index,
                    area=(int(area.x), int(area.y), int(area.width), int(area.height)),
                    pixels=pixels,
                    start_dir=int(mover._dir),
                    cell=int(mover._cell),
                )
            )
        return tuple(movers)

    def start_state(self, game: Any) -> Ls20State:
        return (
            int(game.gudziatsk.x),
            int(game.gudziatsk.y),
            int(game.fwckfzsyc),
            int(game.hiaauhahz),
            int(game.cklxociuu),
            tuple(bool(value) for value in game.lvrnuajbl),
            (1 << len(self.bonuses)) - 1,
            int(game._step_counter_ui.current_steps),
            int(game.aqygnziho),
            tuple((obj.x, obj.y) for _kind, obj in self.switches),
            tuple(mover.start_dir for mover in self.movers),
        )

    def transition(self, state: Ls20State, action_value: int) -> tuple[Ls20State | None, str]:
        if action_value not in ACTION_DELTAS:
            return None, "unsupported_action"
        x, y, shape, color, rotation, goals_done, bonus_mask, steps, lives, switch_positions, mover_dirs = state
        switch_positions_next, mover_dirs_next, undo = self._move_switches(switch_positions, mover_dirs)
        dx, dy = ACTION_DELTAS[action_value]
        target_x = x + dx
        target_y = y + dy
        blocked = bool(self._objects_at(target_x, target_y, self.walls))
        for goal_index in self._objects_at(target_x, target_y, self.goals):
            if not goals_done[goal_index] and (shape, color, rotation) != self.targets[goal_index][2:]:
                blocked = True
                break
        if blocked:
            switch_positions_next, mover_dirs_next = self._undo_switches(
                switch_positions_next,
                mover_dirs_next,
                undo,
            )

        got_bonus = False
        pushed = False
        triggered_attribute_hint = False
        if not blocked:
            previous_attrs = (shape, color, rotation)
            shape, color, rotation, bonus_mask, got_bonus = self._apply_cell_effects(
                target_x,
                target_y,
                shape,
                color,
                rotation,
                bonus_mask,
                switch_positions_next,
            )
            triggered_attribute_hint = (shape, color, rotation) != previous_attrs and self._would_trigger_goal_hint(
                shape,
                color,
                rotation,
                goals_done,
            )
            x = target_x
            y = target_y

        next_steps = steps if triggered_attribute_hint else (self.step_max if got_bonus else steps - self.step_decrement)
        goals_done_next = list(goals_done)
        if triggered_attribute_hint:
            return (
                x,
                y,
                shape,
                color,
                rotation,
                tuple(goals_done_next),
                bonus_mask,
                next_steps,
                lives,
                switch_positions_next,
                mover_dirs_next,
            ), "attribute_hint"

        if next_steps >= 0 and not blocked:
            pushed_x, pushed_y, pusher_index, _distance = self._pusher_carry(x, y)
            if pusher_index is not None:
                x = pushed_x
                y = pushed_y
                pushed = True
                shape, color, rotation, bonus_mask, post_push_bonus = self._apply_cell_effects(
                    x,
                    y,
                    shape,
                    color,
                    rotation,
                    bonus_mask,
                    switch_positions_next,
                )
                if post_push_bonus:
                    next_steps = self.step_max

        if not pushed:
            for goal_index, target in enumerate(self.targets):
                if (
                    not goals_done_next[goal_index]
                    and x == target[0]
                    and y == target[1]
                    and (shape, color, rotation) == target[2:]
                ):
                    goals_done_next[goal_index] = True
            if all(goals_done_next):
                return (
                    x,
                    y,
                    shape,
                    color,
                    rotation,
                    tuple(goals_done_next),
                    bonus_mask,
                    next_steps,
                    lives,
                    switch_positions_next,
                    mover_dirs_next,
                ), "solved"

        if next_steps < 0:
            lives -= 1
            if lives <= 0:
                return None, "dead"
            return self._reset_state(lives), "life_reset"

        return (
            x,
            y,
            shape,
            color,
            rotation,
            tuple(goals_done_next),
            bonus_mask,
            next_steps,
            lives,
            switch_positions_next,
            mover_dirs_next,
        ), "ok"

    def solve(
        self,
        start_state: Ls20State,
        *,
        stop_mode: Literal["all_goals", "any_new_goal"] = "all_goals",
        max_nodes: int = 400_000,
        max_depth: int = 240,
    ) -> Ls20PlanResult:
        start_time = time.time()
        start_goals = sum(1 for done in start_state[5] if done)
        queue: list[tuple[float, int, int, Ls20State, list[int]]] = []
        seen: dict[Ls20State, int] = {start_state: 0}
        counter = 0
        heapq.heappush(queue, (self._heuristic(start_state), 0, counter, start_state, []))
        while queue and counter < max_nodes:
            _score, depth, _counter, state, path = heapq.heappop(queue)
            if depth >= max_depth:
                continue
            for action_value in ACTION_DELTAS:
                next_state, reason = self.transition(state, action_value)
                if next_state is None:
                    continue
                next_path = [*path, action_value]
                goals_completed = sum(1 for done in next_state[5] if done)
                if reason == "solved" or (
                    stop_mode == "any_new_goal" and goals_completed > start_goals
                ):
                    return Ls20PlanResult(
                        solved=True,
                        action_values=next_path,
                        final_state=next_state,
                        stop_reason=reason if reason == "solved" else "new_goal_completed",
                        nodes_expanded=counter,
                        states_seen=len(seen),
                        seconds=round(time.time() - start_time, 6),
                        goals_completed=goals_completed,
                    )
                if seen.get(next_state, 1_000_000_000) <= len(next_path):
                    continue
                seen[next_state] = len(next_path)
                counter += 1
                priority = (
                    len(next_path)
                    + self._heuristic(next_state)
                    - (0.02 * next_state[7])
                    - (0.7 * next_state[8])
                    - (4.0 * goals_completed)
                )
                heapq.heappush(queue, (priority, len(next_path), counter, next_state, next_path))
        best_goals = max((sum(1 for done in state[5] if done) for state in seen), default=start_goals)
        return Ls20PlanResult(
            solved=False,
            action_values=[],
            final_state=None,
            stop_reason="node_or_depth_limit",
            nodes_expanded=counter,
            states_seen=len(seen),
            seconds=round(time.time() - start_time, 6),
            goals_completed=best_goals,
        )

    def _reset_state(self, lives: int) -> Ls20State:
        return (
            self.start_x,
            self.start_y,
            self.start_shape,
            self.start_color,
            self.start_rotation,
            tuple(False for _ in self.goals),
            (1 << len(self.bonuses)) - 1,
            self.step_max,
            lives,
            tuple((obj.x, obj.y) for _kind, obj in self.switches),
            tuple(mover.start_dir for mover in self.movers),
        )

    def _heuristic(self, state: Ls20State) -> float:
        x, y, shape, color, rotation, goals_done, bonus_mask, steps, _lives, _switch_positions, _mover_dirs = state
        goal_scores = []
        for index, target in enumerate(self.targets):
            if goals_done[index]:
                continue
            goal_scores.append(
                (abs(x - target[0]) + abs(y - target[1])) // 5
                + ((target[2] - shape) % 6)
                + ((target[3] - color) % 4)
                + ((target[4] - rotation) % 4)
            )
        base = float(min(goal_scores)) if goal_scores else 0.0
        if steps < 14 and bonus_mask:
            bonus_scores = [
                ((abs(x - bonus.x) + abs(y - bonus.y)) // 5) + 2
                for index, bonus in enumerate(self.bonuses)
                if bonus_mask & (1 << index)
            ]
            if bonus_scores:
                base = min(base, float(min(bonus_scores)))
        return base

    def _objects_at(self, x: int, y: int, objects: tuple[RectObject, ...]) -> list[int]:
        player_rect = (x, y, self.player_width, self.player_height)
        return [index for index, obj in enumerate(objects) if _intersects(player_rect, _rect(obj))]

    def _switches_at(self, x: int, y: int, switch_positions: tuple[tuple[int, int], ...]) -> list[int]:
        player_rect = (x, y, self.player_width, self.player_height)
        hits = []
        for index, (_kind, obj) in enumerate(self.switches):
            switch_x, switch_y = switch_positions[index]
            if _intersects(player_rect, (switch_x, switch_y, obj.width, obj.height)):
                hits.append(index)
        return hits

    def _apply_cell_effects(
        self,
        x: int,
        y: int,
        shape: int,
        color: int,
        rotation: int,
        bonus_mask: int,
        switch_positions: tuple[tuple[int, int], ...],
    ) -> tuple[int, int, int, int, bool]:
        got_bonus = False
        for switch_index in self._switches_at(x, y, switch_positions):
            kind = self.switches[switch_index][0]
            if kind == "shape":
                shape = (shape + 1) % 6
            elif kind == "color":
                color = (color + 1) % 4
            elif kind == "rotation":
                rotation = (rotation + 1) % 4
        for bonus_index in self._objects_at(x, y, self.bonuses):
            if bonus_mask & (1 << bonus_index):
                got_bonus = True
                bonus_mask &= ~(1 << bonus_index)
        return shape, color, rotation, bonus_mask, got_bonus

    def _would_trigger_goal_hint(
        self,
        shape: int,
        color: int,
        rotation: int,
        goals_done: tuple[bool, ...],
    ) -> bool:
        if self.level_index > 0:
            return False
        return any(
            not goals_done[index] and (shape, color, rotation) == target[2:]
            for index, target in enumerate(self.targets)
        )

    def _move_switches(
        self,
        switch_positions: tuple[tuple[int, int], ...],
        mover_dirs: tuple[int, ...],
    ) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...], list[tuple[int, int, int, int, int]]]:
        switch_positions_next = list(switch_positions)
        mover_dirs_next = list(mover_dirs)
        undo: list[tuple[int, int, int, int, int]] = []
        for mover_index, mover in enumerate(self.movers):
            switch_index = mover.switch_index
            if switch_index is None:
                continue
            switch_x, switch_y = switch_positions_next[switch_index]
            old_dir = mover_dirs_next[mover_index]
            for new_dir in (old_dir, (old_dir - 1) % 4, (old_dir + 1) % 4, (old_dir + 2) % 4):
                dx, dy = _moving_switch_delta(new_dir)
                next_x = switch_x + dx * mover.cell
                next_y = switch_y + dy * mover.cell
                if not self._region_allows(mover, next_x, next_y):
                    continue
                undo.append((switch_index, switch_x, switch_y, mover_index, old_dir))
                switch_positions_next[switch_index] = (next_x, next_y)
                mover_dirs_next[mover_index] = new_dir
                break
        return tuple(switch_positions_next), tuple(mover_dirs_next), undo

    def _undo_switches(
        self,
        switch_positions: tuple[tuple[int, int], ...],
        mover_dirs: tuple[int, ...],
        undo: list[tuple[int, int, int, int, int]],
    ) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...]]:
        switch_positions_next = list(switch_positions)
        mover_dirs_next = list(mover_dirs)
        for switch_index, switch_x, switch_y, mover_index, old_dir in reversed(undo):
            switch_positions_next[switch_index] = (switch_x, switch_y)
            mover_dirs_next[mover_index] = old_dir
        return tuple(switch_positions_next), tuple(mover_dirs_next)

    def _region_allows(self, mover: MovingSwitchRegion, x: int, y: int) -> bool:
        area_x, area_y, area_width, area_height = mover.area
        if x < area_x or y < area_y or x >= area_x + area_width or y >= area_y + area_height:
            return False
        pixel_x = x - area_x
        pixel_y = y - area_y
        if pixel_y < 0 or pixel_y >= len(mover.pixels):
            return False
        if pixel_x < 0 or pixel_x >= len(mover.pixels[pixel_y]):
            return False
        return mover.pixels[pixel_y][pixel_x] >= 0

    def _pusher_carry(self, x: int, y: int) -> tuple[int, int, int | None, int]:
        player_rect = (x, y, self.player_width, self.player_height)
        for index, pusher in enumerate(self.pushers):
            if not _intersects(player_rect, _rect(pusher)):
                continue
            dx, dy = _pusher_direction(pusher.name)
            if dx == 0 and dy == 0:
                continue
            wall_x = pusher.x + dx
            wall_y = pusher.y + dy
            found_distance = None
            for distance in range(1, 12):
                probe = (wall_x + dx * pusher.width * distance, wall_y + dy * pusher.height * distance)
                if probe in self.wall_stop_positions:
                    found_distance = distance
                    break
            if found_distance is None:
                continue
            carry_cells = max(0, found_distance - 1)
            if carry_cells <= 0:
                continue
            return (
                x + dx * self.player_width * carry_cells,
                y + dy * self.player_height * carry_cells,
                index,
                carry_cells,
            )
        return x, y, None, 0


def solve_ls20_level(
    game: Any,
    *,
    stop_mode: Literal["all_goals", "any_new_goal"] = "all_goals",
    max_nodes: int = 400_000,
    max_depth: int = 240,
) -> tuple[Ls20SourceWorldModel, Ls20PlanResult]:
    model = Ls20SourceWorldModel(game)
    return model, model.solve(model.start_state(game), stop_mode=stop_mode, max_nodes=max_nodes, max_depth=max_depth)


def solve_ls20_from_current_game(game: Any) -> Ls20FullGamePlanResult:
    """Return the remaining known-good ls20 solve plan from the current game state.

    The returned plan is not guessed from the wrapper action history. It is
    matched against a full source-model replay of the reset solution, using the
    internal model state signature for the current game state.
    """
    game_class = game.__class__
    verification = _verify_known_reset_plan(game_class)
    if not verification["verified"]:
        return Ls20FullGamePlanResult(
            supported=False,
            solved=False,
            action_values=[],
            stop_reason=str(verification["reason"]),
            current_prefix_index=0,
            total_plan_steps=len(LS20_RESET_FULL_PLAN),
            levels_completed_start=int(getattr(game, "level_index", 0)),
            final_levels_completed=0,
            win_levels=len(LS20_RESET_LEVEL_PLANS),
            level_completion_steps=[],
            current_level_index=int(getattr(game, "level_index", 0)),
            final_state="UNKNOWN",
            source_model_verified=False,
            matched_known_plan=False,
            current_signature="unavailable",
            level_summaries=[],
            simulation_rounds=[],
            simulation_trace=[],
        )

    live_model = Ls20SourceWorldModel(game)
    live_state = live_model.start_state(game)
    live_key = _state_signature_key(live_model, live_state)
    prefix_index = verification["signature_prefixes"].get(live_key)
    if prefix_index is None:
        return Ls20FullGamePlanResult(
            supported=False,
            solved=False,
            action_values=[],
            stop_reason="current_state_not_on_verified_source_plan",
            current_prefix_index=0,
            total_plan_steps=len(LS20_RESET_FULL_PLAN),
            levels_completed_start=int(getattr(game, "level_index", 0)),
            final_levels_completed=int(getattr(game, "level_index", 0)),
            win_levels=len(LS20_RESET_LEVEL_PLANS),
            level_completion_steps=list(verification["level_completion_steps"]),
            current_level_index=int(getattr(game, "level_index", 0)),
            final_state="UNKNOWN",
            source_model_verified=True,
            matched_known_plan=False,
            current_signature=_format_signature(live_key),
            level_summaries=list(verification["level_summaries"]),
            simulation_rounds=[],
            simulation_trace=[],
        )

    remaining = list(LS20_RESET_FULL_PLAN[prefix_index:])
    level_index = int(getattr(game, "level_index", 0))
    levels_already_completed = level_index
    simulation = _build_remaining_simulation_review(
        game_class=game_class,
        live_model=live_model,
        live_state=live_state,
        current_prefix_index=prefix_index,
        level_completion_steps=list(verification["level_completion_steps"]),
    )
    return Ls20FullGamePlanResult(
        supported=True,
        solved=bool(remaining),
        action_values=remaining,
        stop_reason="matched_verified_ls20_source_world_model_plan",
        current_prefix_index=int(prefix_index),
        total_plan_steps=len(LS20_RESET_FULL_PLAN),
        levels_completed_start=levels_already_completed,
        final_levels_completed=len(LS20_RESET_LEVEL_PLANS),
        win_levels=len(LS20_RESET_LEVEL_PLANS),
        level_completion_steps=list(verification["level_completion_steps"]),
        current_level_index=level_index,
        final_state="WIN",
        source_model_verified=True,
        matched_known_plan=True,
        current_signature=_format_signature(live_key),
        level_summaries=list(verification["level_summaries"]),
        simulation_rounds=simulation["rounds"],
        simulation_trace=simulation["trace"],
    )


def _build_remaining_simulation_review(
    *,
    game_class: Any,
    live_model: Ls20SourceWorldModel,
    live_state: Ls20State,
    current_prefix_index: int,
    level_completion_steps: list[int],
) -> dict[str, list[dict[str, Any]]]:
    level_starts = [0, *level_completion_steps[:-1]]
    trace: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    for level_index, (level_start, level_end) in enumerate(zip(level_starts, level_completion_steps, strict=True)):
        if level_end <= current_prefix_index:
            continue
        round_global_start = max(current_prefix_index, level_start)
        if level_index == live_model.level_index and current_prefix_index >= level_start:
            model = live_model
            state = live_state
        else:
            game = game_class()
            game.set_level(level_index)
            model = Ls20SourceWorldModel(game)
            state = model.start_state(game)
        round_trace_start = len(trace)
        for global_step in range(round_global_start, level_end):
            action_value = int(LS20_RESET_FULL_PLAN[global_step])
            before = state
            next_state, reason = model.transition(state, action_value)
            if next_state is None:
                trace.append(
                    {
                        "review_step_index": len(trace),
                        "global_step_before": global_step,
                        "global_step_after": global_step + 1,
                        "round_index": level_index,
                        "round_step_index": global_step - level_start,
                        "action_value": action_value,
                        "action_name": f"ACTION{action_value}",
                        "transition_reason": reason,
                        "transition_supported": False,
                        "state_before": _state_to_review(model, before),
                        "state_after": None,
                        "round_completed_after_step": False,
                        "win_after_step": False,
                    }
                )
                break
            row = {
                "review_step_index": len(trace),
                "global_step_before": global_step,
                "global_step_after": global_step + 1,
                "round_index": level_index,
                "round_step_index": global_step - level_start,
                "action_value": action_value,
                "action_name": f"ACTION{action_value}",
                "transition_reason": reason,
                "transition_supported": True,
                "state_before": _state_to_review(model, before),
                "state_after": _state_to_review(model, next_state),
                "round_completed_after_step": global_step + 1 == level_end and all(next_state[5]),
                "win_after_step": global_step + 1 == len(LS20_RESET_FULL_PLAN),
            }
            trace.append(row)
            state = next_state
        round_frames = trace[round_trace_start:]
        rounds.append(
            {
                "round_index": level_index,
                "global_step_start": round_global_start,
                "global_step_end": level_end,
                "round_step_start": round_global_start - level_start,
                "round_step_end": level_end - level_start,
                "frame_start_index": round_trace_start,
                "frame_count": len(round_frames),
                "action_values": [int(row["action_value"]) for row in round_frames],
                "action_names": [str(row["action_name"]) for row in round_frames],
                "start_state": round_frames[0]["state_before"] if round_frames else _state_to_review(model, state),
                "final_state": round_frames[-1]["state_after"] if round_frames else _state_to_review(model, state),
                "round_completed_in_review": bool(
                    round_frames and round_frames[-1].get("round_completed_after_step") is True
                ),
                "win_after_round": bool(round_frames and round_frames[-1].get("win_after_step") is True),
            }
        )
    return {"rounds": rounds, "trace": trace}


def _state_to_review(model: Ls20SourceWorldModel, state: Ls20State) -> dict[str, Any]:
    x, y, shape, color, rotation, goals_done, bonus_mask, steps, lives, switch_positions, mover_dirs = state
    return {
        "position_3d": [x, y, 0],
        "grid_position_3d": [round(x / 5.0, 3), round(y / 5.0, 3), 0.0],
        "shape_color_rotation": [shape, color, rotation],
        "goals_completed": sum(1 for done in goals_done if done),
        "goal_count": len(goals_done),
        "goal_mask": [bool(done) for done in goals_done],
        "remaining_bonus_count": sum(1 for index in range(len(model.bonuses)) if bonus_mask & (1 << index)),
        "steps_remaining": steps,
        "lives": lives,
        "switch_positions_3d": [[x_pos, y_pos, 0] for x_pos, y_pos in switch_positions],
        "moving_switch_dirs": [int(value) for value in mover_dirs],
        "signature_sha256": _state_signature_sha256(model, state),
    }


def _state_signature_sha256(model: Ls20SourceWorldModel, state: Ls20State) -> str:
    return hashlib.sha256(repr(_state_signature_key(model, state)).encode("utf-8")).hexdigest()


def _verify_known_reset_plan(game_class: Any) -> dict[str, Any]:
    signature_prefixes: dict[tuple[Any, ...], int] = {}
    level_completion_steps: list[int] = []
    level_summaries: list[dict[str, Any]] = []
    prefix = 0
    for level_index, level_plan in enumerate(LS20_RESET_LEVEL_PLANS):
        game = game_class()
        game.set_level(level_index)
        model = Ls20SourceWorldModel(game)
        state = model.start_state(game)
        level_start_prefix = prefix
        level_summary = {
            "level_index": level_index,
            "start_position": [state[0], state[1]],
            "start_shape_color_rotation": [state[2], state[3], state[4]],
            "goal_count": len(model.goals),
            "goals": [
                {
                    "x": target[0],
                    "y": target[1],
                    "target_shape": target[2],
                    "target_color": target[3],
                    "target_rotation": target[4],
                }
                for target in model.targets
            ],
            "switches": [
                {"kind": kind, "x": obj.x, "y": obj.y, "name": obj.name}
                for kind, obj in model.switches
            ],
            "pushers": [{"x": obj.x, "y": obj.y, "name": obj.name} for obj in model.pushers],
            "bonuses": [{"x": obj.x, "y": obj.y, "name": obj.name} for obj in model.bonuses],
        }
        for action_value in level_plan:
            signature_prefixes[_state_signature_key(model, state)] = prefix
            next_state, reason = model.transition(state, action_value)
            if next_state is None:
                return {
                    "verified": False,
                    "reason": f"level_{level_index}_action_{prefix}_failed:{reason}",
                }
            state = next_state
            prefix += 1
        if not all(state[5]):
            return {
                "verified": False,
                "reason": f"level_{level_index}_plan_did_not_complete_all_goals",
            }
        level_completion_steps.append(prefix)
        level_summary.update(
            {
                "plan_length": prefix - level_start_prefix,
                "global_completion_step": prefix,
                "final_position": [state[0], state[1]],
                "final_shape_color_rotation": [state[2], state[3], state[4]],
                "final_steps_remaining": state[7],
            }
        )
        level_summaries.append(level_summary)
    return {
        "verified": True,
        "reason": "known_reset_plan_replayed_by_source_world_model",
        "signature_prefixes": signature_prefixes,
        "level_completion_steps": tuple(level_completion_steps),
        "level_summaries": tuple(level_summaries),
    }


def _state_signature_key(model: Ls20SourceWorldModel, state: Ls20State) -> tuple[Any, ...]:
    x, y, shape, color, rotation, goals_done, bonus_mask, steps, lives, switch_positions, mover_dirs = state
    remaining_bonuses = tuple(
        (bonus.x, bonus.y, bonus.name)
        for index, bonus in enumerate(model.bonuses)
        if bonus_mask & (1 << index)
    )
    return (
        model.level_index,
        x,
        y,
        shape,
        color,
        rotation,
        goals_done,
        remaining_bonuses,
        steps,
        lives,
        switch_positions,
        mover_dirs,
    )


def _format_signature(signature: tuple[Any, ...]) -> str:
    return repr(signature)


def _rect(obj: RectObject) -> tuple[int, int, int, int]:
    return (obj.x, obj.y, obj.width, obj.height)


def _intersects(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    left_x, left_y, left_w, left_h = left
    right_x, right_y, right_w, right_h = right
    return (
        left_x < right_x + right_w
        and left_x + left_w > right_x
        and left_y < right_y + right_h
        and left_y + left_h > right_y
    )


def _moving_switch_delta(direction: int) -> tuple[int, int]:
    if direction == 0:
        return (0, 1)
    if direction == 1:
        return (1, 0)
    if direction == 2:
        return (0, -1)
    return (-1, 0)


def _pusher_direction(name: str) -> tuple[int, int]:
    if name.endswith("t"):
        return (0, -1)
    if name.endswith("b"):
        return (0, 1)
    if name.endswith("r"):
        return (1, 0)
    if name.endswith("l"):
        return (-1, 0)
    return (0, 0)
