#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add standalone script to add IDF style comments back to a previously translated JSON file (which would have removed them)

`ml_EPJ` provides Machine Learning capabilties to train surrogate models in `genEPJ`.
A variety of training functions are provided by the excellent pytorch library.

`ml_EPJ` offers the ability to wrap code in a function mockup unit (FMU) so it can be used directly in the Modelica/Julia ecosystems.
"""

from sys import argv, path

path.append('genEPJ')
path.append('../genEPJ')
# add_comments: overwrites provided file (saves previous to _bkup.idf)
# add_comments_file: creates a new file
from generate_EPJ import add_comments

# Allow for commandline use
if __name__ == '__main__':

    if len(argv)==1 :
        print("add_comment requires a file: 'add_comments.py FILENAME.idf'")
    else:
        add_comments(argv[1])
