#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from genEPJ import *

# Building Config {{{
#*****************
mybldg = Building()
mybldg.type_set( 'multi-residential' )
#mybldg.verbose_substitute = True
mybldg.location_set("Ontario")

mybldg.weather="CAN_ON_Ottawa.716280_CWEC.epw"

mybldg.basename="nomad_3RV96.idf"

# EnergyPlus version
mybldg.config.eplus_version_set("9.6.0")

## Names need to match task JSON keys
mybldg.task_suffix= [ "prep", "ref", "prop", "opti" ]
mybldg.set_filenames()
prep_file=mybldg.task_filenames['prep'] # prep filenames used by dispatch_HVAC

HVAC_lkup={
          1 : add_HVAC_Baseboard,
          2 : add_HVAC_VRF,
}

# Used in hourly debugs (default)
output_vars_meter=[
 'Photovoltaic:ElectricityProduced',
 'Cooling:EnergyTransfer',
 'Heating:EnergyTransfer',
 'Gas:Building',
 'Electricity:Building',
 'Water:Building',
]

# Used in hourly debugs (only if flag is set)
output_vars_meter_debug=[
    'Electricity:HVAC',
    'Gas:HVAC',
    'InteriorLights:Electricity',
    'InteriorEquipment:Electricity',
]


prep_fnlist=[
  #[ check_model, True, {'interactive': False, "epw": mybldg.weather, "idf": mybldg.basename} ],
]

# Common tasks for make_ref_90.1, make_ref, make_prop
fn_common_tasks=[
  [ rm_all_HVAC_simple, True, {} ], # Remove existing mech. We'll add a new one
  [ mod_OutputTables, True, {} ], # HTML tables using kWh/m2
  [ add_enduse_outputs, True, { 'timestep': "hourly", 'output_vars': output_vars_meter} ],
  [ add_enduse_outputs, True, { 'timestep': "hourly", 'output_vars': output_vars_meter_debug} ],
       ]

inputs=find_JSON() # Open JSON file of inputs, default to 'opti_inputs.json'
def build_fnlist(json_value_key='value'):

    li_frac             = inputs['li_frac'][json_value_key]
    app_frac            = inputs['app_frac'][json_value_key]
    hvacsys_type        = inputs['hvac_sys'][json_value_key]
    azi                 = inputs['azi'][json_value_key]
    infil_frac          = inputs['infil_frac'][json_value_key]

    # Build fnlist
    _fnlist=[

          [ mod_pd, True, { 'name': 'Lights', 'frac': li_frac/100.} ],
          [ mod_pd, True, { 'name': 'ElectricEquipment', 'frac': app_frac/100.} ],
          [ dispatch_HVAC, True, { 'add_HVAC_fn': HVAC_lkup[ hvacsys_type ],\
                                  'use_DOAS': True, 'use_district': False, 'to_file': prep_file} ],
          [ mod_infil, True, { 'frac': infil_frac, }],

    ]
    return _fnlist


# Simulation Coordination {{{
#*************************

# Reference/Code-compliant building
ref_fnlist=build_fnlist(json_value_key='ref-value')

# Proposed/As-built building
prop_fnlist=build_fnlist(json_value_key='prop-value')

# Optimized building
opti_fnlist=build_fnlist(json_value_key='value')

mybldg.tasks= {
  "prep": prep_fnlist,
  #"ref":  join_lists(fn_common_tasks, ref_fnlist),
  #"prop": join_lists(fn_common_tasks, prop_fnlist),
  "opti": join_lists(fn_common_tasks, opti_fnlist),
}

mybldg.generate(force_recreate=True, run_eplus=True)


#************************* }}}

