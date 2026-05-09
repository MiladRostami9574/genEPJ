#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example genEPJ workflow for a NOMAD multi-residential model."""

from genEPJ import *

mybldg = Building()
mybldg.type_set("multi-residential")
mybldg.location_set("Ontario")
mybldg.weather = "CAN_ON_Ottawa.716280_CWEC.epw"
mybldg.basename = "nomad_3RV96.idf"

# EnergyPlus version
mybldg.config.eplus_version_set("9.6.0")

# Task names must match the JSON task keys.
mybldg.task_suffix = ["prep", "ref", "prop", "opti"]
mybldg.set_filenames()
prep_file = mybldg.task_filenames["prep"]

HVAC_LOOKUP = {
    1: add_HVAC_Baseboard,
    2: add_HVAC_VRF,
}

# Default hourly outputs.
OUTPUT_VARS_METER = [
    "Photovoltaic:ElectricityProduced",
    "Cooling:EnergyTransfer",
    "Heating:EnergyTransfer",
    "Gas:Building",
    "Electricity:Building",
    "Water:Building",
]

# Additional hourly outputs used for debugging.
OUTPUT_VARS_METER_DEBUG = [
    "Electricity:HVAC",
    "Gas:HVAC",
    "InteriorLights:Electricity",
    "InteriorEquipment:Electricity",
]

prep_fnlist = []

# Common tasks for reference, proposed, and optimized cases.
fn_common_tasks = [
    [rm_all_HVAC_simple, True, {}],
    [mod_OutputTables, True, {}],
    [
        add_enduse_outputs,
        True,
        {"timestep": "hourly", "output_vars": OUTPUT_VARS_METER},
    ],
    [
        add_enduse_outputs,
        True,
        {"timestep": "hourly", "output_vars": OUTPUT_VARS_METER_DEBUG},
    ],
]

# Open JSON inputs. Defaults to ``opti_inputs.json``.
inputs = find_JSON()


def build_fnlist(json_value_key="value"):
    """Build a function list from the selected JSON value key."""
    li_frac = inputs["li_frac"][json_value_key]
    app_frac = inputs["app_frac"][json_value_key]
    hvacsys_type = inputs["hvac_sys"][json_value_key]
    azi = inputs["azi"][json_value_key]
    infil_frac = inputs["infil_frac"][json_value_key]

    return [
        [mod_pd, True, {"name": "Lights", "frac": li_frac / 100.0}],
        [
            mod_pd,
            True,
            {"name": "ElectricEquipment", "frac": app_frac / 100.0},
        ],
        [
            dispatch_HVAC,
            True,
            {
                "add_HVAC_fn": HVAC_LOOKUP[hvacsys_type],
                "use_DOAS": True,
                "use_district": False,
                "to_file": prep_file,
            },
        ],
        [mod_infil, True, {"frac": infil_frac}],
    ]


# Build task lists.
ref_fnlist = build_fnlist(json_value_key="ref-value")
prop_fnlist = build_fnlist(json_value_key="prop-value")
opti_fnlist = build_fnlist(json_value_key="value")

mybldg.tasks = {
    "prep": prep_fnlist,
    "opti": join_lists(fn_common_tasks, opti_fnlist),
}

mybldg.generate(force_recreate=True, run_eplus=True)
