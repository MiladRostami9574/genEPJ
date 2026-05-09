#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch an interactive IPython session for a genEPJ directives file."""

from optparse import OptionParser
from os.path import join
import sys

from traitlets.config import get_config

parser = OptionParser()
parser.add_option(
    "-d",
    "--directives",
    dest="directives",
    action="store",
    type="string",
    help=(
        "Run an interactive session using directives for prep/ref/prop "
        "IDF or epJSON manipulations."
    ),
)
(options, args) = parser.parse_args()
mydirect = options.directives

cfg = get_config()
cfg.InteractiveShellEmbed.colors = "Linux"
cfg.TerminalIPythonApp.display_banner = True
cfg.InteractiveShell.confirm_exit = False

cfg.InteractiveShellApp.hide_initial_ns = False
cfg.InteractiveShellApp.exec_lines = [
    'print("\\nimporting some things\\n")',
    "import numpy as np",
    "import scipy as sp",
    "import pandas as pd",
]
cfg.InteractiveShellApp.exec_files = [f"{mydirect}"]

cfg.TerminalIPythonApp.hide_initial_ns = False
cfg.TerminalIPythonApp.exec_lines = cfg.InteractiveShellApp.exec_lines
cfg.TerminalIPythonApp.exec_files = cfg.InteractiveShellApp.exec_files

print(mydirect)

sys.path.append(".")
from genEPJ import *  # noqa: F401,F403


def demo():
    """Run the bundled interactive genEPJ demo."""
    from IPython.lib.demo import Demo

    demo_fname = join("genEPJ_pkg", "interactive_demo.py")
    mydemo = Demo(demo_fname)
    mydemo()


if __name__ == "__main__" and not callable(globals().get("get_ipython", None)):
    from IPython import start_ipython
    from IPython.terminal.embed import InteractiveShellEmbed

    show_welcome(config.version)
    start_ipython(config=cfg, argv=[])

    ipshell = InteractiveShellEmbed(
        config=cfg,
        banner1="Welcome to genEPJ!",
        exit_msg=(
            "Thanks for using genEPJ. If you found this useful, "
            "consider contributing to the project at PATERON"
        ),
    )
    ipshell(
        "***My Customize genEPJ messaging... "
        "Hit Ctrl-D to exit interpreter and continue program.\n"
        'All variables/functions described via "%whos" magic command\n'
        'Type "demo()" to see a possible workflow'
    )
else:
    print("Inside IPython already")
