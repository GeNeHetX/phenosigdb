from pathlib import Path

from phenosigdb.release import bump_versions


def test_bump_versions_updates_root_python_and_r(tmp_path: Path):
    (tmp_path / "phenosigdb").mkdir()
    (tmp_path / "python" / "phenosigdb").mkdir(parents=True)
    (tmp_path / "rpkg" / "R").mkdir(parents=True)

    (tmp_path / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "phenosigdb" / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "python" / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "python" / "phenosigdb" / "_version.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "rpkg" / "DESCRIPTION").write_text("Version: 0.1.0\n", encoding="utf-8")
    (tmp_path / "rpkg" / "R" / "phenosigdb.R").write_text('.phenosigdb_package_version <- "0.1.0"\n', encoding="utf-8")

    bump_versions("0.2.0", root=tmp_path)

    assert 'version = "0.2.0"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert '__version__ = "0.2.0"' in (tmp_path / "phenosigdb" / "__init__.py").read_text(encoding="utf-8")
    assert 'version = "0.2.0"' in (tmp_path / "python" / "pyproject.toml").read_text(encoding="utf-8")
    assert '__version__ = "0.2.0"' in (tmp_path / "python" / "phenosigdb" / "_version.py").read_text(encoding="utf-8")
    assert "Version: 0.2.0" in (tmp_path / "rpkg" / "DESCRIPTION").read_text(encoding="utf-8")
    assert '.phenosigdb_package_version <- "0.2.0"' in (tmp_path / "rpkg" / "R" / "phenosigdb.R").read_text(encoding="utf-8")
