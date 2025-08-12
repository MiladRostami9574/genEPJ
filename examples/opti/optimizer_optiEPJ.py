#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from genEPJ import opti_EPJ as opti

from platypus import Problem, Solution, NSGAII, NSGAIII, Real, ProcessPoolEvaluator, experiment, SBX, HUX, PM, BitFlip, CompoundOperator, nondominated, unique

num_cpus=2

algorithms = [( NSGAII, {"variator": CompoundOperator(SBX(), HUX(), PM(), BitFlip())} )]

sql_objfits=['eui']
def myobjfn(x):
    return opti.objective_function(x, sql_objfits)

json_inputs='opti_inputs.json'
json_params=opti.get_input_file(json_inputs)
nvars= len( json_params.keys() )
print(nvars)
problem = Problem(nvars, len(sql_objfits), 0) # No constraints
problem.types[:] = opti.build_parameters(json_params)
problem.function = myobjfn

myindiv=opti.rand_indiv(problem)
myindiv=opti.fit_eval(myindiv, delete=False)

#with ProcessPoolEvaluator(num_cpus) as evaluator:
#    algorithm = NSGAII(problem, variator=CompoundOperator(SBX(), HUX(), PM(), BitFlip()), evaluator=evaluator)
#    algorithm.run(100)
#
#print("Non-Dominated Pareto Front")
#for solution in unique(nondominated(algorithm.result)):
#    print( opti.solution2dict(solution), solution.objectives)

## Pathway analysis
#ref_bldg= opti.get_ref_bldg(problem, json_params)
#prop_bldg=opti.get_prop_bldg(problem,json_params)
#output=opti.search_pathway_OAT(ref_bldg, prop_bldg)
#print(output)
