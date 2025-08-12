from flask import Flask
import ghhops_server as hs
import json
from genEPJ import *

# register hops app as middleware
app = Flask(__name__)
hops = hs.Hops(app)

# creates the Hops component inside grasshopper and establishes the local server
@hops.component(
    "/runSim",
    name="RunSim",
    description="runs genEpj simulation",
    icon="icon.png",
    inputs=[
      # creates an input node on the grasshopper component for an EPW file and passes the input to the function sim
      hs.HopsString("Weather","EPW","EPW Weather File"),
      # creates an input node on the grasshopper component for a Building Type and passes the input to the function sim
      hs.HopsString("BuildingType","BLDGType","ePlus building type"),
      # creates an input node on the grasshopper component for an Boolian Toggle to run node and passes the input to the function sim
      hs.HopsBoolean("_run","run",'set to "True" to run genEPJ'),
      # creates an input node on the grasshopper component for an IDF file and passes the input to the function sim
      hs.HopsString("idf","idf","idf input file"),
    ],
    outputs=[
      # creates an input node on the grasshopper component for the location of SQL prep file and passes the output from the function sim
      hs.HopsString("sql_prep","sql","location of sql prep prop file"),
      # creates an input node on the grasshopper component for the location of SQL prep_prop file and passes the output from the function sim
      hs.HopsString("sql_prep_prop","sql","location of sql prop file")
    ]
)

# wraps the genEPJ configuration File passing in the variables input from the Hops node
def sim(weather: str,buildingType: str, _run, idf: str):
  if _run:

    tank_params={
    'volume': "0.036", # Reem 36L tank
    'size': "1440",
    'skin_losses': "1.5",
    }

    # Building Config {{{
    #*****************
    mybldg = Building()
    mybldg.type_set( buildingType )
    mybldg.verbose_substitute = True
    #mybldg.verbose_substitute = False
    mybldg.location_set("Ontario")

    # TODO- set via external flag
    from sys import argv, exit
    try:
        _arg=argv[1]
        resil_flag=True
    except:
        resil_flag=False
    try:
        _arg=argv[2]
        outage_flag=True
    except:
        outage_flag=False
    print("Resil flag:",resil_flag)
    print("Outage flag:",outage_flag)


    mybldg.weather=weather
    mybldg.basename=idf # Revit translated, Hand converted to v9 (rm `Shading Control` from `FenestrationSurface:Detailed` This is the idf name passed from rhino. 

    mybldg.set_thermostats("HVACtemplate_thermosche_heat_resi", "HVACtemplate_thermosche_cool_resi")
    #======================================================
    ## Show all print/warning/sub statements from templater
    #======================================================
    verbose.verbose_set( mybldg.verbose_substitute )


    # EnergyPlus version
    mybldg.config.eplus_version_set("9.6.0")
    mybldg.config.run_eplus=False
    mybldg.config.force_recreate=False

    ## Names need to match task JSON keys
    mybldg.task_suffix= [ "prep", "ref", "prop", "opti" ]
    mybldg.set_filenames()
    prep_file=mybldg.task_filenames['prep'] # prep filenames used by dispatch_HVAC

    use_debug=True
    set_debugall(use_debug)
    options.debugall=use_debug
    options.debughvac=use_debug
    options.debugtherm=use_debug
    options.debuglight=use_debug
    options.debugelec=use_debug
    options.debugpv=use_debug
    options.debugshade=use_debug
    options.debugenduse=use_debug


    ### DHW Peak useage
    dhw_multi=0.800
    DHW_peak = 6.198e-006 * dhw_multi # m3/s
    DHW_heat_recov_frac = 0.8 # Able to recovery 20% of heat from drain. Less than typical 30% due to mixing with luke warm water
    #

    ## Lookup tables used in: make_ref, make_prop, build_opt
    HVAC_lkup={
              1 : add_HVAC_Baseboard,
              2 : add_HVAC_VRF,
    #          3 : add_HVAC_PTHP,
    #          2 : add_HVAC_FCU,
    }
    win_lkup={
              1 : 'DGLEAR',
              2 : 'TGLEAR',
    }
    DHW_lkup={
              #1 : add_DHWNGplant,
              1 : add_DHWElecTank,
              2 : add_DHWElecTank,
    #          1 : add_DHWHPplant,
    #          1 : add_DHWNGplant,
    #          4 : add_DHWNGplant,
    }

    #PV_eff=0.1581
    pv_frac=0.9

    # FOR- data_temp/nomad_3RV96.idf
    pv_omit_lst=[
      'zone_1_Srf_8',
    ]
    pv_add_lst=[
      'zone_1_Srf_12',
      'zone_1_Srf_11',
      'zone_1_Srf_0',
    ]

    hrly_output_vars=[
      #SB: Only use for debugging temperature profiles
      'Zone Mean Air Temperature',
      'Generator Produced DC Electric Power',  # Needed for Battery Charge/Discharge. Normally I use Meters.csv
      'Electric Storage Charge Power',         # Needed for Battery Charge/Discharge. Normally I use Meters.csv
      'Electric Storage Discharge Power',      # Needed for Battery Charge/Discharge. Normally I use Meters.csv
      'Electric Storage Battery Charge State', # Needed for Battery Charge/Discharge. Normally I use Meters.csv
      'Facility Total Building Electricity Demand Rate',
      'Inverter AC Output Electricity Rate',
      'Facility Net Purchased Electricity Rate',
      'Facility Net Purchased Electric Power', # Needed for Battery Charge/Discharge. Normally I use Meters.csv
      'Transformer Output Electric Power',
    ]

    # Used in hourly debugs (default)
    output_vars_meter=[
    'Photovoltaic:ElectricityProduced',
    'Cooling:EnergyTransfer',
    'Heating:EnergyTransfer',
    'Gas:Building',
    'Electricity:Building',
    'Water:Building',
    ]

    # Used in hourly debugs (only if debugall flag is set)
    output_vars_meter_debug=[
        'Electricity:HVAC',
        'Gas:HVAC',
        'InteriorLights:Electricity',
        'InteriorEquipment:Electricity',
    ]

    output_vars_meter_monthly=[
      "InteriorLights:Electricity",
      "InteriorEquipment:Electricity",
      "ExteriorEquipment:Electricity",
      "Pumps:Electricity",
      "Fans:Electricity",
      "Heating:Electricity",
      "Heating:Gas",
      "Cooling:Electricity",
      "HeatRejection:Electricity",
      "HeatRecovery:Electricity",
      "Humidification:Electricity",
      "WaterSystems:Electricity",
      "WaterSystems:Gas",
      "Generators:Electricity",
    ]

    output_vars_debugelec=[
      'Lights Electric Power',
      'Electric Equipment Electric Power',
    ]

    #dhw_zones=['restroom', 'bakery', 'cafeteria', 'breakroom', 'community room']
    dhw_zones=['apartment']

    prep_fnlist=[]

    # Common tasks for make_ref_90.1, make_ref, make_prop
    fn_common_tasks=[
      [ rm_all_HVAC_simple, True, {} ],
      #[ add_construction_materials, True, { 'const_file': "templates/ref_constructions_materials.idf" } ], # Adding Constructions/Materials from Template file
      #[ add_Daylight_zones, feat_dict['use_daylight'], {'file_name': prep_file, } ], # Adding daylighting to zones
      [ turn_off_comfort_warnings, True, {} ],
      [ add_site_BC, feat_dict['grnd_bc'], {} ], # Adding site boundary conditions
      [ mod_OutputTables, True, {} ],
      #[ remove_DHW_loads, True, {} ], # Adding Domestic Hot Water
      #[ add_vent_loads, True, { 'kitch':1, 'bath':2, 'file_name': prep_file } ], # Adding Exhaust to Apartment and Mech/Elec Rooms
      #[ add_enduse_outputs, options.debugelec, { 'timestep': "hourly", 'output_vars': output_vars_debugelec} ],
      ##NOTE- Surface lists used to extract areas. Used in later LCC
      [ add_misc_outputs, True, {'output_vars': ['\n  Output:Surfaces:List,lines;']} ],
      [ add_misc_outputs, True, {'output_vars': ['\n  Output:Surfaces:List,Details;']} ],
      #[ add_HVAC_RTU, True, {'no_mech_lst': ['plenum', 'tower', 'stairs', 'mechanical', 'storage', 'entry vestibule', 'exit vestibule', 'loadingdock']} ],
      # Ouputs to Meter Files
      [ add_enduse_outputs, True, { 'timestep': "hourly", 'output_vars': output_vars_meter} ],
      [ add_enduse_outputs, options.debugall, { 'timestep': "hourly", 'output_vars': output_vars_meter_debug} ],
      # Add/modify reporting tolerences for ASHRAE 55
      [ add_output_control, True, {} ],
      # Add humidity capacitance to building
      [ add_capacitance_multi, feat_dict['use_humid_cap'], {} ],
      # Add InternalMass Objects to building (Most suitable for Office Buildings)
      #[ add_internalmass, feat_dict['use_therm_mass'], {'file_name': prep_file, 'const_name':'FurnitureConstruction' } ],

      # Add monthly end use outputs for eQuest-like diagnostics
      #[ add_enduse_outputs, True, { 'timestep': "monthly", 'output_vars': output_vars_meter_monthly} ],

      #[ add_enduse_outputs, options.debugenduse, { 'timestep': "hourly"} ],
      # Thermal HT debugging parameters
      [ add_output_variables, options.debugtherm, {'output_vars': hrly_output_vars, 'timestep': 'hourly' } ],
      # Add extra warning in ERR file
      [ add_misc_outputs, True, {'output_vars': ['\nOutput:Diagnostics,DisplayExtraWarnings;']} ],
      # Modify simulation timestep if necessary
      [ mod_timesteps, True, { 'new_TS': feat_dict['timestep'] } ],
      # Enforce ASHRAE 62.1 ventilation standards
      [ enforce_ashrae62, feat_dict['enforce_ashrae62'], {} ],
      [ add_condfd, feat_dict['use_condfd'], {} ],
          ]

    _inp=find_JSON() # Get JSON, default to 'opti_inputs'
    def build_fnlist(json_value_key='value'):

        li_frac             = _inp['li_frac'][json_value_key]
        app_frac            = _inp['app_frac'][json_value_key]
        DHW_heat_recov_frac = _inp['dhw_recov'][json_value_key]
        #pv_frac             = _inp['pv_frac'][json_value_key]
        ins_extroof         = _inp['Rroof'][json_value_key]
        ins_extwall         = _inp['Rwall'][json_value_key]
        ins_extflor         = _inp['Rflor'][json_value_key]
        infil_frac          = _inp['infil_frac'][json_value_key]
        GTs                 = [_inp['gt_n'][json_value_key],
                              _inp['gt_e'][json_value_key],
                              _inp['gt_s'][json_value_key],
                              _inp['gt_w'][json_value_key],
                              ]
        dhwsys_type         = _inp['dhw_sys'][json_value_key]
        hvacsys_type        = _inp['hvac_sys'][json_value_key]
        azi                 = _inp['azi'][json_value_key]
        batt_size           = _inp['batt_size'][json_value_key]
        PV_eff              = _inp['pv_eff'][json_value_key]
        use_tank            = int(_inp['use_tankstorage'][json_value_key])
        #PV_eff=0.1581
        #batt_size=0.01
        #batt_size=20

        # Build fnlist
        _fnlist=[
        #      [ mod_azi, True, {  'azi': azi } ],
              [ add_construction_materials, True, { 'const_file': "templates/ref_constructions_materialsv96.idf" } ],
        #      # Update R-values, keep this, may be required afterwards
              [ mod_insul, True, { 'loc': "ExtRoof", 'resis': ins_extroof*5.678263337} ],
              [ mod_insul, True, { 'loc': "ExtWall", 'resis': ins_extwall*5.678263337} ],
              [ mod_insul, True, { 'loc': "ExtSlab", 'resis': ins_extflor*5.678263337} ],
        #      # Interior Lights
              [ mod_pd, True, { 'name': 'Lights', 'frac': li_frac/100.} ],
              [ mod_pd, True, { 'name': 'ElectricEquipment', 'frac': app_frac/100.} ],
        #      # Add Mech system
              # Oversize reduces unmet hours (especially in VRF systems)
              [ dispatch_HVAC, True, { 'add_HVAC_fn': HVAC_lkup[ hvacsys_type ], 'use_DOAS': True, 'use_district': False, 'to_file': prep_file, 'heat_oversize': 4, 'cool_oversize': 4 } ],
              #[ dispatch_HVAC, True, { 'add_HVAC_fn': HVAC_lkup[ hvacsys_type ], 'use_DOAS': True, 'use_district': False, 'to_file': prep_file } ],
        #      # DHW Fraction
              [ add_DHW_loads, True, {'frac': DHW_heat_recov_frac, 'water_temp': 43.3, 'file_name': prep_file, 'zones': dhw_zones, 'peak_use': DHW_peak } ],
        #      # DHW Plant system
              [ DHW_lkup[ dhwsys_type ],  True, tank_params],
        #      # Roof area: Hacked as azi=0
              [ add_PV_by_azi, True, { 'frac': pv_frac, 'azi': 0,   'pm': 0, 'Model': feat_dict['pv_model'],
                                      'PVcoupled': feat_dict['pv_couple'], 'file_name': prep_file, 'pv_eff':PV_eff,
                                      'add_surface_list': pv_add_lst, 'omit_surface_list': pv_omit_lst } ],
        #                               'omit_surface_list': pv_omit_lst } ],
        #                               'add_surface_list': pv_add_lst} ],
        #                               'add_surface_list': pv_add_lst, 'omit_surface_list': pv_omit_lst } ],
              [ mod_infil, True, { 'frac': infil_frac, }],
        #      ## Directions of Window Types: [north, east, south, west]
              [ mod_wintype, True, { 'wintypes': [win_lkup[int(gt)] for gt in GTs ], 'use_win7': feat_dict['use_win7'], 'file_name': prep_file } ],
        #      ## Directions of wwrs: [north, east, south, west]
        #      #[ mod_WWR, True, { 'wwrs': wwrs, 'file_name': prep_file  } ],


              # SB- set enable flag for WaterTank in opti_inputs.json (ref=False, prop=True)
              # Add thermal mass via 900L water tank (filled)
              [ add_internalmass, True, {'file_name': prep_file, 'const_name':'FurnitureConstruction'} ],
              #commented out by Dom
              ##[ add_internalmass, use_tank, {'file_name': prep_file, 'const_name':'WaterTank', 'suffix': "2"  } ],

    #           # Resiliency event. Limited simuilation
    #           [ add_resiliency_battery,  resil_flag,     {'zone_name': "zone_1", 'pv_list': "PV list 0", 'batt_size': batt_size, 'inverter_name': "Simple Ideal Inverter 0", 'battavail_sche':  "ALWAYS ON PV 0", 't_resil_start': t_start, 't_resil_stop': t_stop, 'outage_flag': outage_flag, 'sche_payload': sches_turnoff, 'sensor_elec': "Electricity" , 'sensor_suffix': "Rate"}],
    #           # Annual simulation. Add battery (cost savings but energy penalty) but don't simulate weather event
    #           [ add_resiliency_battery,  not resil_flag, {'zone_name': "zone_1", 'pv_list': "PV list 0", 'batt_size': batt_size, 'inverter_name': "Simple Ideal Inverter 0", 'battavail_sche':  "ALWAYS ON PV 0", 'sensor_elec': "Electricity" , 'sensor_suffix': "Rate"}],


        ]
        return _fnlist



    # Simulation Coordination {{{
    #*************************

    # TODO- for event in resiliency_events:
    # 0. IF switch: skip opti task.  Force run_eplus
    # 1. Build task list (resil1, resil2, ...)
    # 2. Calc VoLL: read in resiliency_events, and calc VoLL for each event
    # 3. cash_flow: read in each VoLL result and apply to LCC

    if resil_flag:

        # LOAD IN ALL JSON resiliency payloads
        json_resil=find_JSON("resiliency_events")
        for i,event_key in enumerate( json_resil.keys() ):
            # Use MODIFIED EPW with weather event
            mybldg.weather=json_resil[event_key]["EPW"]
            sches_turnoff=json_resil[event_key]["sches_turnoff"]
            t_start=json_resil[event_key]["t_start"]
            t_stop =json_resil[event_key]["t_stop"]
            resil_fnlist=build_fnlist(json_value_key='value')
            #resil_fnlist=build_fnlist(json_value_key='prop-value')
            mybldg.tasks= {
              "resil%d"%(i+1): join_lists(fn_common_tasks, resil_fnlist),
            }
            #mybldg.generate(force_recreate=True, run_eplus=True)
            mybldg.generate(force_recreate=True, run_eplus=False)

    else:
        t_start=0
        t_stop =0
        sches_turnoff={}
        # Build Ref:
        ref_fnlist=build_fnlist(json_value_key='ref-value')

        # Build Prop:
        prop_fnlist=build_fnlist(json_value_key='prop-value')

        # Build Opti:
        opti_fnlist=build_fnlist(json_value_key='value')

        mybldg.tasks= {
          "prep": prep_fnlist,
          #"ref":  join_lists(fn_common_tasks, ref_fnlist),
          "prop": join_lists(fn_common_tasks, prop_fnlist),
          #"opti": join_lists(fn_common_tasks, opti_fnlist),
        }

        mybldg.generate(force_recreate=True, run_eplus=True)
        sql_prep=r"C:\Users\domin\Documents\school2022\Summer\Directed Study\sim-NomadResilv96\sim-NomadResilv96\data_temp\Output\nomad_3RV96_prep.sql"
        sql_prep_prop=r"C:\Users\domin\Documents\school2022\Summer\Directed Study\sim-NomadResilv96\sim-NomadResilv96\data_temp\Output\nomad_3RV96_prep_prop.sql"
        return sql_prep,sql_prep_prop

    #Ref/Prop
    #mybldg.generate(force_recreate=True, run_eplus=True)

    #************************* }}}
 
if __name__ == "__main__":
    app.run()