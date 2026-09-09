"""Setup must preserve existing directories and keep check-only free of installs."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location(
    "setup_tool", Path(__file__).parents[1] / "scripts/setup.py"
)
setup_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_tool)


def test_existing_non_environment_is_preserved(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("existing work")
    with pytest.raises(ValueError, match="Refusing"):
        setup_tool.install_environment(tmp_path)
    assert marker.read_text() == "existing work"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["keep.txt"]


def test_check_only_never_installs_or_creates_demo(tmp_path, monkeypatch, capsys):
    target = tmp_path / "absent-env"
    demo = tmp_path / "absent-demo"
    monkeypatch.setattr(
        "sys.argv", ["setup", "--check-only", "--venv", str(target), "--demo-dir", str(demo)]
    )
    with (
        patch.object(setup_tool, "install_environment") as install,
        patch.object(setup_tool, "readiness", return_value={"gflo_installed": False}),
    ):
        assert setup_tool.main() == 1
        install.assert_not_called()
    assert not target.exists() and not demo.exists()
    assert '"demo_prepared": false' in capsys.readouterr().out
