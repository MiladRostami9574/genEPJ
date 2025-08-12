#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Two ways to run this script:
# 1. If calling from python/script: python genEPJ_pkg/interactive_genEPJ.py -d NAME_genEPJ.py
# 4. Call from ipython
#    ipython
#      --profile-dir=genEPJ_pkg/ipython/profile_genEPJ
#      -i NAME_genEPJ.py

# Goals of the script:
# * Load a provided *_genEPJ.py file and launch an interactive session
# * Load results (csv, sql, ...) and predefined diagnostics
# * Load new results (csv, sql, ...) and predefined diagnostics when prep/ref/prop simulation are run

# Unsolved Issues as of Wed Feb 20 10:46:42 EST 2019
# * Loading script via command SOLVED if you use start_ipython. However, doesn't work for ipshell()
# * Custom messages and demos works for ipshell(). However, doesn't work for start_ipython()

from os.path import basename, join

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-d", "--directives", dest="directives",
    action="store", type="string",
    help="Runs interactive session using directives on IDF/epJSON manipulations for prep/ref/prop buildings.")
(options, args) = parser.parse_args()
mydirect=options.directives


from traitlets.config import get_config
cfg = get_config()
cfg.InteractiveShellEmbed.colors = "Linux"
cfg.TerminalIPythonApp.display_banner = True
#cfg.TerminalInteractiveShell.banner2 = '*** Welcome! ***'
cfg.InteractiveShell.confirm_exit = False

# ipshell config (?)
cfg.InteractiveShellApp.hide_initial_ns=False # Load exec_files and exec_lines
cfg.InteractiveShellApp.exec_lines = [
    'print("\\nimporting some things\\n")',
    'import numpy as np',
    'import scipy as sp',
    'import pandas as pd',
]
cfg.InteractiveShellApp.exec_files = [
    '%s'%(mydirect),
]

# start_ipython config (?)
cfg.TerminalIPythonApp.hide_initial_ns=False # Load exec_files and exec_lines
cfg.TerminalIPythonApp.exec_lines=cfg.InteractiveShellApp.exec_lines
cfg.TerminalIPythonApp.exec_files=cfg.InteractiveShellApp.exec_files

print(mydirect)

import sys
sys.path.append('.')
from genEPJ import * # TODO- read from commandline options

def demo():
    from IPython.lib.demo import Demo
    demo_fname = join('genEPJ_pkg', 'interactive_demo.py')
    mydemo = Demo(demo_fname)
    mydemo()

if __name__ == '__main__' and not callable(globals().get("get_ipython", None)):
    from IPython import start_ipython, embed
    # import the embeddable shell class
    from IPython.terminal.embed import InteractiveShellEmbed
    show_welcome(config.version)
    start_ipython( config=cfg, argv=[] )

    ipshell = InteractiveShellEmbed(config=cfg,
          banner1 = 'Welcome to genEPJ!',
          exit_msg = 'Thanks for using genEPJ. If you found this useful, consider contributing to the project at PATERON')
    ipshell('***My Customize genEPJ messaging... '
        'Hit Ctrl-D to exit interpreter and continue program.\n'
        'All variables/functions described via "%whos" magic command\n'
        'Type "demo()" to see a possible workflow'
        )
else:
    # Imported from within IPython
    print("Inside IPython already")

