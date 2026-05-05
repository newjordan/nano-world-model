import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from chronometric_bridge import (  # noqa: E402
    synthetic_bridge_records,
    validate_bridge_manifest,
    validate_bridge_record,
    write_jsonl,
)


def test_synthetic_bridge_records_validate():
    records = synthetic_bridge_records()

    for record in records:
        assert validate_bridge_record(record) == []


def test_bridge_record_rejects_missing_required_field():
    record = synthetic_bridge_records()[0]
    del record["branch_direction_n"]

    errors = validate_bridge_record(record)

    assert any("branch_direction_n" in error for error in errors)


def test_bridge_manifest_validation_roundtrip(tmp_path):
    path = tmp_path / "manifest.jsonl"
    write_jsonl(path, synthetic_bridge_records())

    result = validate_bridge_manifest(path)

    assert result["valid"] is True
    assert result["records"] == 2
    assert result["errors"] == []
