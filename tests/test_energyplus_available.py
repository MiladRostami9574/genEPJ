import shutil
import subprocess

import pytest


@pytest.mark.energyplus
def test_energyplus_command_is_available():
    if shutil.which("energyplus") is None:
        pytest.skip("EnergyPlus executable is not available on PATH.")

    result = subprocess.run(
        ["energyplus", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
