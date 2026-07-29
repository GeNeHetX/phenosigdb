from pathlib import Path

from phenosigdb_maintainer.release import bump_versions


def test_bump_versions_updates_packages(tmp_path: Path):
    (tmp_path / "packages" / "python" / "phenosigdb").mkdir(parents=True)
    (tmp_path / "packages" / "r" / "R").mkdir(parents=True)
    (tmp_path / "packages" / "python" / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "packages" / "python" / "phenosigdb" / "_version.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "packages" / "r" / "DESCRIPTION").write_text("Version: 0.1.0\n", encoding="utf-8")
    (tmp_path / "packages" / "r" / "R" / "phenosigdb.R").write_text('.phenosigdb_package_version <- "0.1.0"\n', encoding="utf-8")

    bump_versions("0.2.0", root=tmp_path)

    assert 'version = "0.2.0"' in (tmp_path / "packages" / "python" / "pyproject.toml").read_text(encoding="utf-8")
    assert '__version__ = "0.2.0"' in (tmp_path / "packages" / "python" / "phenosigdb" / "_version.py").read_text(encoding="utf-8")
    assert "Version: 0.2.0" in (tmp_path / "packages" / "r" / "DESCRIPTION").read_text(encoding="utf-8")
    assert '.phenosigdb_package_version <- "0.2.0"' in (tmp_path / "packages" / "r" / "R" / "phenosigdb.R").read_text(encoding="utf-8")


def test_bump_versions_updates_pinned_install_urls(tmp_path: Path):
    (tmp_path / "packages" / "python" / "phenosigdb").mkdir(parents=True)
    (tmp_path / "packages" / "r" / "R").mkdir(parents=True)
    (tmp_path / "packages" / "python" / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "packages" / "python" / "phenosigdb" / "_version.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "packages" / "r" / "DESCRIPTION").write_text("Version: 0.1.0\n", encoding="utf-8")
    (tmp_path / "packages" / "r" / "R" / "phenosigdb.R").write_text('.phenosigdb_package_version <- "0.1.0"\n', encoding="utf-8")
    (tmp_path / "packages" / "r" / "README.md").write_text(
        "https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.0/phenosigdb_0.1.0.tar.gz\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.0/phenosigdb_0.1.0.tar.gz\n",
        encoding="utf-8",
    )
    (tmp_path / "MAINTAINING.md").write_text(
        "https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.0/phenosigdb_0.1.0.tar.gz\n",
        encoding="utf-8",
    )
    bump_versions("0.2.0", root=tmp_path)
    for relative in ("README.md", "MAINTAINING.md", "packages/r/README.md"):
        text = (tmp_path / relative).read_text(encoding="utf-8")
        assert "releases/download/v0.2.0/phenosigdb_0.2.0.tar.gz" in text
