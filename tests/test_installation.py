from pathlib import Path
import subprocess
import sys


def test_genepj_package_imports():
    import genEPJ  # noqa: F401


def test_template_file_is_packaged():
    from genEPJ.resources import epjson_template_path

    template = epjson_template_path()
    assert template.is_file()
    assert template.name == "templates_9.0.1.json"


def test_generate_epj_imports_without_template_path_error():
    import genEPJ.generate_EPJ as generate_epj

    assert generate_epj.epJSON_template.endswith("templates_9.0.1.json")


def test_tinyhome_demo_files_exist():
    root = Path(__file__).resolve().parents[1]
    demo = root / "examples" / "sim-tinyhome"

    assert (demo / "nomad_3RV96.idf").is_file()
    assert (demo / "Nomad_genEPJ.py").is_file()
    assert (demo / "opti_inputs.json").is_file()


def test_check_model_smoke_command_runs_on_tinyhome():
    root = Path(__file__).resolve().parents[1]
    demo_idf = root / "examples" / "sim-tinyhome" / "nomad_3RV96.idf"

    result = subprocess.run(
        [sys.executable, "-m", "genEPJ.standalone.check_model", str(demo_idf)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Smoke check completed successfully" in result.stdout
