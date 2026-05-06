use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct Coord {
    pub x: i32,
    pub y: i32,
    pub z: i32,
}

impl Coord {
    pub const fn new(x: i32, y: i32, z: i32) -> Self {
        Self { x, y, z }
    }

    pub const fn add(self, delta: Coord) -> Self {
        Self {
            x: self.x + delta.x,
            y: self.y + delta.y,
            z: self.z + delta.z,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CellKind {
    Empty,
    Wall,
    Goal,
    Hazard,
}

impl CellKind {
    pub const fn blocks_motion(self) -> bool {
        matches!(self, CellKind::Wall)
    }

    pub const fn terminal_reward(self) -> Option<f32> {
        match self {
            CellKind::Goal => Some(1.0),
            CellKind::Hazard => Some(-1.0),
            CellKind::Empty | CellKind::Wall => None,
        }
    }

    pub const fn as_str(self) -> &'static str {
        match self {
            CellKind::Empty => "empty",
            CellKind::Wall => "wall",
            CellKind::Goal => "goal",
            CellKind::Hazard => "hazard",
        }
    }

    pub fn object_id(self, position: Coord) -> Option<String> {
        match self {
            CellKind::Empty => None,
            CellKind::Wall | CellKind::Goal | CellKind::Hazard => Some(format!(
                "{}:{}:{}:{}",
                self.as_str(),
                position.x,
                position.y,
                position.z
            )),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EntityKind {
    Agent,
    Object,
}

impl EntityKind {
    pub const fn as_str(&self) -> &'static str {
        match self {
            EntityKind::Agent => "agent",
            EntityKind::Object => "object",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Entity {
    pub id: String,
    pub kind: EntityKind,
    pub position: Coord,
}

impl Entity {
    pub fn agent(id: impl Into<String>, position: Coord) -> Self {
        Self {
            id: id.into(),
            kind: EntityKind::Agent,
            position,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct KnownMap {
    pub width: usize,
    pub height: usize,
    pub depth: usize,
    cells: Vec<CellKind>,
}

impl KnownMap {
    pub fn new(
        width: usize,
        height: usize,
        depth: usize,
        cells: Vec<CellKind>,
    ) -> Result<Self, String> {
        if width == 0 || height == 0 || depth == 0 {
            return Err("map dimensions must be non-zero".to_string());
        }
        let expected = width
            .checked_mul(height)
            .and_then(|value| value.checked_mul(depth))
            .ok_or_else(|| "map dimensions overflow".to_string())?;
        if cells.len() != expected {
            return Err(format!("expected {expected} cells, got {}", cells.len()));
        }
        Ok(Self {
            width,
            height,
            depth,
            cells,
        })
    }

    pub fn cell(&self, coord: Coord) -> Option<CellKind> {
        self.index(coord).map(|index| self.cells[index])
    }

    pub fn in_bounds(&self, coord: Coord) -> bool {
        self.index(coord).is_some()
    }

    fn index(&self, coord: Coord) -> Option<usize> {
        if coord.x < 0 || coord.y < 0 || coord.z < 0 {
            return None;
        }
        let x = coord.x as usize;
        let y = coord.y as usize;
        let z = coord.z as usize;
        if x >= self.width || y >= self.height || z >= self.depth {
            return None;
        }
        Some(z * self.width * self.height + y * self.width + x)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SimState {
    pub map: KnownMap,
    pub entities: Vec<Entity>,
    pub tick: u32,
    pub terminal: bool,
}

impl SimState {
    pub fn from_ascii_layer(lines: &[&str]) -> Result<Self, String> {
        if lines.is_empty() {
            return Err("ascii layer must be non-empty".to_string());
        }
        let width = lines[0].chars().count();
        if width == 0 {
            return Err("ascii layer rows must be non-empty".to_string());
        }
        if lines.iter().any(|line| line.chars().count() != width) {
            return Err("ascii layer rows must have equal width".to_string());
        }

        let mut cells = Vec::with_capacity(width * lines.len());
        let mut entities = Vec::new();
        for (y, line) in lines.iter().enumerate() {
            for (x, ch) in line.chars().enumerate() {
                let coord = Coord::new(x as i32, y as i32, 0);
                match ch {
                    '.' => cells.push(CellKind::Empty),
                    '#' => cells.push(CellKind::Wall),
                    'G' => cells.push(CellKind::Goal),
                    'H' => cells.push(CellKind::Hazard),
                    'A' => {
                        cells.push(CellKind::Empty);
                        entities.push(Entity::agent("agent", coord));
                    }
                    'O' => {
                        cells.push(CellKind::Empty);
                        entities.push(Entity {
                            id: format!("object_{x}_{y}_0"),
                            kind: EntityKind::Object,
                            position: coord,
                        });
                    }
                    other => {
                        return Err(format!("unsupported ascii map character: {other:?}"));
                    }
                }
            }
        }
        if entities
            .iter()
            .filter(|entity| entity.kind == EntityKind::Agent)
            .count()
            != 1
        {
            return Err("ascii layer must contain exactly one agent 'A'".to_string());
        }
        Ok(Self {
            map: KnownMap::new(width, lines.len(), 1, cells)?,
            entities,
            tick: 0,
            terminal: false,
        })
    }

    pub fn entity(&self, id: &str) -> Option<&Entity> {
        self.entities.iter().find(|entity| entity.id == id)
    }

    pub fn entity_mut(&mut self, id: &str) -> Option<&mut Entity> {
        self.entities.iter_mut().find(|entity| entity.id == id)
    }

    pub fn occupied_by(&self, coord: Coord, except_id: Option<&str>) -> Option<&Entity> {
        self.entities
            .iter()
            .find(|entity| entity.position == coord && Some(entity.id.as_str()) != except_id)
    }

    pub fn render_top_down(&self) -> Vec<String> {
        let mut rows = Vec::with_capacity(self.map.height);
        for y in 0..self.map.height {
            let mut row = String::with_capacity(self.map.width);
            for x in 0..self.map.width {
                let coord = Coord::new(x as i32, y as i32, 0);
                if let Some(entity) = self.occupied_by(coord, None) {
                    row.push(match entity.kind {
                        EntityKind::Agent => 'A',
                        EntityKind::Object => 'O',
                    });
                    continue;
                }
                row.push(match self.map.cell(coord).unwrap_or(CellKind::Wall) {
                    CellKind::Empty => '.',
                    CellKind::Wall => '#',
                    CellKind::Goal => 'G',
                    CellKind::Hazard => 'H',
                });
            }
            rows.push(row);
        }
        rows
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Action {
    Wait,
    Move { entity_index: usize, delta: Coord },
}

impl Action {
    pub const fn move_agent(delta: Coord) -> Self {
        Self::Move {
            entity_index: 0,
            delta,
        }
    }

    pub fn action_id(self) -> String {
        match self {
            Action::Wait => "wait".to_string(),
            Action::Move {
                entity_index,
                delta,
            } => format!(
                "move_entity_{entity_index}_dx{}_dy{}_dz{}",
                delta.x, delta.y, delta.z
            ),
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct StepOutcome {
    pub tick_before: u32,
    pub tick_after: u32,
    pub action_id: String,
    pub branch_id: String,
    pub accepted: bool,
    pub reason: String,
    pub reward: f32,
    pub terminal: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ContactKind {
    Bounds,
    Wall,
    Goal,
    Hazard,
    Entity,
}

impl ContactKind {
    pub const fn as_str(&self) -> &'static str {
        match self {
            ContactKind::Bounds => "bounds",
            ContactKind::Wall => "wall",
            ContactKind::Goal => "goal",
            ContactKind::Hazard => "hazard",
            ContactKind::Entity => "entity",
        }
    }

    pub const fn network(&self) -> RayNetworkKind {
        match self {
            ContactKind::Goal => RayNetworkKind::Beneficial,
            ContactKind::Hazard => RayNetworkKind::Adversarial,
            ContactKind::Bounds | ContactKind::Wall => RayNetworkKind::Structural,
            ContactKind::Entity => RayNetworkKind::Neutral,
        }
    }

    pub const fn signed_potential_y(&self) -> f32 {
        match self {
            ContactKind::Goal => 1.0,
            ContactKind::Hazard => -1.0,
            ContactKind::Bounds | ContactKind::Wall => -0.25,
            ContactKind::Entity => 0.0,
        }
    }

    pub const fn potential_family(&self) -> &'static str {
        match self {
            ContactKind::Goal => "goal_progress.level_delta",
            ContactKind::Hazard => "hazard.env_failure",
            ContactKind::Bounds | ContactKind::Wall | ContactKind::Entity => {
                "mirror.progress_blocker"
            }
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RayNetworkKind {
    Beneficial,
    Adversarial,
    Structural,
    Neutral,
}

impl RayNetworkKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            RayNetworkKind::Beneficial => "beneficial",
            RayNetworkKind::Adversarial => "adversarial",
            RayNetworkKind::Structural => "structural",
            RayNetworkKind::Neutral => "neutral",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RayContact {
    pub object_id: String,
    pub category_id: String,
    pub position: Coord,
    pub kind: ContactKind,
    pub label: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct RayHit {
    pub origin: Coord,
    pub direction: Coord,
    pub path: Vec<Coord>,
    pub contact: RayContact,
    pub network: RayNetworkKind,
    pub signed_potential_y: f32,
    pub potential_family: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PotentialDatum {
    pub family: String,
    pub object_id: String,
    pub category_id: String,
    pub position: Coord,
    pub event_coord: EventCoord,
    pub chrono_y: f32,
    pub value: f32,
    pub network: RayNetworkKind,
    pub source: String,
    pub provenance: DatumProvenance,
}

impl PotentialDatum {
    pub fn new(
        family: impl Into<String>,
        object_id: impl Into<String>,
        position: Coord,
        value: f32,
        network: RayNetworkKind,
        source: impl Into<String>,
        tick: u32,
        action_id: Option<&str>,
        branch_id: Option<&str>,
        evidence: EvidenceKind,
        confidence: f32,
    ) -> Self {
        let chrono_y = value.clamp(-1.0, 1.0);
        let source = source.into();
        let object_id = object_id.into();
        Self {
            family: family.into(),
            category_id: category_id_for_object_id(&object_id),
            object_id,
            position,
            event_coord: EventCoord {
                t: tick,
                x: position.x as f32,
                y_chrono: chrono_y,
                z: position.y as f32,
            },
            chrono_y,
            value,
            network,
            source: source.clone(),
            provenance: DatumProvenance {
                source_type: source,
                source_tick: tick,
                action_id: action_id.map(str::to_string),
                branch_id: branch_id.map(str::to_string),
                evidence,
                confidence: confidence.clamp(0.0, 1.0),
            },
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct EventCoord {
    pub t: u32,
    pub x: f32,
    pub y_chrono: f32,
    pub z: f32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EvidenceKind {
    Imagined,
    Observed,
    Reconciled,
}

impl EvidenceKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            EvidenceKind::Imagined => "imagined",
            EvidenceKind::Observed => "observed",
            EvidenceKind::Reconciled => "reconciled",
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct DatumProvenance {
    pub source_type: String,
    pub source_tick: u32,
    pub action_id: Option<String>,
    pub branch_id: Option<String>,
    pub evidence: EvidenceKind,
    pub confidence: f32,
}

#[derive(Clone, Debug, PartialEq)]
pub struct OutcomeCalibration {
    pub imagined_chrono_y: f32,
    pub observed_chrono_y: Option<f32>,
    pub calibration_error: Option<f32>,
    pub calibrated_chrono_y: f32,
    pub source: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ChronometricFrame {
    pub source: String,
    pub event_mu: [f32; 4],
    pub branch_direction_n: [f32; 4],
    pub phase_theta: f32,
    pub signed_outcome_y: f32,
    pub outcome_calibration: OutcomeCalibration,
    pub potential_family_names: Vec<String>,
    pub potential_family_vector: Vec<f32>,
    pub potential_datapoints: Vec<PotentialDatum>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct FrameIntegrity {
    pub prev_frame_hash: Option<String>,
    pub frame_hash: String,
    pub invariant_passed: bool,
    pub invariant_errors: Vec<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct DreamFrame {
    pub tick: u32,
    pub render_top_down: Vec<String>,
    pub rays: Vec<RayHit>,
    pub chronometric: ChronometricFrame,
    pub outcome: Option<StepOutcome>,
    pub integrity: Option<FrameIntegrity>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ObjectRegistryEntry {
    pub object_id: String,
    pub kind: String,
    pub category_id: String,
    pub category_confidence: f32,
    pub open_tags: Vec<String>,
    pub hypothesis_refs: Vec<String>,
    pub map_coord: Option<Coord>,
    pub extent: Vec<Coord>,
    pub source: String,
    pub confidence: f32,
    pub dynamic: bool,
}

#[derive(Clone, Debug, PartialEq)]
pub struct BranchSummary {
    pub branch_id: String,
    pub action_id: String,
    pub start_tick: u32,
    pub end_tick: u32,
    pub map_anchor: Option<Coord>,
    pub chrono_y_net: f32,
    pub chrono_y_min: f32,
    pub positive_mass: f32,
    pub negative_exposure: f32,
    pub supporting_objects: Vec<String>,
    pub risk_objects: Vec<String>,
    pub frame_hash: Option<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct BranchPotential {
    pub potential_id: String,
    pub branch_id: String,
    pub object_id: String,
    pub category_id: String,
    pub event_coord: EventCoord,
    pub outcome_probability: f32,
    pub positive_probability: f32,
    pub negative_probability: f32,
    pub chrono_y_correlation: f32,
    pub uncertainty: f32,
    pub probability_source: String,
    pub relation_candidate_ids: Vec<String>,
    pub evidence_sources: Vec<String>,
    pub hypothesis: String,
    pub nemo_relay_required: bool,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ObjectLinkHypothesis {
    pub link_id: String,
    pub branch_id: String,
    pub source_object_id: String,
    pub target_object_id: String,
    pub relation_kind: String,
    pub probability: f32,
    pub chrono_y_correlation: f32,
    pub evidence_sources: Vec<String>,
    pub unresolved_questions: Vec<String>,
    pub nemo_relay_required: bool,
}

#[derive(Clone, Debug, PartialEq)]
pub struct NemoRelayQuestion {
    pub question_id: String,
    pub branch_id: Option<String>,
    pub object_id: Option<String>,
    pub link_id: Option<String>,
    pub prompt: String,
    pub hypothesis_refs: Vec<String>,
    pub expected_answer_shape: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct NemoRelayPacket {
    pub schema: String,
    pub relay_id: String,
    pub required_model: String,
    pub model_role: String,
    pub relay_status: String,
    pub branch_potential_ids: Vec<String>,
    pub object_link_ids: Vec<String>,
    pub open_questions: Vec<NemoRelayQuestion>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct SequenceIntegrity {
    pub sequence_hash: String,
    pub frame_count: usize,
    pub invariant_passed: bool,
    pub invariant_errors: Vec<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct DreamSequence {
    pub object_registry: Vec<ObjectRegistryEntry>,
    pub branch_matrix: Vec<BranchSummary>,
    pub branch_potentials: Vec<BranchPotential>,
    pub object_link_hypotheses: Vec<ObjectLinkHypothesis>,
    pub nemo_relay: NemoRelayPacket,
    pub integrity: SequenceIntegrity,
    pub frames: Vec<DreamFrame>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DreamKernel {
    pub state: SimState,
}

impl DreamKernel {
    pub fn new(state: SimState) -> Self {
        Self { state }
    }

    pub fn step(&mut self, action: Action) -> StepOutcome {
        let tick_before = self.state.tick;
        let action_id = action.action_id();
        let branch_id = format!("tick{tick_before}.{action_id}");
        if self.state.terminal {
            self.state.tick += 1;
            return StepOutcome {
                tick_before,
                tick_after: self.state.tick,
                action_id,
                branch_id,
                accepted: false,
                reason: "state already terminal".to_string(),
                reward: 0.0,
                terminal: true,
            };
        }

        let mut accepted = true;
        let mut reason = "wait".to_string();
        let mut reward = 0.0;
        let mut terminal = false;

        match action {
            Action::Wait => {}
            Action::Move {
                entity_index,
                delta,
            } => {
                let Some(entity) = self.state.entities.get(entity_index).cloned() else {
                    accepted = false;
                    reason = "missing entity".to_string();
                    self.state.tick += 1;
                    return StepOutcome {
                        tick_before,
                        tick_after: self.state.tick,
                        action_id,
                        branch_id,
                        accepted,
                        reason,
                        reward,
                        terminal,
                    };
                };
                let target = entity.position.add(delta);
                match self.state.map.cell(target) {
                    None => {
                        accepted = false;
                        reason = "blocked by bounds".to_string();
                    }
                    Some(cell) if cell.blocks_motion() => {
                        accepted = false;
                        reason = "blocked by wall".to_string();
                    }
                    Some(cell) => {
                        if self
                            .state
                            .occupied_by(target, Some(entity.id.as_str()))
                            .is_some()
                        {
                            accepted = false;
                            reason = "blocked by entity".to_string();
                        } else {
                            self.state.entities[entity_index].position = target;
                            reason = format!("moved into {}", cell.as_str());
                            if let Some(value) = cell.terminal_reward() {
                                reward = value;
                                terminal = true;
                                self.state.terminal = true;
                            }
                        }
                    }
                }
            }
        }

        self.state.tick += 1;
        StepOutcome {
            tick_before,
            tick_after: self.state.tick,
            action_id,
            branch_id,
            accepted,
            reason,
            reward,
            terminal,
        }
    }

    pub fn sense_from(
        &self,
        entity_id: &str,
        directions: &[Coord],
        max_range: usize,
    ) -> Result<Vec<RayHit>, String> {
        let origin = self
            .state
            .entity(entity_id)
            .ok_or_else(|| format!("missing entity: {entity_id}"))?
            .position;
        directions
            .iter()
            .map(|direction| self.cast_ray(origin, *direction, max_range, Some(entity_id)))
            .collect()
    }

    pub fn cast_ray(
        &self,
        origin: Coord,
        direction: Coord,
        max_range: usize,
        ignore_entity_id: Option<&str>,
    ) -> Result<RayHit, String> {
        if direction == Coord::new(0, 0, 0) {
            return Err("ray direction cannot be zero".to_string());
        }
        let mut path = Vec::new();
        let mut cursor = origin;
        let mut seen = HashSet::new();
        for _ in 0..max_range {
            cursor = cursor.add(direction);
            if !seen.insert(cursor) {
                return Err("ray repeated a coordinate".to_string());
            }
            if !self.state.map.in_bounds(cursor) {
                return Ok(make_ray_hit(
                    origin,
                    direction,
                    path,
                    RayContact {
                        object_id: format!("bounds:{}:{}:{}", cursor.x, cursor.y, cursor.z),
                        category_id: "synthetic.ray.boundary".to_string(),
                        position: cursor,
                        kind: ContactKind::Bounds,
                        label: "bounds".to_string(),
                    },
                ));
            }
            path.push(cursor);
            if let Some(entity) = self.state.occupied_by(cursor, ignore_entity_id) {
                return Ok(make_ray_hit(
                    origin,
                    direction,
                    path,
                    RayContact {
                        object_id: entity.id.clone(),
                        category_id: category_id_for_object_id(&entity.id),
                        position: cursor,
                        kind: ContactKind::Entity,
                        label: entity.kind.as_str().to_string(),
                    },
                ));
            }
            match self.state.map.cell(cursor).unwrap_or(CellKind::Wall) {
                CellKind::Empty => {}
                cell @ CellKind::Wall => {
                    return Ok(make_ray_hit(
                        origin,
                        direction,
                        path,
                        RayContact {
                            object_id: cell
                                .object_id(cursor)
                                .unwrap_or_else(|| "wall:unknown".to_string()),
                            category_id: "map.structural.wall".to_string(),
                            position: cursor,
                            kind: ContactKind::Wall,
                            label: cell.as_str().to_string(),
                        },
                    ));
                }
                cell @ CellKind::Goal => {
                    return Ok(make_ray_hit(
                        origin,
                        direction,
                        path,
                        RayContact {
                            object_id: cell
                                .object_id(cursor)
                                .unwrap_or_else(|| "goal:unknown".to_string()),
                            category_id: "map.terminal.positive".to_string(),
                            position: cursor,
                            kind: ContactKind::Goal,
                            label: cell.as_str().to_string(),
                        },
                    ));
                }
                cell @ CellKind::Hazard => {
                    return Ok(make_ray_hit(
                        origin,
                        direction,
                        path,
                        RayContact {
                            object_id: cell
                                .object_id(cursor)
                                .unwrap_or_else(|| "hazard:unknown".to_string()),
                            category_id: "map.terminal.negative".to_string(),
                            position: cursor,
                            kind: ContactKind::Hazard,
                            label: cell.as_str().to_string(),
                        },
                    ));
                }
            }
        }
        Ok(make_ray_hit(
            origin,
            direction,
            path,
            RayContact {
                object_id: format!("max_range:{}:{}:{}", cursor.x, cursor.y, cursor.z),
                category_id: "synthetic.ray.max_range".to_string(),
                position: cursor,
                kind: ContactKind::Bounds,
                label: "max_range".to_string(),
            },
        ))
    }

    pub fn rollout(
        &mut self,
        actions: &[Action],
        ray_directions: &[Coord],
        max_range: usize,
        sensor_entity_id: &str,
    ) -> Result<DreamSequence, String> {
        let mut object_registry = self.object_registry();
        let mut frames = Vec::with_capacity(actions.len() + 1);
        frames.push(self.frame(sensor_entity_id, ray_directions, max_range, None)?);
        for action in actions {
            let outcome = self.step(*action);
            frames.push(self.frame(sensor_entity_id, ray_directions, max_range, Some(outcome))?);
        }
        attach_frame_integrity(&mut frames, &object_registry);
        let branch_matrix = branch_matrix_from_frames(&frames);
        let mut branch_potentials = branch_potentials_from_frames(&frames, &object_registry);
        let object_link_hypotheses =
            object_link_hypotheses_from_branch_potentials(&mut branch_potentials);
        attach_hypothesis_refs(
            &mut object_registry,
            &branch_potentials,
            &object_link_hypotheses,
        );
        let nemo_relay = nemo_relay_from_potentials(&branch_potentials, &object_link_hypotheses);
        let integrity = sequence_integrity(
            &object_registry,
            &branch_matrix,
            &branch_potentials,
            &object_link_hypotheses,
            &nemo_relay,
            &frames,
        );
        Ok(DreamSequence {
            object_registry,
            branch_matrix,
            branch_potentials,
            object_link_hypotheses,
            nemo_relay,
            integrity,
            frames,
        })
    }

    fn object_registry(&self) -> Vec<ObjectRegistryEntry> {
        let mut registry = Vec::new();
        for z in 0..self.state.map.depth {
            for y in 0..self.state.map.height {
                for x in 0..self.state.map.width {
                    let position = Coord::new(x as i32, y as i32, z as i32);
                    let Some(cell) = self.state.map.cell(position) else {
                        continue;
                    };
                    let Some(object_id) = cell.object_id(position) else {
                        continue;
                    };
                    registry.push(ObjectRegistryEntry {
                        category_id: category_id_for_cell(cell)
                            .unwrap_or("map.cell.unknown")
                            .to_string(),
                        category_confidence: 1.0,
                        open_tags: open_tags_for_cell(cell),
                        hypothesis_refs: Vec::new(),
                        object_id,
                        kind: cell.as_str().to_string(),
                        map_coord: Some(position),
                        extent: vec![position],
                        source: "known_map.static_cell".to_string(),
                        confidence: 1.0,
                        dynamic: false,
                    });
                }
            }
        }
        for entity in &self.state.entities {
            registry.push(ObjectRegistryEntry {
                object_id: entity.id.clone(),
                kind: entity.kind.as_str().to_string(),
                category_id: category_id_for_entity_kind(&entity.kind).to_string(),
                category_confidence: 1.0,
                open_tags: open_tags_for_entity(entity),
                hypothesis_refs: Vec::new(),
                map_coord: Some(entity.position),
                extent: vec![entity.position],
                source: "sim_state.entity".to_string(),
                confidence: 1.0,
                dynamic: true,
            });
        }
        registry.sort_by(|left, right| left.object_id.cmp(&right.object_id));
        registry
    }

    fn frame(
        &self,
        sensor_entity_id: &str,
        ray_directions: &[Coord],
        max_range: usize,
        outcome: Option<StepOutcome>,
    ) -> Result<DreamFrame, String> {
        let rays = self.sense_from(sensor_entity_id, ray_directions, max_range)?;
        let chronometric = self.chronometric_frame(sensor_entity_id, &rays, outcome.as_ref())?;
        Ok(DreamFrame {
            tick: self.state.tick,
            render_top_down: self.state.render_top_down(),
            rays,
            chronometric,
            outcome,
            integrity: None,
        })
    }

    fn chronometric_frame(
        &self,
        sensor_entity_id: &str,
        rays: &[RayHit],
        outcome: Option<&StepOutcome>,
    ) -> Result<ChronometricFrame, String> {
        let sensor = self
            .state
            .entity(sensor_entity_id)
            .ok_or_else(|| format!("missing entity: {sensor_entity_id}"))?;
        let tick = self.state.tick;
        let action_id = outcome.map(|row| row.action_id.as_str());
        let branch_id = outcome.map(|row| row.branch_id.as_str());
        let signed_outcome_y = signed_outcome_from_step(outcome);
        let phase_theta = log_time_phase(tick);
        let mut potential_datapoints =
            self.known_map_terminal_potentials(tick, action_id, branch_id);
        potential_datapoints.extend(ray_contact_potentials(rays, tick, action_id, branch_id));
        potential_datapoints.extend(self.transition_potentials(
            sensor,
            outcome,
            phase_theta,
            tick,
            action_id,
            branch_id,
        ));
        let potential_family_names = POTENTIAL_FAMILY_ORDER
            .iter()
            .map(|name| (*name).to_string())
            .collect::<Vec<_>>();
        let potential_family_vector =
            potential_family_vector(&potential_datapoints, &potential_family_names);
        let branch_direction_n = branch_direction_from_rays(rays);
        let outcome_calibration = outcome_calibration(branch_direction_n[2], outcome);
        Ok(ChronometricFrame {
            source: CHRONOMETRIC_SOURCE.to_string(),
            event_mu: [
                self.state.tick as f32,
                normalized_coord(sensor.position.x, self.state.map.width),
                signed_outcome_y,
                normalized_coord(sensor.position.y, self.state.map.height),
            ],
            branch_direction_n,
            phase_theta,
            signed_outcome_y,
            outcome_calibration,
            potential_family_names,
            potential_family_vector,
            potential_datapoints,
        })
    }

    fn known_map_terminal_potentials(
        &self,
        tick: u32,
        action_id: Option<&str>,
        branch_id: Option<&str>,
    ) -> Vec<PotentialDatum> {
        let mut potentials = Vec::new();
        for z in 0..self.state.map.depth {
            for y in 0..self.state.map.height {
                for x in 0..self.state.map.width {
                    let position = Coord::new(x as i32, y as i32, z as i32);
                    let Some(cell) = self.state.map.cell(position) else {
                        continue;
                    };
                    let (family, value, network) = match cell {
                        CellKind::Goal => {
                            ("goal_progress.level_delta", 1.0, RayNetworkKind::Beneficial)
                        }
                        CellKind::Hazard => {
                            ("hazard.env_failure", -1.0, RayNetworkKind::Adversarial)
                        }
                        CellKind::Empty | CellKind::Wall => continue,
                    };
                    potentials.push(PotentialDatum::new(
                        family,
                        cell.object_id(position)
                            .unwrap_or_else(|| format!("cell:{}:{}:{}", x, y, z)),
                        position,
                        value,
                        network,
                        "known_map.static_terminal_cell",
                        tick,
                        action_id,
                        branch_id,
                        EvidenceKind::Imagined,
                        1.0,
                    ));
                }
            }
        }
        potentials
    }

    fn transition_potentials(
        &self,
        sensor: &Entity,
        outcome: Option<&StepOutcome>,
        phase_theta: f32,
        tick: u32,
        action_id: Option<&str>,
        branch_id: Option<&str>,
    ) -> Vec<PotentialDatum> {
        let mut potentials = Vec::new();
        potentials.push(PotentialDatum::new(
            "time_phase.repeated_effect_size",
            sensor.id.clone(),
            sensor.position,
            phase_theta.sin(),
            RayNetworkKind::Neutral,
            "chronometer.log_time_phase",
            tick,
            action_id,
            branch_id,
            EvidenceKind::Imagined,
            1.0,
        ));

        let Some(outcome) = outcome else {
            return potentials;
        };
        if outcome.accepted && outcome.reason.starts_with("moved") {
            potentials.push(PotentialDatum::new(
                "transition.changed_cells",
                sensor.id.clone(),
                sensor.position,
                1.0,
                RayNetworkKind::Neutral,
                "step.accepted_motion",
                tick,
                action_id,
                branch_id,
                EvidenceKind::Observed,
                1.0,
            ));
        }
        if !outcome.accepted || outcome.reason == "wait" {
            potentials.push(PotentialDatum::new(
                "stasis.no_change",
                sensor.id.clone(),
                sensor.position,
                1.0,
                RayNetworkKind::Structural,
                "step.no_state_change",
                tick,
                action_id,
                branch_id,
                EvidenceKind::Observed,
                1.0,
            ));
        }
        if outcome.reward != 0.0 {
            let (family, network) = if outcome.reward > 0.0 {
                ("goal_progress.level_delta", RayNetworkKind::Beneficial)
            } else {
                ("hazard.env_failure", RayNetworkKind::Adversarial)
            };
            let object_id = self
                .state
                .map
                .cell(sensor.position)
                .and_then(|cell| cell.object_id(sensor.position))
                .unwrap_or_else(|| sensor.id.clone());
            potentials.push(PotentialDatum::new(
                family,
                object_id,
                sensor.position,
                outcome.reward.clamp(-1.0, 1.0),
                network,
                "step.terminal_reward",
                tick,
                action_id,
                branch_id,
                EvidenceKind::Observed,
                1.0,
            ));
        }
        potentials
    }
}

pub const POTENTIAL_FAMILY_ORDER: [&str; 8] = [
    "transition.changed_cells",
    "time_phase.repeated_effect_size",
    "goal_progress.level_delta",
    "stasis.no_change",
    "loop.repeated_action",
    "mirror.progress_path",
    "mirror.progress_blocker",
    "hazard.env_failure",
];

const CHRONOMETRIC_SOURCE: &str = "dream_kernel_v001_deterministic_overlay";
const LOG_PHASE_LAMBDA: f32 = 3722.0 / 2705.0;

fn category_id_for_cell(cell: CellKind) -> Option<&'static str> {
    match cell {
        CellKind::Empty => None,
        CellKind::Wall => Some("map.structural.wall"),
        CellKind::Goal => Some("map.terminal.positive"),
        CellKind::Hazard => Some("map.terminal.negative"),
    }
}

fn category_id_for_entity_kind(kind: &EntityKind) -> &'static str {
    match kind {
        EntityKind::Agent => "entity.agent.self",
        EntityKind::Object => "object.unknown.open",
    }
}

fn category_id_for_object_id(object_id: &str) -> String {
    if object_id == "agent" {
        "entity.agent.self".to_string()
    } else if object_id.starts_with("goal:") {
        "map.terminal.positive".to_string()
    } else if object_id.starts_with("hazard:") {
        "map.terminal.negative".to_string()
    } else if object_id.starts_with("wall:") {
        "map.structural.wall".to_string()
    } else if object_id.starts_with("bounds:") {
        "synthetic.ray.boundary".to_string()
    } else if object_id.starts_with("max_range:") {
        "synthetic.ray.max_range".to_string()
    } else if object_id.starts_with("object_") {
        "object.unknown.open".to_string()
    } else {
        "object.unknown.open".to_string()
    }
}

fn open_tags_for_cell(cell: CellKind) -> Vec<String> {
    match cell {
        CellKind::Empty => vec!["map_cell".to_string(), "empty".to_string()],
        CellKind::Wall => vec![
            "map_cell".to_string(),
            "structural".to_string(),
            "occluder".to_string(),
            "blocks_motion".to_string(),
        ],
        CellKind::Goal => vec![
            "map_cell".to_string(),
            "terminal".to_string(),
            "outcome.positive".to_string(),
            "branch_reward_candidate".to_string(),
        ],
        CellKind::Hazard => vec![
            "map_cell".to_string(),
            "terminal".to_string(),
            "outcome.negative".to_string(),
            "branch_risk_candidate".to_string(),
        ],
    }
}

fn open_tags_for_entity(entity: &Entity) -> Vec<String> {
    let mut tags = match entity.kind {
        EntityKind::Agent => vec![
            "entity".to_string(),
            "controllable".to_string(),
            "self_anchor".to_string(),
            "branch_actor".to_string(),
        ],
        EntityKind::Object => vec![
            "entity".to_string(),
            "open_world".to_string(),
            "undefined_role".to_string(),
            "branch_candidate".to_string(),
        ],
    };
    tags.push(format!("instance:{}", entity.id));
    tags
}

fn make_ray_hit(origin: Coord, direction: Coord, path: Vec<Coord>, contact: RayContact) -> RayHit {
    RayHit {
        origin,
        direction,
        path,
        network: contact.kind.network(),
        signed_potential_y: contact.kind.signed_potential_y(),
        potential_family: contact.kind.potential_family().to_string(),
        contact,
    }
}

fn ray_contact_potentials(
    rays: &[RayHit],
    tick: u32,
    action_id: Option<&str>,
    branch_id: Option<&str>,
) -> Vec<PotentialDatum> {
    rays.iter()
        .map(|ray| {
            PotentialDatum::new(
                ray.potential_family.clone(),
                ray.contact.object_id.clone(),
                ray.contact.position,
                ray.signed_potential_y,
                ray.network,
                "ray_contact",
                tick,
                action_id,
                branch_id,
                EvidenceKind::Imagined,
                1.0,
            )
        })
        .collect()
}

fn potential_family_vector(datapoints: &[PotentialDatum], family_names: &[String]) -> Vec<f32> {
    family_names
        .iter()
        .map(|family| {
            datapoints
                .iter()
                .filter(|datum| datum.family == *family)
                .map(|datum| datum.value)
                .sum::<f32>()
                .clamp(-1.0, 1.0)
        })
        .collect()
}

fn branch_direction_from_rays(rays: &[RayHit]) -> [f32; 4] {
    let mut x = 0.0;
    let mut y_potential = 0.0;
    let mut z = 0.0;
    for ray in rays {
        let distance = ray.path.len().max(1) as f32;
        let weight = ray.signed_potential_y / distance;
        x += ray.direction.x as f32 * weight;
        y_potential += weight;
        z += ray.direction.y as f32 * weight;
    }
    let norm = (x * x + y_potential * y_potential + z * z).sqrt();
    if norm <= 1e-6 {
        return [0.0, 0.0, 0.0, 0.0];
    }
    [0.0, x / norm, y_potential / norm, z / norm]
}

fn signed_outcome_from_step(outcome: Option<&StepOutcome>) -> f32 {
    match outcome {
        Some(outcome) if outcome.reward > 0.0 => 1.0,
        Some(outcome) if outcome.reward < 0.0 => -1.0,
        Some(outcome) if !outcome.accepted => -0.25,
        _ => 0.0,
    }
}

fn log_time_phase(tick: u32) -> f32 {
    let tau = tick as f32 + 1.0;
    std::f32::consts::TAU / LOG_PHASE_LAMBDA.ln() * tau.ln()
}

fn normalized_coord(value: i32, span: usize) -> f32 {
    if span <= 1 {
        return 0.0;
    }
    (value as f32 / (span - 1) as f32).clamp(-1.0, 1.0)
}

fn outcome_calibration(
    imagined_chrono_y: f32,
    outcome: Option<&StepOutcome>,
) -> OutcomeCalibration {
    let observed_chrono_y = outcome.map(|row| signed_outcome_from_step(Some(row)));
    let calibration_error = observed_chrono_y.map(|observed| observed - imagined_chrono_y);
    OutcomeCalibration {
        imagined_chrono_y,
        observed_chrono_y,
        calibration_error,
        calibrated_chrono_y: observed_chrono_y.unwrap_or(imagined_chrono_y),
        source: if outcome.is_some() {
            "step_outcome_vs_ray_projection".to_string()
        } else {
            "ray_projection_only".to_string()
        },
    }
}

fn attach_frame_integrity(frames: &mut [DreamFrame], registry: &[ObjectRegistryEntry]) {
    let mut prev_frame_hash = None;
    for frame in frames {
        let invariant_errors = validate_frame(frame, registry);
        let frame_payload = frame_core_to_json(frame);
        let hash_payload = format!(
            "prev={};payload={frame_payload}",
            prev_frame_hash.as_deref().unwrap_or("")
        );
        let frame_hash = stable_hash_hex(&hash_payload);
        frame.integrity = Some(FrameIntegrity {
            prev_frame_hash: prev_frame_hash.clone(),
            frame_hash: frame_hash.clone(),
            invariant_passed: invariant_errors.is_empty(),
            invariant_errors,
        });
        prev_frame_hash = Some(frame_hash);
    }
}

fn sequence_integrity(
    registry: &[ObjectRegistryEntry],
    branch_matrix: &[BranchSummary],
    branch_potentials: &[BranchPotential],
    object_link_hypotheses: &[ObjectLinkHypothesis],
    nemo_relay: &NemoRelayPacket,
    frames: &[DreamFrame],
) -> SequenceIntegrity {
    let mut invariant_errors = validate_registry(registry);
    invariant_errors.extend(validate_branch_matrix(branch_matrix, registry, frames));
    invariant_errors.extend(validate_branch_potentials(
        branch_potentials,
        branch_matrix,
        registry,
    ));
    invariant_errors.extend(validate_object_link_hypotheses(
        object_link_hypotheses,
        branch_matrix,
        registry,
    ));
    invariant_errors.extend(validate_nemo_relay(
        nemo_relay,
        branch_matrix,
        registry,
        branch_potentials,
        object_link_hypotheses,
    ));
    for frame in frames {
        if let Some(integrity) = &frame.integrity {
            invariant_errors.extend(
                integrity
                    .invariant_errors
                    .iter()
                    .map(|error| format!("tick {}: {error}", frame.tick)),
            );
        } else {
            invariant_errors.push(format!("tick {}: missing frame integrity", frame.tick));
        }
    }
    let frame_hashes = frames
        .iter()
        .filter_map(|frame| {
            frame
                .integrity
                .as_ref()
                .map(|item| item.frame_hash.as_str())
        })
        .collect::<Vec<_>>()
        .join("|");
    let hash_payload = format!(
        "registry={};branches={};potentials={};links={};nemo={};frames={frame_hashes};errors={}",
        object_registry_to_json(registry),
        branch_matrix_to_json(branch_matrix),
        branch_potentials_to_json(branch_potentials),
        object_link_hypotheses_to_json(object_link_hypotheses),
        nemo_relay_to_json(nemo_relay),
        invariant_errors.join("|")
    );
    SequenceIntegrity {
        sequence_hash: stable_hash_hex(&hash_payload),
        frame_count: frames.len(),
        invariant_passed: invariant_errors.is_empty(),
        invariant_errors,
    }
}

fn validate_registry(registry: &[ObjectRegistryEntry]) -> Vec<String> {
    let mut errors = Vec::new();
    let mut ids = BTreeSet::new();
    let mut occupied = BTreeMap::new();
    for entry in registry {
        if entry.object_id.is_empty() {
            errors.push("registry entry has empty object_id".to_string());
        }
        if entry.category_id.is_empty() {
            errors.push(format!("object {} has empty category_id", entry.object_id));
        }
        if entry.kind.is_empty() {
            errors.push(format!("object {} has empty kind", entry.object_id));
        }
        if entry.source.is_empty() {
            errors.push(format!("object {} has empty source", entry.object_id));
        }
        if entry.open_tags.is_empty() {
            errors.push(format!("object {} has no open_tags", entry.object_id));
        }
        if !ids.insert(entry.object_id.as_str()) {
            errors.push(format!("duplicate object_id {}", entry.object_id));
        }
        if !entry.dynamic {
            if let Some(coord) = entry.map_coord {
                let key = (coord.x, coord.y, coord.z);
                if let Some(previous) = occupied.insert(key, entry.object_id.as_str()) {
                    errors.push(format!(
                        "static coord {:?} claimed by both {} and {}",
                        key, previous, entry.object_id
                    ));
                }
            } else {
                errors.push(format!(
                    "static object {} missing map_coord",
                    entry.object_id
                ));
            }
        }
        if !(0.0..=1.0).contains(&entry.confidence) {
            errors.push(format!(
                "object {} confidence out of range",
                entry.object_id
            ));
        }
        if !(0.0..=1.0).contains(&entry.category_confidence) {
            errors.push(format!(
                "object {} category_confidence out of range",
                entry.object_id
            ));
        }
    }
    errors
}

fn validate_frame(frame: &DreamFrame, registry: &[ObjectRegistryEntry]) -> Vec<String> {
    let mut errors = Vec::new();
    let registry_by_id = registry
        .iter()
        .map(|entry| (entry.object_id.as_str(), entry))
        .collect::<BTreeMap<_, _>>();
    for ray in &frame.rays {
        if ray.contact.object_id.is_empty() {
            errors.push("ray contact has empty object_id".to_string());
        }
        if ray.contact.category_id.is_empty() {
            errors.push(format!(
                "ray contact {} has empty category_id",
                ray.contact.object_id
            ));
        }
        if let Some(entry) = registry_by_id.get(ray.contact.object_id.as_str()) {
            if !entry.dynamic && entry.kind != ray.contact.kind.as_str() {
                errors.push(format!(
                    "ray contact {} kind {} disagrees with registry kind {}",
                    ray.contact.object_id,
                    ray.contact.kind.as_str(),
                    entry.kind
                ));
            }
        } else if !is_synthetic_contact_id(&ray.contact.object_id) {
            errors.push(format!(
                "ray contact {} missing from object registry",
                ray.contact.object_id
            ));
        }
    }
    for datum in &frame.chronometric.potential_datapoints {
        if datum.object_id.is_empty() {
            errors.push("potential datum has empty object_id".to_string());
        }
        if datum.category_id.is_empty() {
            errors.push(format!(
                "potential datum {} has empty category_id",
                datum.object_id
            ));
        }
        if datum.source.is_empty() {
            errors.push(format!(
                "potential datum {} missing source",
                datum.object_id
            ));
        }
        if !(0.0..=1.0).contains(&datum.provenance.confidence) {
            errors.push(format!(
                "potential datum {} confidence out of range",
                datum.object_id
            ));
        }
        if datum.event_coord.t != frame.tick {
            errors.push(format!(
                "potential datum {} event tick {} != frame tick {}",
                datum.object_id, datum.event_coord.t, frame.tick
            ));
        }
        if !approx_eq(datum.event_coord.x, datum.position.x as f32)
            || !approx_eq(datum.event_coord.z, datum.position.y as f32)
        {
            errors.push(format!(
                "potential datum {} event x/z not tethered to map coord {}",
                datum.object_id, datum.position
            ));
        }
        if !approx_eq(datum.event_coord.y_chrono, datum.chrono_y) {
            errors.push(format!(
                "potential datum {} event y_chrono != chrono_y",
                datum.object_id
            ));
        }
        if datum.network == RayNetworkKind::Beneficial && datum.chrono_y < -1e-5 {
            errors.push(format!(
                "beneficial datum {} has negative chrono_y {}",
                datum.object_id, datum.chrono_y
            ));
        }
        if datum.network == RayNetworkKind::Adversarial && datum.chrono_y > 1e-5 {
            errors.push(format!(
                "adversarial datum {} has positive chrono_y {}",
                datum.object_id, datum.chrono_y
            ));
        }
        if let Some(entry) = registry_by_id.get(datum.object_id.as_str()) {
            if !entry.dynamic && entry.map_coord != Some(datum.position) {
                errors.push(format!(
                    "potential datum {} map coord {} disagrees with registry",
                    datum.object_id, datum.position
                ));
            }
        } else if !is_synthetic_contact_id(&datum.object_id) {
            errors.push(format!(
                "potential datum {} missing from object registry",
                datum.object_id
            ));
        }
    }
    errors
}

fn validate_branch_matrix(
    branch_matrix: &[BranchSummary],
    registry: &[ObjectRegistryEntry],
    frames: &[DreamFrame],
) -> Vec<String> {
    let mut errors = Vec::new();
    let object_ids = registry
        .iter()
        .map(|entry| entry.object_id.as_str())
        .collect::<BTreeSet<_>>();
    let frame_hash_by_tick = frames
        .iter()
        .filter_map(|frame| {
            frame
                .integrity
                .as_ref()
                .map(|integrity| (frame.tick, integrity.frame_hash.as_str()))
        })
        .collect::<BTreeMap<_, _>>();
    let mut branch_ids = BTreeSet::new();
    for branch in branch_matrix {
        if branch.branch_id.is_empty() {
            errors.push("branch matrix row has empty branch_id".to_string());
        }
        if !branch_ids.insert(branch.branch_id.as_str()) {
            errors.push(format!("duplicate branch_id {}", branch.branch_id));
        }
        if branch.action_id.is_empty() {
            errors.push(format!("branch {} has empty action_id", branch.branch_id));
        }
        if branch.end_tick < branch.start_tick {
            errors.push(format!(
                "branch {} end_tick before start_tick",
                branch.branch_id
            ));
        }
        for object_id in branch
            .supporting_objects
            .iter()
            .chain(branch.risk_objects.iter())
        {
            if !object_ids.contains(object_id.as_str()) && !is_synthetic_contact_id(object_id) {
                errors.push(format!(
                    "branch {} references unknown object {}",
                    branch.branch_id, object_id
                ));
            }
        }
        match (&branch.frame_hash, frame_hash_by_tick.get(&branch.end_tick)) {
            (Some(branch_hash), Some(frame_hash)) if branch_hash != frame_hash => {
                errors.push(format!(
                    "branch {} frame_hash does not match end_tick frame",
                    branch.branch_id
                ));
            }
            (Some(_), None) => errors.push(format!(
                "branch {} references missing end_tick frame {}",
                branch.branch_id, branch.end_tick
            )),
            _ => {}
        }
    }
    errors
}

fn validate_branch_potentials(
    branch_potentials: &[BranchPotential],
    branch_matrix: &[BranchSummary],
    registry: &[ObjectRegistryEntry],
) -> Vec<String> {
    let mut errors = Vec::new();
    let branch_ids = branch_matrix
        .iter()
        .map(|branch| branch.branch_id.as_str())
        .collect::<BTreeSet<_>>();
    let object_ids = registry
        .iter()
        .map(|entry| entry.object_id.as_str())
        .collect::<BTreeSet<_>>();
    let mut potential_ids = BTreeSet::new();
    for potential in branch_potentials {
        if potential.potential_id.is_empty() {
            errors.push("branch potential has empty potential_id".to_string());
        }
        if !potential_ids.insert(potential.potential_id.as_str()) {
            errors.push(format!(
                "duplicate branch potential {}",
                potential.potential_id
            ));
        }
        if !branch_ids.contains(potential.branch_id.as_str()) {
            errors.push(format!(
                "branch potential {} references unknown branch {}",
                potential.potential_id, potential.branch_id
            ));
        }
        if potential.object_id.is_empty() {
            errors.push(format!(
                "branch potential {} has empty object_id",
                potential.potential_id
            ));
        }
        if !object_ids.contains(potential.object_id.as_str())
            && !is_synthetic_contact_id(&potential.object_id)
        {
            errors.push(format!(
                "branch potential {} references unknown object {}",
                potential.potential_id, potential.object_id
            ));
        }
        if potential.category_id.is_empty() {
            errors.push(format!(
                "branch potential {} has empty category_id",
                potential.potential_id
            ));
        }
        if !(-1.0..=1.0).contains(&potential.chrono_y_correlation) {
            errors.push(format!(
                "branch potential {} correlation out of range",
                potential.potential_id
            ));
        }
        for (name, value) in [
            ("outcome_probability", potential.outcome_probability),
            ("positive_probability", potential.positive_probability),
            ("negative_probability", potential.negative_probability),
            ("uncertainty", potential.uncertainty),
        ] {
            if !(0.0..=1.0).contains(&value) {
                errors.push(format!(
                    "branch potential {} {name} out of range",
                    potential.potential_id
                ));
            }
        }
        if !approx_eq(
            potential.event_coord.y_chrono,
            potential.chrono_y_correlation,
        ) {
            errors.push(format!(
                "branch potential {} event y_chrono != correlation",
                potential.potential_id
            ));
        }
    }
    errors
}

fn validate_object_link_hypotheses(
    object_link_hypotheses: &[ObjectLinkHypothesis],
    branch_matrix: &[BranchSummary],
    registry: &[ObjectRegistryEntry],
) -> Vec<String> {
    let mut errors = Vec::new();
    let branch_ids = branch_matrix
        .iter()
        .map(|branch| branch.branch_id.as_str())
        .collect::<BTreeSet<_>>();
    let object_ids = registry
        .iter()
        .map(|entry| entry.object_id.as_str())
        .collect::<BTreeSet<_>>();
    let mut link_ids = BTreeSet::new();
    for link in object_link_hypotheses {
        if link.link_id.is_empty() {
            errors.push("object link hypothesis has empty link_id".to_string());
        }
        if !link_ids.insert(link.link_id.as_str()) {
            errors.push(format!("duplicate object link {}", link.link_id));
        }
        if !branch_ids.contains(link.branch_id.as_str()) {
            errors.push(format!(
                "object link {} references unknown branch {}",
                link.link_id, link.branch_id
            ));
        }
        for object_id in [&link.source_object_id, &link.target_object_id] {
            if object_id.is_empty() {
                errors.push(format!("object link {} has empty object id", link.link_id));
            }
            if !object_ids.contains(object_id.as_str()) && !is_synthetic_contact_id(object_id) {
                errors.push(format!(
                    "object link {} references unknown object {}",
                    link.link_id, object_id
                ));
            }
        }
        if !(0.0..=1.0).contains(&link.probability) {
            errors.push(format!(
                "object link {} probability out of range",
                link.link_id
            ));
        }
        if !(-1.0..=1.0).contains(&link.chrono_y_correlation) {
            errors.push(format!(
                "object link {} correlation out of range",
                link.link_id
            ));
        }
        if link.relation_kind.is_empty() {
            errors.push(format!(
                "object link {} has empty relation_kind",
                link.link_id
            ));
        }
    }
    errors
}

fn validate_nemo_relay(
    nemo_relay: &NemoRelayPacket,
    branch_matrix: &[BranchSummary],
    registry: &[ObjectRegistryEntry],
    branch_potentials: &[BranchPotential],
    object_link_hypotheses: &[ObjectLinkHypothesis],
) -> Vec<String> {
    let mut errors = Vec::new();
    if nemo_relay.schema.is_empty() {
        errors.push("nemo relay has empty schema".to_string());
    }
    if nemo_relay.required_model.is_empty() {
        errors.push("nemo relay has empty required_model".to_string());
    }
    if nemo_relay.relay_status.is_empty() {
        errors.push("nemo relay has empty relay_status".to_string());
    }
    let potential_ids = branch_potentials
        .iter()
        .map(|potential| potential.potential_id.as_str())
        .collect::<BTreeSet<_>>();
    let branch_ids = branch_matrix
        .iter()
        .map(|branch| branch.branch_id.as_str())
        .collect::<BTreeSet<_>>();
    let object_ids = registry
        .iter()
        .map(|entry| entry.object_id.as_str())
        .collect::<BTreeSet<_>>();
    let link_ids = object_link_hypotheses
        .iter()
        .map(|link| link.link_id.as_str())
        .collect::<BTreeSet<_>>();
    for id in &nemo_relay.branch_potential_ids {
        if !potential_ids.contains(id.as_str()) {
            errors.push(format!(
                "nemo relay references unknown branch potential {id}"
            ));
        }
    }
    for id in &nemo_relay.object_link_ids {
        if !link_ids.contains(id.as_str()) {
            errors.push(format!("nemo relay references unknown object link {id}"));
        }
    }
    for question in &nemo_relay.open_questions {
        if question.question_id.is_empty() {
            errors.push("nemo relay question has empty question_id".to_string());
        }
        if question.prompt.is_empty() {
            errors.push(format!(
                "nemo relay question {} has empty prompt",
                question.question_id
            ));
        }
        if let Some(branch_id) = &question.branch_id {
            if !branch_ids.contains(branch_id.as_str()) {
                errors.push(format!(
                    "nemo relay question {} references unknown branch {}",
                    question.question_id, branch_id
                ));
            }
        }
        if let Some(object_id) = &question.object_id {
            if !object_ids.contains(object_id.as_str()) && !is_synthetic_contact_id(object_id) {
                errors.push(format!(
                    "nemo relay question {} references unknown object {}",
                    question.question_id, object_id
                ));
            }
        }
        if let Some(link_id) = &question.link_id {
            if !link_ids.contains(link_id.as_str()) {
                errors.push(format!(
                    "nemo relay question {} references unknown link {}",
                    question.question_id, link_id
                ));
            }
        }
        for id in &question.hypothesis_refs {
            if !potential_ids.contains(id.as_str()) && !link_ids.contains(id.as_str()) {
                errors.push(format!(
                    "nemo relay question {} references unknown hypothesis {}",
                    question.question_id, id
                ));
            }
        }
    }
    errors
}

fn branch_matrix_from_frames(frames: &[DreamFrame]) -> Vec<BranchSummary> {
    frames
        .iter()
        .filter_map(|frame| {
            let outcome = frame.outcome.as_ref()?;
            let mut positive_mass = 0.0;
            let mut negative_exposure = 0.0;
            let mut chrono_y_min = 0.0;
            let mut chrono_y_net = 0.0;
            let mut supporting_objects = BTreeSet::new();
            let mut risk_objects = BTreeSet::new();
            for datum in &frame.chronometric.potential_datapoints {
                let y = datum.chrono_y;
                chrono_y_net += y;
                chrono_y_min = f32::min(chrono_y_min, y);
                if y > 0.0 {
                    positive_mass += y;
                    supporting_objects.insert(datum.object_id.clone());
                } else if y < 0.0 {
                    negative_exposure += y;
                    risk_objects.insert(datum.object_id.clone());
                }
            }
            let terminal_calibrated_net = calibrated_branch_chrono_y_net(chrono_y_net, outcome);
            Some(BranchSummary {
                branch_id: outcome.branch_id.clone(),
                action_id: outcome.action_id.clone(),
                start_tick: outcome.tick_before,
                end_tick: outcome.tick_after,
                map_anchor: frame
                    .chronometric
                    .potential_datapoints
                    .iter()
                    .find(|datum| datum.object_id == "agent")
                    .map(|datum| datum.position),
                chrono_y_net: terminal_calibrated_net,
                chrono_y_min,
                positive_mass,
                negative_exposure,
                supporting_objects: supporting_objects.into_iter().collect(),
                risk_objects: risk_objects.into_iter().collect(),
                frame_hash: frame
                    .integrity
                    .as_ref()
                    .map(|integrity| integrity.frame_hash.clone()),
            })
        })
        .collect()
}

fn calibrated_branch_chrono_y_net(raw_chrono_y_net: f32, outcome: &StepOutcome) -> f32 {
    if outcome.terminal && outcome.reward > 0.0 {
        return 1.0;
    }
    if outcome.terminal && outcome.reward < 0.0 {
        return -1.0;
    }
    raw_chrono_y_net.clamp(-1.0, 0.99)
}

fn branch_potentials_from_frames(
    frames: &[DreamFrame],
    registry: &[ObjectRegistryEntry],
) -> Vec<BranchPotential> {
    let registry_by_id = registry
        .iter()
        .map(|entry| (entry.object_id.as_str(), entry))
        .collect::<BTreeMap<_, _>>();
    let mut potentials = Vec::new();
    for frame in frames {
        let Some(outcome) = frame.outcome.as_ref() else {
            continue;
        };
        for (index, datum) in frame.chronometric.potential_datapoints.iter().enumerate() {
            let category_id = registry_by_id
                .get(datum.object_id.as_str())
                .map(|entry| entry.category_id.clone())
                .unwrap_or_else(|| datum.category_id.clone());
            let correlation = datum.chrono_y.clamp(-1.0, 1.0);
            let positive_probability = clamped_probability(0.5 + 0.5 * correlation);
            let negative_probability = clamped_probability(0.5 - 0.5 * correlation);
            let outcome_probability = clamped_probability(0.5 + 0.5 * correlation.abs());
            let potential_id = format!(
                "bp:{}:{}:{}",
                id_fragment(&outcome.branch_id),
                id_fragment(&datum.object_id),
                index
            );
            let evidence_sources = vec![
                datum.source.clone(),
                datum.family.clone(),
                datum.provenance.evidence.as_str().to_string(),
            ];
            potentials.push(BranchPotential {
                potential_id,
                branch_id: outcome.branch_id.clone(),
                object_id: datum.object_id.clone(),
                category_id: category_id.clone(),
                event_coord: datum.event_coord,
                outcome_probability,
                positive_probability,
                negative_probability,
                chrono_y_correlation: correlation,
                uncertainty: 1.0 - datum.provenance.confidence.clamp(0.0, 1.0),
                probability_source: "chrono_y_linear_projection_v001".to_string(),
                relation_candidate_ids: Vec::new(),
                evidence_sources,
                hypothesis: format!(
                    "{} at {} may influence branch {} through {} with signed Chronometric Y {}",
                    category_id,
                    datum.position,
                    outcome.branch_id,
                    datum.family,
                    number_to_json(correlation)
                ),
                nemo_relay_required: true,
            });
        }
    }
    potentials
}

fn object_link_hypotheses_from_branch_potentials(
    branch_potentials: &mut [BranchPotential],
) -> Vec<ObjectLinkHypothesis> {
    let mut by_branch: BTreeMap<String, Vec<usize>> = BTreeMap::new();
    for (index, potential) in branch_potentials.iter().enumerate() {
        by_branch
            .entry(potential.branch_id.clone())
            .or_default()
            .push(index);
    }

    let mut links = Vec::new();
    for (branch_id, indexes) in by_branch {
        let mut seen_pairs = BTreeSet::new();
        let mut branch_links = Vec::new();
        for (left_offset, left_index) in indexes.iter().enumerate() {
            for right_index in indexes.iter().skip(left_offset + 1) {
                let left = &branch_potentials[*left_index];
                let right = &branch_potentials[*right_index];
                if left.object_id == right.object_id {
                    continue;
                }
                let pair = ordered_pair(&left.object_id, &right.object_id);
                if !seen_pairs.insert(pair.clone()) {
                    continue;
                }
                let correlation =
                    (left.chrono_y_correlation * right.chrono_y_correlation).clamp(-1.0, 1.0);
                let probability = clamped_probability(0.5 + 0.5 * correlation.abs());
                let link_id = format!(
                    "link:{}:{}:{}",
                    id_fragment(&branch_id),
                    id_fragment(&pair.0),
                    id_fragment(&pair.1)
                );
                branch_links.push(ObjectLinkHypothesis {
                    link_id,
                    branch_id: branch_id.clone(),
                    source_object_id: pair.0,
                    target_object_id: pair.1,
                    relation_kind: "branch.coactivation.open_relation".to_string(),
                    probability,
                    chrono_y_correlation: correlation,
                    evidence_sources: vec![
                        left.potential_id.clone(),
                        right.potential_id.clone(),
                        left.evidence_sources.join("+"),
                        right.evidence_sources.join("+"),
                    ],
                    unresolved_questions: vec![
                        "What semantic or causal relation, if any, connects these objects in this branch?"
                            .to_string(),
                        "Should the relation change the positive/negative branch potential?"
                            .to_string(),
                    ],
                    nemo_relay_required: true,
                });
            }
        }
        branch_links.sort_by(|left, right| {
            right
                .chrono_y_correlation
                .abs()
                .partial_cmp(&left.chrono_y_correlation.abs())
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        branch_links.truncate(24);
        links.extend(branch_links);
    }

    for link in &links {
        for potential in branch_potentials.iter_mut() {
            if potential.branch_id == link.branch_id
                && (potential.object_id == link.source_object_id
                    || potential.object_id == link.target_object_id)
            {
                potential.relation_candidate_ids.push(link.link_id.clone());
            }
        }
    }
    for potential in branch_potentials {
        potential.relation_candidate_ids.sort();
        potential.relation_candidate_ids.dedup();
    }
    links
}

fn attach_hypothesis_refs(
    registry: &mut [ObjectRegistryEntry],
    branch_potentials: &[BranchPotential],
    object_link_hypotheses: &[ObjectLinkHypothesis],
) {
    let mut refs_by_object: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for potential in branch_potentials {
        refs_by_object
            .entry(potential.object_id.clone())
            .or_default()
            .push(potential.potential_id.clone());
    }
    for link in object_link_hypotheses {
        refs_by_object
            .entry(link.source_object_id.clone())
            .or_default()
            .push(link.link_id.clone());
        refs_by_object
            .entry(link.target_object_id.clone())
            .or_default()
            .push(link.link_id.clone());
    }
    for entry in registry {
        if let Some(refs) = refs_by_object.get_mut(&entry.object_id) {
            refs.sort();
            refs.dedup();
            entry.hypothesis_refs = refs.clone();
        }
    }
}

fn nemo_relay_from_potentials(
    branch_potentials: &[BranchPotential],
    object_link_hypotheses: &[ObjectLinkHypothesis],
) -> NemoRelayPacket {
    let branch_potential_ids = branch_potentials
        .iter()
        .map(|potential| potential.potential_id.clone())
        .collect::<Vec<_>>();
    let object_link_ids = object_link_hypotheses
        .iter()
        .map(|link| link.link_id.clone())
        .collect::<Vec<_>>();
    let mut open_questions = Vec::new();
    for potential in branch_potentials.iter().filter(|potential| {
        potential.category_id.contains("unknown") || potential.chrono_y_correlation.abs() >= 0.75
    }) {
        open_questions.push(NemoRelayQuestion {
            question_id: format!("nq:{}", id_fragment(&potential.potential_id)),
            branch_id: Some(potential.branch_id.clone()),
            object_id: Some(potential.object_id.clone()),
            link_id: None,
            prompt: format!(
                "Evaluate whether object {} with category {} should keep, revise, or split its branch potential on {}. Hypothesis: {}",
                potential.object_id,
                potential.category_id,
                potential.branch_id,
                potential.hypothesis
            ),
            hypothesis_refs: vec![potential.potential_id.clone()],
            expected_answer_shape:
                "category_revision, relation_candidates, confidence, evidence_needed".to_string(),
        });
    }
    for link in object_link_hypotheses
        .iter()
        .filter(|link| link.probability >= 0.875)
        .take(96)
    {
        open_questions.push(NemoRelayQuestion {
            question_id: format!("nq:{}", id_fragment(&link.link_id)),
            branch_id: Some(link.branch_id.clone()),
            object_id: None,
            link_id: Some(link.link_id.clone()),
            prompt: format!(
                "Infer possible open-ended relations between {} and {} on branch {}. Do not force a closed label; return candidate relation names, correlation direction, confidence, and what evidence would confirm or reject them.",
                link.source_object_id, link.target_object_id, link.branch_id
            ),
            hypothesis_refs: vec![link.link_id.clone()],
            expected_answer_shape:
                "relation_candidates, correlation_direction, confidence, confirming_evidence"
                    .to_string(),
        });
    }
    NemoRelayPacket {
        schema: "dream_kernel.nemo_relay.v001".to_string(),
        relay_id: "dream_kernel.branch_potential_relay.v001".to_string(),
        required_model: "nemotron_3_nano_omni".to_string(),
        model_role: "semantic_thinking_relay_for_open_world_object_relations".to_string(),
        relay_status: "packet_ready_model_not_called".to_string(),
        branch_potential_ids,
        object_link_ids,
        open_questions,
    }
}

fn approx_eq(left: f32, right: f32) -> bool {
    (left - right).abs() <= 1e-5
}

fn is_synthetic_contact_id(object_id: &str) -> bool {
    object_id.starts_with("bounds:") || object_id.starts_with("max_range:")
}

fn clamped_probability(value: f32) -> f32 {
    value.clamp(0.0, 1.0)
}

fn ordered_pair(left: &str, right: &str) -> (String, String) {
    if left <= right {
        (left.to_string(), right.to_string())
    } else {
        (right.to_string(), left.to_string())
    }
}

fn id_fragment(value: &str) -> String {
    let mut fragment = value
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() {
                ch.to_ascii_lowercase()
            } else {
                '_'
            }
        })
        .collect::<String>();
    while fragment.contains("__") {
        fragment = fragment.replace("__", "_");
    }
    fragment.trim_matches('_').to_string()
}

fn stable_hash_hex(input: &str) -> String {
    let mut hash = 0xcbf29ce484222325u64;
    for byte in input.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{hash:016x}")
}

pub fn cardinal_directions() -> [Coord; 4] {
    [
        Coord::new(1, 0, 0),
        Coord::new(-1, 0, 0),
        Coord::new(0, 1, 0),
        Coord::new(0, -1, 0),
    ]
}

pub fn compass_directions() -> [Coord; 8] {
    [
        Coord::new(1, 0, 0),
        Coord::new(-1, 0, 0),
        Coord::new(0, 1, 0),
        Coord::new(0, -1, 0),
        Coord::new(1, 1, 0),
        Coord::new(1, -1, 0),
        Coord::new(-1, 1, 0),
        Coord::new(-1, -1, 0),
    ]
}

pub fn demo_sequence() -> Result<DreamSequence, String> {
    let state = SimState::from_ascii_layer(&["######", "#A.HG#", "#....#", "######"])?;
    let mut kernel = DreamKernel::new(state);
    let actions = [
        Action::move_agent(Coord::new(0, 1, 0)),
        Action::move_agent(Coord::new(1, 0, 0)),
        Action::move_agent(Coord::new(1, 0, 0)),
        Action::move_agent(Coord::new(1, 0, 0)),
        Action::move_agent(Coord::new(0, -1, 0)),
        Action::move_agent(Coord::new(1, 0, 0)),
    ];
    kernel.rollout(&actions, &compass_directions(), 16, "agent")
}

pub fn sequence_to_json(sequence: &DreamSequence) -> String {
    let object_registry = object_registry_to_json(&sequence.object_registry);
    let branch_matrix = branch_matrix_to_json(&sequence.branch_matrix);
    let branch_potentials = branch_potentials_to_json(&sequence.branch_potentials);
    let object_link_hypotheses = object_link_hypotheses_to_json(&sequence.object_link_hypotheses);
    let frames = sequence
        .frames
        .iter()
        .map(frame_to_json)
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "{{\"schema\":\"dream_kernel.sequence.v003\",\"object_registry\":{},\"branch_matrix\":{},\"branch_potentials\":{},\"object_link_hypotheses\":{},\"nemo_relay\":{},\"integrity\":{},\"frames\":[{frames}]}}",
        object_registry,
        branch_matrix,
        branch_potentials,
        object_link_hypotheses,
        nemo_relay_to_json(&sequence.nemo_relay),
        sequence_integrity_to_json(&sequence.integrity)
    )
}

fn frame_to_json(frame: &DreamFrame) -> String {
    format!(
        "{{{},\"integrity\":{}}}",
        frame_core_fields_to_json(frame),
        frame
            .integrity
            .as_ref()
            .map(frame_integrity_to_json)
            .unwrap_or_else(|| "null".to_string())
    )
}

fn frame_core_to_json(frame: &DreamFrame) -> String {
    format!("{{{}}}", frame_core_fields_to_json(frame))
}

fn frame_core_fields_to_json(frame: &DreamFrame) -> String {
    let rows = frame
        .render_top_down
        .iter()
        .map(|row| format!("\"{}\"", json_escape(row)))
        .collect::<Vec<_>>()
        .join(",");
    let rays = frame
        .rays
        .iter()
        .map(ray_to_json)
        .collect::<Vec<_>>()
        .join(",");
    let outcome = frame
        .outcome
        .as_ref()
        .map(outcome_to_json)
        .unwrap_or_else(|| "null".to_string());
    format!(
        "\"tick\":{},\"render_top_down\":[{}],\"rays\":[{}],\"chronometric\":{},\"outcome\":{}",
        frame.tick,
        rows,
        rays,
        chronometric_to_json(&frame.chronometric),
        outcome
    )
}

fn object_registry_to_json(registry: &[ObjectRegistryEntry]) -> String {
    format!(
        "[{}]",
        registry
            .iter()
            .map(object_registry_entry_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn object_registry_entry_to_json(entry: &ObjectRegistryEntry) -> String {
    let extent = entry
        .extent
        .iter()
        .map(coord_to_json)
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "{{\"object_id\":\"{}\",\"kind\":\"{}\",\"category_id\":\"{}\",\"category_confidence\":{},\"open_tags\":{},\"hypothesis_refs\":{},\"map_coord\":{},\"extent\":[{}],\"source\":\"{}\",\"confidence\":{},\"dynamic\":{}}}",
        json_escape(&entry.object_id),
        json_escape(&entry.kind),
        json_escape(&entry.category_id),
        number_to_json(entry.category_confidence),
        string_vec_to_json(&entry.open_tags),
        string_vec_to_json(&entry.hypothesis_refs),
        coord_option_to_json(entry.map_coord),
        extent,
        json_escape(&entry.source),
        number_to_json(entry.confidence),
        entry.dynamic
    )
}

fn branch_matrix_to_json(branches: &[BranchSummary]) -> String {
    format!(
        "[{}]",
        branches
            .iter()
            .map(branch_summary_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn branch_summary_to_json(branch: &BranchSummary) -> String {
    format!(
        "{{\"branch_id\":\"{}\",\"action_id\":\"{}\",\"start_tick\":{},\"end_tick\":{},\"map_anchor\":{},\"chrono_y_net\":{},\"chrono_y_min\":{},\"positive_mass\":{},\"negative_exposure\":{},\"supporting_objects\":{},\"risk_objects\":{},\"frame_hash\":{}}}",
        json_escape(&branch.branch_id),
        json_escape(&branch.action_id),
        branch.start_tick,
        branch.end_tick,
        coord_option_to_json(branch.map_anchor),
        number_to_json(branch.chrono_y_net),
        number_to_json(branch.chrono_y_min),
        number_to_json(branch.positive_mass),
        number_to_json(branch.negative_exposure),
        string_vec_to_json(&branch.supporting_objects),
        string_vec_to_json(&branch.risk_objects),
        string_option_to_json(branch.frame_hash.as_deref())
    )
}

fn branch_potentials_to_json(potentials: &[BranchPotential]) -> String {
    format!(
        "[{}]",
        potentials
            .iter()
            .map(branch_potential_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn branch_potential_to_json(potential: &BranchPotential) -> String {
    format!(
        "{{\"potential_id\":\"{}\",\"branch_id\":\"{}\",\"object_id\":\"{}\",\"category_id\":\"{}\",\"event_coord\":{},\"outcome_probability\":{},\"positive_probability\":{},\"negative_probability\":{},\"chrono_y_correlation\":{},\"uncertainty\":{},\"probability_source\":\"{}\",\"relation_candidate_ids\":{},\"evidence_sources\":{},\"hypothesis\":\"{}\",\"nemo_relay_required\":{}}}",
        json_escape(&potential.potential_id),
        json_escape(&potential.branch_id),
        json_escape(&potential.object_id),
        json_escape(&potential.category_id),
        event_coord_to_json(&potential.event_coord),
        number_to_json(potential.outcome_probability),
        number_to_json(potential.positive_probability),
        number_to_json(potential.negative_probability),
        number_to_json(potential.chrono_y_correlation),
        number_to_json(potential.uncertainty),
        json_escape(&potential.probability_source),
        string_vec_to_json(&potential.relation_candidate_ids),
        string_vec_to_json(&potential.evidence_sources),
        json_escape(&potential.hypothesis),
        potential.nemo_relay_required
    )
}

fn object_link_hypotheses_to_json(links: &[ObjectLinkHypothesis]) -> String {
    format!(
        "[{}]",
        links
            .iter()
            .map(object_link_hypothesis_to_json)
            .collect::<Vec<_>>()
            .join(",")
    )
}

fn object_link_hypothesis_to_json(link: &ObjectLinkHypothesis) -> String {
    format!(
        "{{\"link_id\":\"{}\",\"branch_id\":\"{}\",\"source_object_id\":\"{}\",\"target_object_id\":\"{}\",\"relation_kind\":\"{}\",\"probability\":{},\"chrono_y_correlation\":{},\"evidence_sources\":{},\"unresolved_questions\":{},\"nemo_relay_required\":{}}}",
        json_escape(&link.link_id),
        json_escape(&link.branch_id),
        json_escape(&link.source_object_id),
        json_escape(&link.target_object_id),
        json_escape(&link.relation_kind),
        number_to_json(link.probability),
        number_to_json(link.chrono_y_correlation),
        string_vec_to_json(&link.evidence_sources),
        string_vec_to_json(&link.unresolved_questions),
        link.nemo_relay_required
    )
}

fn nemo_relay_to_json(relay: &NemoRelayPacket) -> String {
    let questions = relay
        .open_questions
        .iter()
        .map(nemo_relay_question_to_json)
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "{{\"schema\":\"{}\",\"relay_id\":\"{}\",\"required_model\":\"{}\",\"model_role\":\"{}\",\"relay_status\":\"{}\",\"branch_potential_ids\":{},\"object_link_ids\":{},\"open_questions\":[{}]}}",
        json_escape(&relay.schema),
        json_escape(&relay.relay_id),
        json_escape(&relay.required_model),
        json_escape(&relay.model_role),
        json_escape(&relay.relay_status),
        string_vec_to_json(&relay.branch_potential_ids),
        string_vec_to_json(&relay.object_link_ids),
        questions
    )
}

fn nemo_relay_question_to_json(question: &NemoRelayQuestion) -> String {
    format!(
        "{{\"question_id\":\"{}\",\"branch_id\":{},\"object_id\":{},\"link_id\":{},\"prompt\":\"{}\",\"hypothesis_refs\":{},\"expected_answer_shape\":\"{}\"}}",
        json_escape(&question.question_id),
        string_option_to_json(question.branch_id.as_deref()),
        string_option_to_json(question.object_id.as_deref()),
        string_option_to_json(question.link_id.as_deref()),
        json_escape(&question.prompt),
        string_vec_to_json(&question.hypothesis_refs),
        json_escape(&question.expected_answer_shape)
    )
}

fn sequence_integrity_to_json(integrity: &SequenceIntegrity) -> String {
    format!(
        "{{\"sequence_hash\":\"{}\",\"frame_count\":{},\"invariant_passed\":{},\"invariant_errors\":{}}}",
        json_escape(&integrity.sequence_hash),
        integrity.frame_count,
        integrity.invariant_passed,
        string_vec_to_json(&integrity.invariant_errors)
    )
}

fn frame_integrity_to_json(integrity: &FrameIntegrity) -> String {
    format!(
        "{{\"prev_frame_hash\":{},\"frame_hash\":\"{}\",\"invariant_passed\":{},\"invariant_errors\":{}}}",
        string_option_to_json(integrity.prev_frame_hash.as_deref()),
        json_escape(&integrity.frame_hash),
        integrity.invariant_passed,
        string_vec_to_json(&integrity.invariant_errors)
    )
}

fn ray_to_json(ray: &RayHit) -> String {
    let path = ray
        .path
        .iter()
        .map(coord_to_json)
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "{{\"origin\":{},\"direction\":{},\"path\":[{}],\"network\":\"{}\",\"signed_potential_y\":{},\"potential_family\":\"{}\",\"contact\":{{\"object_id\":\"{}\",\"category_id\":\"{}\",\"position\":{},\"kind\":\"{}\",\"label\":\"{}\"}}}}",
        coord_to_json(&ray.origin),
        coord_to_json(&ray.direction),
        path,
        ray.network.as_str(),
        number_to_json(ray.signed_potential_y),
        json_escape(&ray.potential_family),
        json_escape(&ray.contact.object_id),
        json_escape(&ray.contact.category_id),
        coord_to_json(&ray.contact.position),
        ray.contact.kind.as_str(),
        json_escape(&ray.contact.label)
    )
}

fn chronometric_to_json(chronometric: &ChronometricFrame) -> String {
    let names = chronometric
        .potential_family_names
        .iter()
        .map(|name| format!("\"{}\"", json_escape(name)))
        .collect::<Vec<_>>()
        .join(",");
    let vector = chronometric
        .potential_family_vector
        .iter()
        .map(|value| number_to_json(*value))
        .collect::<Vec<_>>()
        .join(",");
    let datapoints = chronometric
        .potential_datapoints
        .iter()
        .map(potential_datum_to_json)
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "{{\"source\":\"{}\",\"event_mu\":{},\"branch_direction_n\":{},\"phase_theta\":{},\"signed_outcome_y\":{},\"outcome_calibration\":{},\"potential_family_names\":[{}],\"potential_family_vector\":[{}],\"potential_datapoints\":[{}]}}",
        json_escape(&chronometric.source),
        vector4_to_json(&chronometric.event_mu),
        vector4_to_json(&chronometric.branch_direction_n),
        number_to_json(chronometric.phase_theta),
        number_to_json(chronometric.signed_outcome_y),
        outcome_calibration_to_json(&chronometric.outcome_calibration),
        names,
        vector,
        datapoints
    )
}

fn potential_datum_to_json(datum: &PotentialDatum) -> String {
    format!(
        "{{\"family\":\"{}\",\"object_id\":\"{}\",\"category_id\":\"{}\",\"position\":{},\"map_coord\":{},\"event_coord\":{},\"chrono_y\":{},\"value\":{},\"network\":\"{}\",\"source\":\"{}\",\"provenance\":{}}}",
        json_escape(&datum.family),
        json_escape(&datum.object_id),
        json_escape(&datum.category_id),
        coord_to_json(&datum.position),
        coord_to_json(&datum.position),
        event_coord_to_json(&datum.event_coord),
        number_to_json(datum.chrono_y),
        number_to_json(datum.value),
        datum.network.as_str(),
        json_escape(&datum.source),
        datum_provenance_to_json(&datum.provenance)
    )
}

fn outcome_calibration_to_json(calibration: &OutcomeCalibration) -> String {
    format!(
        "{{\"imagined_chrono_y\":{},\"observed_chrono_y\":{},\"calibration_error\":{},\"calibrated_chrono_y\":{},\"source\":\"{}\"}}",
        number_to_json(calibration.imagined_chrono_y),
        number_option_to_json(calibration.observed_chrono_y),
        number_option_to_json(calibration.calibration_error),
        number_to_json(calibration.calibrated_chrono_y),
        json_escape(&calibration.source)
    )
}

fn datum_provenance_to_json(provenance: &DatumProvenance) -> String {
    format!(
        "{{\"source_type\":\"{}\",\"source_tick\":{},\"action_id\":{},\"branch_id\":{},\"evidence\":\"{}\",\"confidence\":{}}}",
        json_escape(&provenance.source_type),
        provenance.source_tick,
        string_option_to_json(provenance.action_id.as_deref()),
        string_option_to_json(provenance.branch_id.as_deref()),
        provenance.evidence.as_str(),
        number_to_json(provenance.confidence)
    )
}

fn event_coord_to_json(coord: &EventCoord) -> String {
    format!(
        "{{\"t\":{},\"x\":{},\"y_chrono\":{},\"z\":{}}}",
        coord.t,
        number_to_json(coord.x),
        number_to_json(coord.y_chrono),
        number_to_json(coord.z)
    )
}

fn vector4_to_json(vector: &[f32; 4]) -> String {
    format!(
        "[{},{},{},{}]",
        number_to_json(vector[0]),
        number_to_json(vector[1]),
        number_to_json(vector[2]),
        number_to_json(vector[3])
    )
}

fn outcome_to_json(outcome: &StepOutcome) -> String {
    format!(
        "{{\"tick_before\":{},\"tick_after\":{},\"action_id\":\"{}\",\"branch_id\":\"{}\",\"accepted\":{},\"reason\":\"{}\",\"reward\":{},\"terminal\":{}}}",
        outcome.tick_before,
        outcome.tick_after,
        json_escape(&outcome.action_id),
        json_escape(&outcome.branch_id),
        outcome.accepted,
        json_escape(&outcome.reason),
        outcome.reward,
        outcome.terminal
    )
}

fn coord_to_json(coord: &Coord) -> String {
    format!("{{\"x\":{},\"y\":{},\"z\":{}}}", coord.x, coord.y, coord.z)
}

fn coord_option_to_json(coord: Option<Coord>) -> String {
    coord
        .as_ref()
        .map(coord_to_json)
        .unwrap_or_else(|| "null".to_string())
}

fn number_to_json(value: f32) -> String {
    let value = if value.abs() < 0.0000005 { 0.0 } else { value };
    if value.is_finite() {
        format!("{value:.6}")
    } else {
        "0.000000".to_string()
    }
}

fn number_option_to_json(value: Option<f32>) -> String {
    value
        .map(number_to_json)
        .unwrap_or_else(|| "null".to_string())
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

impl fmt::Display for Coord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "({}, {}, {})", self.x, self.y, self.z)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_known_map_and_renders_agent_position() {
        let state = SimState::from_ascii_layer(&["#####", "#A.G#", "#...#", "#####"]).unwrap();

        assert_eq!(state.map.width, 5);
        assert_eq!(state.map.height, 4);
        assert_eq!(state.entity("agent").unwrap().position, Coord::new(1, 1, 0));
        assert_eq!(state.render_top_down()[1], "#A.G#");
    }

    #[test]
    fn rejects_motion_into_wall_without_mutating_position() {
        let state = SimState::from_ascii_layer(&["#####", "#A..#", "#####"]).unwrap();
        let mut kernel = DreamKernel::new(state);

        let outcome = kernel.step(Action::move_agent(Coord::new(0, -1, 0)));

        assert!(!outcome.accepted);
        assert_eq!(outcome.reason, "blocked by wall");
        assert_eq!(
            kernel.state.entity("agent").unwrap().position,
            Coord::new(1, 1, 0)
        );
    }

    #[test]
    fn ray_reports_hazard_before_goal() {
        let state = SimState::from_ascii_layer(&["######", "#A.HG#", "######"]).unwrap();
        let kernel = DreamKernel::new(state);

        let ray = kernel
            .cast_ray(Coord::new(1, 1, 0), Coord::new(1, 0, 0), 16, Some("agent"))
            .unwrap();

        assert_eq!(ray.path, vec![Coord::new(2, 1, 0), Coord::new(3, 1, 0)]);
        assert_eq!(ray.contact.kind, ContactKind::Hazard);
        assert_eq!(ray.contact.object_id, "hazard:3:1:0");
        assert_eq!(ray.contact.position, Coord::new(3, 1, 0));
        assert_eq!(ray.network, RayNetworkKind::Adversarial);
        assert_eq!(ray.signed_potential_y, -1.0);
        assert_eq!(ray.potential_family, "hazard.env_failure");
    }

    #[test]
    fn ray_reports_entity_object_identifier() {
        let state = SimState::from_ascii_layer(&["#####", "#AO.#", "#####"]).unwrap();
        let kernel = DreamKernel::new(state);

        let ray = kernel
            .cast_ray(Coord::new(1, 1, 0), Coord::new(1, 0, 0), 16, Some("agent"))
            .unwrap();

        assert_eq!(ray.contact.kind, ContactKind::Entity);
        assert_eq!(ray.contact.object_id, "object_2_1_0");
        assert_eq!(ray.contact.label, "object");
        assert_eq!(ray.contact.position, Coord::new(2, 1, 0));
        assert_eq!(ray.network, RayNetworkKind::Neutral);
    }

    #[test]
    fn rollout_produces_internal_sequence_with_terminal_goal() {
        let state = SimState::from_ascii_layer(&["#####", "#A.G#", "#...#", "#####"]).unwrap();
        let mut kernel = DreamKernel::new(state);
        let sequence = kernel
            .rollout(
                &[
                    Action::move_agent(Coord::new(1, 0, 0)),
                    Action::move_agent(Coord::new(1, 0, 0)),
                ],
                &cardinal_directions(),
                8,
                "agent",
            )
            .unwrap();

        assert_eq!(sequence.frames.len(), 3);
        let final_frame = sequence.frames.last().unwrap();
        assert_eq!(final_frame.render_top_down[1], "#..A#");
        assert_eq!(final_frame.outcome.as_ref().unwrap().reward, 1.0);
        assert!(final_frame.outcome.as_ref().unwrap().terminal);
        assert_eq!(final_frame.chronometric.signed_outcome_y, 1.0);
        assert!(
            final_frame
                .chronometric
                .potential_datapoints
                .iter()
                .any(|datum| datum.object_id == "goal:3:1:0"
                    && datum.family == "goal_progress.level_delta"
                    && datum.network == RayNetworkKind::Beneficial)
        );
    }

    #[test]
    fn positive_terminal_branch_ranks_above_saturated_nonterminal_progress() {
        let state = SimState::from_ascii_layer(&["######", "#A#.G#", "#....#", "######"]).unwrap();
        let mut kernel = DreamKernel::new(state);
        let sequence = kernel
            .rollout(
                &[
                    Action::move_agent(Coord::new(0, 1, 0)),
                    Action::move_agent(Coord::new(1, 0, 0)),
                    Action::move_agent(Coord::new(1, 0, 0)),
                    Action::move_agent(Coord::new(1, 0, 0)),
                    Action::move_agent(Coord::new(0, -1, 0)),
                ],
                &cardinal_directions(),
                8,
                "agent",
            )
            .unwrap();
        let terminal_outcome = sequence
            .frames
            .iter()
            .filter_map(|frame| frame.outcome.as_ref())
            .find(|outcome| outcome.reward > 0.0)
            .unwrap();
        let best_branch = sequence
            .branch_matrix
            .iter()
            .max_by(|left, right| {
                left.chrono_y_net
                    .partial_cmp(&right.chrono_y_net)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .unwrap();

        assert_eq!(terminal_outcome.branch_id, best_branch.branch_id);
        assert_eq!(best_branch.chrono_y_net, 1.0);
        assert!(
            sequence
                .branch_matrix
                .iter()
                .filter(|branch| branch.branch_id != terminal_outcome.branch_id)
                .all(|branch| branch.chrono_y_net < best_branch.chrono_y_net)
        );
    }

    #[test]
    fn chronometric_frame_exposes_ray_networks_and_potentials() {
        let sequence = demo_sequence().unwrap();
        let first_frame = sequence.frames.first().unwrap();

        assert!(
            first_frame
                .rays
                .iter()
                .any(|ray| ray.network == RayNetworkKind::Adversarial
                    && ray.contact.object_id == "hazard:3:1:0")
        );
        assert!(
            first_frame
                .chronometric
                .potential_family_names
                .contains(&"goal_progress.level_delta".to_string())
        );
        assert!(
            first_frame
                .chronometric
                .potential_datapoints
                .iter()
                .any(|datum| datum.network == RayNetworkKind::Beneficial
                    && datum.object_id == "goal:4:1:0")
        );
        assert!(
            first_frame
                .chronometric
                .potential_datapoints
                .iter()
                .any(|datum| datum.network == RayNetworkKind::Adversarial
                    && datum.object_id == "hazard:3:1:0")
        );
        let hazard = first_frame
            .chronometric
            .potential_datapoints
            .iter()
            .find(|datum| {
                datum.object_id == "hazard:3:1:0"
                    && datum.source == "known_map.static_terminal_cell"
            })
            .unwrap();
        assert_eq!(hazard.position, Coord::new(3, 1, 0));
        assert_eq!(hazard.chrono_y, -1.0);
        assert_eq!(hazard.category_id, "map.terminal.negative");
        assert_eq!(hazard.event_coord.t, first_frame.tick);
        assert_eq!(hazard.event_coord.x, 3.0);
        assert_eq!(hazard.event_coord.y_chrono, -1.0);
        assert_eq!(hazard.event_coord.z, 1.0);
    }

    #[test]
    fn demo_sequence_serializes_as_json() {
        let sequence = demo_sequence().unwrap();
        let json = sequence_to_json(&sequence);

        assert!(json.contains("\"schema\":\"dream_kernel.sequence.v003\""));
        assert!(json.contains("\"object_registry\""));
        assert!(json.contains("\"branch_matrix\""));
        assert!(json.contains("\"branch_potentials\""));
        assert!(json.contains("\"object_link_hypotheses\""));
        assert!(json.contains("\"nemo_relay\""));
        assert!(json.contains("\"sequence_hash\""));
        assert!(json.contains("\"frame_hash\""));
        assert!(json.contains("\"invariant_passed\":true"));
        assert!(sequence.integrity.invariant_passed);
        assert_eq!(sequence.branch_matrix.len(), sequence.frames.len() - 1);
        assert!(!sequence.branch_potentials.is_empty());
        assert!(!sequence.object_link_hypotheses.is_empty());
        assert_eq!(
            sequence.nemo_relay.relay_status,
            "packet_ready_model_not_called"
        );
        assert!(
            sequence
                .object_registry
                .iter()
                .any(|entry| entry.object_id == "goal:4:1:0"
                    && entry.category_id == "map.terminal.positive"
                    && !entry.hypothesis_refs.is_empty())
        );
        assert!(json.contains("\"render_top_down\""));
        assert!(json.contains("\"kind\":\"hazard\""));
        assert!(json.contains("\"object_id\":\"hazard:3:1:0\""));
        assert!(json.contains("\"category_id\":\"map.terminal.negative\""));
        assert!(json.contains("\"category_confidence\":1.000000"));
        assert!(json.contains("\"network\":\"adversarial\""));
        assert!(json.contains("\"chronometric\""));
        assert!(json.contains("\"potential_family_vector\""));
        assert!(json.contains("\"family\":\"hazard.env_failure\""));
        assert!(json.contains("\"family\":\"goal_progress.level_delta\""));
        assert!(json.contains("\"map_coord\""));
        assert!(json.contains("\"event_coord\""));
        assert!(json.contains("\"chrono_y\""));
        assert!(json.contains("\"provenance\""));
        assert!(json.contains("\"outcome_calibration\""));
        assert!(json.contains("\"outcome_probability\""));
        assert!(json.contains("\"chrono_y_correlation\""));
        assert!(json.contains("\"relation_kind\":\"branch.coactivation.open_relation\""));
        assert!(json.contains("\"required_model\":\"nemotron_3_nano_omni\""));
        assert!(json.contains("\"y_chrono\":-1.000000"));
    }

    #[test]
    fn sequence_integrity_rejects_unknown_ids_and_bad_probabilities() {
        let sequence = demo_sequence().unwrap();
        let mut branch_potentials = sequence.branch_potentials.clone();
        branch_potentials[0].branch_id = "missing.branch".to_string();
        branch_potentials[0].outcome_probability = 1.25;
        let integrity = sequence_integrity(
            &sequence.object_registry,
            &sequence.branch_matrix,
            &branch_potentials,
            &sequence.object_link_hypotheses,
            &sequence.nemo_relay,
            &sequence.frames,
        );

        assert!(!integrity.invariant_passed);
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("references unknown branch missing.branch"))
        );
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("outcome_probability out of range"))
        );

        let mut links = sequence.object_link_hypotheses.clone();
        links[0].source_object_id = "missing_object".to_string();
        links[0].probability = -0.1;
        let integrity = sequence_integrity(
            &sequence.object_registry,
            &sequence.branch_matrix,
            &sequence.branch_potentials,
            &links,
            &sequence.nemo_relay,
            &sequence.frames,
        );

        assert!(!integrity.invariant_passed);
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("references unknown object missing_object"))
        );
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("probability out of range"))
        );

        let mut nemo = sequence.nemo_relay.clone();
        nemo.open_questions[0].branch_id = Some("missing.branch".to_string());
        nemo.open_questions[0].object_id = Some("missing_object".to_string());
        nemo.open_questions[0].link_id = Some("missing_link".to_string());
        let integrity = sequence_integrity(
            &sequence.object_registry,
            &sequence.branch_matrix,
            &sequence.branch_potentials,
            &sequence.object_link_hypotheses,
            &nemo,
            &sequence.frames,
        );

        assert!(!integrity.invariant_passed);
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("references unknown branch missing.branch"))
        );
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("references unknown object missing_object"))
        );
        assert!(
            integrity
                .invariant_errors
                .iter()
                .any(|error| error.contains("references unknown link missing_link"))
        );
    }

    #[test]
    fn sequence_hash_changes_when_material_rollout_content_changes() {
        let state = SimState::from_ascii_layer(&["#####", "#A.G#", "#...#", "#####"]).unwrap();
        let directions = cardinal_directions();
        let mut direct_kernel = DreamKernel::new(state.clone());
        let direct = direct_kernel
            .rollout(
                &[
                    Action::move_agent(Coord::new(1, 0, 0)),
                    Action::move_agent(Coord::new(1, 0, 0)),
                ],
                &directions,
                8,
                "agent",
            )
            .unwrap();
        let mut delayed_kernel = DreamKernel::new(state);
        let delayed = delayed_kernel
            .rollout(
                &[
                    Action::move_agent(Coord::new(1, 0, 0)),
                    Action::Wait,
                    Action::move_agent(Coord::new(1, 0, 0)),
                ],
                &directions,
                8,
                "agent",
            )
            .unwrap();

        assert_ne!(
            direct.integrity.sequence_hash,
            delayed.integrity.sequence_hash
        );
    }

    #[test]
    fn object_registry_requires_provenance_and_keeps_unknown_objects_open() {
        let state = SimState::from_ascii_layer(&["#####", "#AO.#", "#####"]).unwrap();
        let kernel = DreamKernel::new(state);
        let registry = kernel.object_registry();

        for entry in &registry {
            assert!(!entry.object_id.is_empty());
            assert!(!entry.kind.is_empty());
            assert!(!entry.category_id.is_empty());
            assert!(!entry.open_tags.is_empty());
            assert!(!entry.source.is_empty());
            assert!((0.0..=1.0).contains(&entry.confidence));
            assert!((0.0..=1.0).contains(&entry.category_confidence));
        }

        let object = registry
            .iter()
            .find(|entry| entry.object_id == "object_2_1_0")
            .unwrap();
        assert_eq!(object.category_id, "object.unknown.open");
        assert!(object.open_tags.contains(&"open_world".to_string()));
        assert_eq!(object.source, "sim_state.entity");
    }
}
