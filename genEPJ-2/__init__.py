"""Top-level package exports for genEPJ.

The package exposes the core model-generation modules, template helpers,
and general utilities used to automate EnergyPlus model generation,
modification, and analysis. Optional integrations are loaded only when
their external dependencies are available so that a fresh installation
can still be imported and tested on Windows.
"""

from .generate_EPJ import *
from .pylib.genEPJ_lib import *
from .pylib.templater import *
from .pylib import templates_v9_0 as templ
from .pylib.epJSON_templater import *

try:  # Optional optimization integration.
    from .opti_EPJ import *
except Exception as exc:  # pragma: no cover - depends on optional packages.
    OPTI_IMPORT_ERROR = exc
else:
    OPTI_IMPORT_ERROR = None

try:  # Optional external Modelkit/Ruby integration.
    from .Modelkit.modelkit_wrapper import *
except Exception as exc:  # pragma: no cover - depends on local Modelkit/Ruby.
    MODELKIT_IMPORT_ERROR = exc
else:
    MODELKIT_IMPORT_ERROR = None
