#!/usr/bin/env python3
"""Windows-safe command-line checks for genEPJ model files.

The default command is an installation smoke check. It verifies that the
package imports, the packaged epJSON template resource is available, and
an IDF file can be parsed. Use ``--full`` to run the legacy detailed
``check_model`` validation, which requires a configured EnergyPlus
installation and project output files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from genEPJ.generate_EPJ import check_model, get_IDF_objs_raw
from genEPJ.pylib.genEPJ_lib import get_obj_type
from genEPJ.resources import epjson_template_path


DEFAULT_DEMO_IDF = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "sim-tinyhome"
    / "nomad_3RV96.idf"
)


def _require_objects(objects: Iterable[str], required_types: Iterable[str]) -> list[str]:
    """Return required EnergyPlus object types that are absent."""
    found = {get_obj_type(obj).lower() for obj in objects}
    return [item for item in required_types if item.lower() not in found]


def run_smoke_check(idf_path: Path) -> int:
    """Run a lightweight installation and IDF parsing check."""
    if not idf_path.is_file():
        raise FileNotFoundError(f"IDF file not found: {idf_path}")

    template = epjson_template_path()
    objects = get_IDF_objs_raw(str(idf_path))
    missing = _require_objects(
        objects,
        ["Version", "Building", "Timestep", "BuildingSurface:Detailed"],
    )

    print("genEPJ installation smoke check")
    print(f"Package epJSON template: {template}")
    print(f"IDF file: {idf_path}")
    print(f"Parsed EnergyPlus objects: {len(objects)}")

    if missing:
        raise ValueError(
            "The IDF file was parsed, but these expected object types "
            f"were not found: {', '.join(missing)}"
        )

    print("Smoke check completed successfully.")
    return 0


def run_full_check(idf_path: Path, epw: str | None, interactive: bool) -> int:
    """Run the legacy detailed genEPJ model-compatibility check."""
    if not idf_path.is_file():
        raise FileNotFoundError(f"IDF file not found: {idf_path}")

    objects = get_IDF_objs_raw(str(idf_path))
    check_model(
        objects,
        args={
            "interactive": interactive,
            "epw": epw or "CAN_ON_Ottawa.716280_CWEC.epw",
            "idf": str(idf_path),
        },
    )
    print("Detailed check_model run completed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Validate a genEPJ installation and optionally run the full model check.",
    )
    parser.add_argument(
        "idf",
        nargs="?",
        type=Path,
        default=DEFAULT_DEMO_IDF,
        help=(
            "Path to the IDF file to check. Defaults to the packaged "
            "tiny-home demonstration model."
        ),
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help=(
            "Run the legacy detailed check_model validation. This requires "
            "EnergyPlus, ENERGYPLUS_DIR, ENERGYPLUS_WEATHER, and relevant "
            "weather/output files."
        ),
    )
    parser.add_argument(
        "--epw",
        default=None,
        help="Optional EPW filename for the full check_model validation.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Allow interactive prompts during the full check.",
    )
    return parser


def main() -> int:
    """Entry point used by ``python -m genEPJ.standalone.check_model``."""
    args = build_parser().parse_args()
    idf_path = args.idf.resolve()

    if args.full:
        return run_full_check(idf_path, args.epw, args.interactive)
    return run_smoke_check(idf_path)


if __name__ == "__main__":
    raise SystemExit(main())
