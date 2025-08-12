#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
**UNDER DEVELOPMENT**

`ml_EPJ` provides Machine Learning capabilties to train surrogate models in `genEPJ`.
A variety of training functions are provided by the excellent pytorch library.

`ml_EPJ` offers the ability to wrap code in a function mockup unit (FMU) so it can be used directly in the Modelica/Julia ecosystems.
"""


# Steps:
# 1. Need a fully functioning *_genEPJ.py with opti_inputs.json file (run_eplus=False(?)). Specify multiple EPW files.
# 2. Training data: sample the space N times, simulate, and copy over to training directory
# 3. Testing set: Split training data into testing/training set
# 4. Train model
# 5. Wrap in FMU (optional)

# Training data: Hourly profiles of heating, cooling, waste heat (if any), DHW

# SB- how can you reuse this for opti?
# + Training data is redirected into data.db3 (set flag to override sampling approach)
#   - WANT a SQL statement
# + Training data folder created and the same process
# OR
# + Start the entire process from the training data folder (created in makefile)
