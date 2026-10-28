from adb_visual_mcp.actions import normalize_key
from adb_visual_mcp.adb import parse_density, parse_size


def test_parse_size_prefers_override():
    dump = "Physical size: 1080x2340\nOverride size: 720x1560\n"
    assert parse_size(dump) == (720, 1560)


def test_parse_density():
    assert parse_density("Physical density: 420\nOverride density: 320\n") == 320


def test_normalize_keys():
    assert normalize_key("enter") == "KEYCODE_ENTER"
    assert normalize_key("a") == "KEYCODE_A"
    assert normalize_key("KEYCODE_HOME") == "KEYCODE_HOME"
