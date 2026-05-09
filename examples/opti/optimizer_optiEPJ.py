#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal example configuration for running genEPJ optimization."""

from genEPJ import opti_EPJ as opti

from platypus import (
    BitFlip,
    CompoundOperator,
    HUX,
    NSGAII,
    PM,
    Problem,
    SBX,
)

NUM_CPUS = 2

ALGORITHMS = [
    (NSGAII, {"variator": CompoundOperator(SBX(), HUX(), PM(), BitFlip())})
]

SQL_OBJECTIVES = ["eui"]


def myobjfn(x):
    """Evaluate the configured objective function for an individual."""
    return opti.objective_function(x, SQL_OBJECTIVES)


json_inputs = "opti_inputs.json"
json_params = opti.get_input_file(json_inputs)
nvars = len(json_params.keys())
print(nvars)

problem = Problem(nvars, len(SQL_OBJECTIVES), 0)
problem.types[:] = opti.build_parameters(json_params)
problem.function = myobjfn

myindiv = opti.rand_indiv(problem)
myindiv = opti.fit_eval(myindiv, delete=False)
