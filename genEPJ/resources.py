"""Resource helpers for genEPJ package data.

The helpers in this module locate files that are distributed with the
installed package. They avoid relying on the user's current working
directory, which is important for Windows installations and editable
installs from a fresh clone.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Iterable


_TEMPLATE_RELATIVE = Path("templateGenerator_epJSON") / "templates_9.0.1.json"


def package_root() -> Path:
    """Return the installed genEPJ package directory."""
    return Path(__file__).resolve().parent


def resource_path(*parts: str) -> Path:
    """Return a filesystem path to a genEPJ package resource.

    Parameters
    ----------
    *parts:
        Relative path components inside the ``genEPJ`` package.

    Returns
    -------
    pathlib.Path
        Path to the requested packaged resource.
    """
    return package_root().joinpath(*parts)


def find_resource(candidates: Iterable[Path | str]) -> Path:
    """Return the first existing file from candidate paths.

    Relative paths are interpreted relative to the current working
    directory. Absolute paths are used as provided.
    """
    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            return candidate_path.resolve()
    raise FileNotFoundError(
        "Could not locate required genEPJ resource. Checked: "
        + ", ".join(str(Path(c)) for c in candidates)
    )


def epjson_template_path() -> Path:
    """Return the packaged epJSON template-file path.

    The preferred location is inside the installed package. A small set
    of legacy locations is also checked to support older scripts that run
    from the repository root or from example folders.
    """
    packaged = resource_path(*_TEMPLATE_RELATIVE.parts)
    candidates = [
        packaged,
        Path("genEPJ") / _TEMPLATE_RELATIVE,
        _TEMPLATE_RELATIVE,
        Path("templates_9.0.1.json"),
    ]
    return find_resource(candidates)


def read_text_resource(*parts: str, encoding: str = "utf-8") -> str:
    """Read a text resource from the installed package."""
    resource = resources.files("genEPJ").joinpath(*parts)
    return resource.read_text(encoding=encoding)
