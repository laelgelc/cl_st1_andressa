import json

from cl_st1.common.storage import Ph1Paths, append_ndjson


def test_ph1paths_create_makes_expected_dirs(tmp_path):
    paths = Ph1Paths.create(tmp_path / "run1")
    assert paths.raw_dir.is_dir()
    assert paths.logs_dir.is_dir()


def test_append_ndjson_writes_valid_json_lines(tmp_path):
    out = tmp_path / "x.ndjson"
    rows = [{"a": 1}, {"b": "two"}]

    n = append_ndjson(out, rows)
    assert n == 2

    lines = out.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == rows