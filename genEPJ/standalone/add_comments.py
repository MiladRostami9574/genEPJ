#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line helper to restore IDF-style comments to a translated file."""

from sys import argv, path

path.append("genEPJ")
path.append("../genEPJ")

from generate_EPJ import add_comments


USAGE = "Usage: add_comments.py FILENAME.idf"


def main() -> None:
    """Run the add-comments helper from the command line."""
    if len(argv) == 1:
        print(USAGE)
        return

    add_comments(argv[1])


if __name__ == "__main__":
    main()
