#!/usr/bin/env python3
"Templates for E+ version 8.1 (and onwards). Templates are overloaded by later versions if changes to templates are required."

# TODO: build this file directly from Energy+.idd?

from string import Template # Allows for substitutions using {}

from templater import templater


def template_timestep():

    defaults={
      'timestep': "1",
    }

    temp_timestep = "\n  Timestep,${timestep};\n"

    return Template(temp_timestep), defaults

def template_meter_output():

    defaults={
      'timestep':     "Monthly",
    }

    temp_meter ="""\n  Output:Meter:MeterFileOnly,${var},${timestep};"""

    return Template(temp_meter), defaults

def template_meter_custom(N=1):
    """Returns a templated 'Meter:Custom' with 'N' entries"""

    defaults={
      'name':     "SuiteElectricity",
      'type':     "Electricity",
    }

    temp_mtr_suite_st = """
  Meter:Custom,
    ${name},         !- Name
    ${type},             !- Fuel Type
"""

    temp_mtr_suite_mi = """    ,       !- Key Name %(num)d
    ${var%(num)d},  !- Output Variable or Meter Name %(num)d
"""

    #===============================
    # Iterate over every meter entry
    #===============================
    temp_mtrlst = [ temp_mtr_suite_st ]
    #for j,mtr in enumerate(mtr_suite_nms):
    for j in range(N):
        if N>j+1 :
            temp_mtrlst.append(temp_mtr_suite_mi%{'num': j+1})
        else: # Last element in the Generation List. Special treatment required
            # NOTE: how to replace ',' with ';' at the last generator in genlist
            _t=temp_mtr_suite_mi%{'num': j+1}
            _t=_t.replace(',',';').replace(';',',',1)
            temp_mtrlst.append(_t)

    return Template(''.join(temp_mtrlst) ), defaults

def template_meter_decrement():

    defaults={
      'name': "CommonLightElectricity",
      'type': "Electricity",
      'src_mtr': "InteriorLights:Electricity",
      'mtr_name': "SuiteLightElectricity",
    }

    txt_mtr_decrement="""
  Meter:CustomDecrement,
    ${name},         !- Name
    ${type},             !- Fuel Type
    ${src_mtr},    !- Source Meter Name
    ,                        !- Key Name 1
    ${mtr_name};         !- Output Variable or Meter Name 1
"""

    return Template(''.join(txt_mtr_decrement) ), defaults

def template_output():

    defaults={
      #'timestep':     "timestep",
      #'timestep':     "hourly",
      'timestep':     "monthly",
    }

    temp_output="""\n  Output:Variable,*,${name},${timestep};"""

    return Template(temp_output), defaults


def template_output_control():

    defaults={
      'units': "JtoKWH",
    }

    temp_tbl="""
  OutputControl:Table:Style,
    HTML,                    !- Column Separator
    ${units};                  !- Unit Conversion
"""

    return Template(temp_tbl), defaults

def template_output_tolerance():

    defaults={
        'hsp_tolerance': "1.0",
        'csp_tolerance': "1.0",
    }

    temp_oc="""
  OutputControl:ReportingTolerances,
    ${hsp_tolerance},                     !- Tolerance for Time Heating Setpoint Not Met deltaC
    ${csp_tolerance};                     !- Tolerance for Time Cooling Setpoint Not Met deltaC
"""

    return Template(temp_oc), defaults

# Used by DHWNGplant
def SetpointManager():

    defaults={
      'name':     "SWHSys1 Loop Setpoint Manager",
      'sche_name':"SWHSys1-Loop-Temp-Schedule",
      'sp_name':  "SWHSys1 Supply Outlet Node",
    }

    temp_sp="""
  SetpointManager:Scheduled,
    ${name},  !- Name
    Temperature,             !- Control Variable
    ${sche_name},  !- Schedule Name
    ${sp_name};  !- Setpoint Node or NodeList Name
"""

    return Template(temp_sp), defaults



def DHW_WaterHeaterMixed():

    defaults={
      'volume': "0.3785", # m3
      'sch_nm': "SWHSys1 Water Heater Setpoint Temperature Schedule Name",
      'size': "845000",
      'fuel': "NATURALGAS",
      #'fuel': "Electricity",
      'eff': "0.8",
      'skin_losses': "0.6",
      'temp_sche': "SWHSys1 Water Heater Ambient Temperature Schedule Name",
    }

    txt_tank="""
  WaterHeater:Mixed,
    SWHSys1 Water Heater,    !- Name
    ${volume},                  !- Tank Volume {m3}
    ${sch_nm},  !- Setpoint Temperature Schedule Name
    2.0,                     !- Deadband Temperature Difference {deltaC}
    82.2222,                 !- Maximum Temperature Limit {C}
    Cycle,                   !- Heater Control Type
    ${size},                  !- Heater Maximum Capacity {W}
    ,                        !- Heater Minimum Capacity {W}
    ,                        !- Heater Ignition Minimum Flow Rate {m3/s}
    ,                        !- Heater Ignition Delay {s}
    ${fuel},              !- Heater Fuel Type
    ${eff},                     !- Heater Thermal Efficiency
    ,                        !- Part Load Factor Curve Name
    20,                      !- Off Cycle Parasitic Fuel Consumption Rate {W}
    ${fuel},              !- Off Cycle Parasitic Fuel Type
    0.8,                     !- Off Cycle Parasitic Heat Fraction to Tank
    ,                        !- On Cycle Parasitic Fuel Consumption Rate {W}
    ${fuel},              !- On Cycle Parasitic Fuel Type
    ,                        !- On Cycle Parasitic Heat Fraction to Tank
    SCHEDULE,                !- Ambient Temperature Indicator
    ${temp_sche},  !- Ambient Temperature Schedule Name
    ,                        !- Ambient Temperature Zone Name
    ,                        !- Ambient Temperature Outdoor Air Node Name
    ${skin_losses},                     !- Off Cycle Loss Coefficient to Ambient Temperature {W/K}
    ,                        !- Off Cycle Loss Fraction to Zone
    ${skin_losses},                     !- On Cycle Loss Coefficient to Ambient Temperature {W/K}
    ,                        !- On Cycle Loss Fraction to Zone
    ,                        !- Peak Use Flow Rate {m3/s}
    ,                        !- Use Flow Rate Fraction Schedule Name
    ,                        !- Cold Water Supply Temperature Schedule Name
    SWHSys1 Pump-SWHSys1 Water HeaterNode,  !- Use Side Inlet Node Name
    SWHSys1 Supply Equipment Outlet Node,  !- Use Side Outlet Node Name
    1.0,                     !- Use Side Effectiveness
    ,                        !- Source Side Inlet Node Name
    ,                        !- Source Side Outlet Node Name
    1.0,                     !- Source Side Effectiveness
    AUTOSIZE,                !- Use Side Design Flow Rate {m3/s}
    AUTOSIZE,                !- Source Side Design Flow Rate {m3/s}
    1.5;                     !- Indirect Water Heating Recovery Time {hr}
"""

    return Template(txt_tank), defaults

def DHW_WaterHeaterStratified():

    defaults={
      'volume': "0.3785", # m3
      'height': "1.4", # m
      'size_half': "1500", # m
      'sch_nm': "SWHSys1 Water Heater Setpoint Temperature Schedule Name",
      'fuel': "ELECTRICITY",
      'eff': "0.98",
      'temp_sche': "",
      'skin_coeff': "0.200",
      #'skin_coeff': "0.846",
    }

    txt_tank="""
  WaterHeater:Stratified,
    SWHSys1 Water Heater,            !- Name
    Water Heater,            !- End-Use Subcategory
    ${volume},                  !- Tank Volume {m3}
    ${height},                     !- Tank Height {m}
    VerticalCylinder,        !- Tank Shape
    ,                        !- Tank Perimeter {m}
    82.2222,                 !- Maximum Temperature Limit {C}
    MasterSlave,             !- Heater Priority Control
    ${sch_nm},  !- Heater 1 Setpoint Temperature Schedule Name
    2.0,                     !- Heater 1 Deadband Temperature Difference {deltaC}
    ${size_half},                    !- Heater 1 Capacity {W}
    1.0,                     !- Heater 1 Height {m}
    ${sch_nm},  !- Heater 2 Setpoint Temperature Schedule Name
    2.0,                     !- Heater 2 Deadband Temperature Difference {deltaC}
    ${size_half},                    !- Heater 2 Capacity {W}
    0.0,                     !- Heater 2 Height {m}
    ${fuel},             !- Heater Fuel Type
    ${eff},                    !- Heater Thermal Efficiency
    10,                      !- Off Cycle Parasitic Fuel Consumption Rate {W}
    ${fuel},             !- Off Cycle Parasitic Fuel Type
    0,                       !- Off Cycle Parasitic Heat Fraction to Tank
    ,                        !- Off Cycle Parasitic Height {m}
    30,                      !- On Cycle Parasitic Fuel Consumption Rate {W}
    ${fuel},             !- On Cycle Parasitic Fuel Type
    0,                       !- On Cycle Parasitic Heat Fraction to Tank
    ,                        !- On Cycle Parasitic Height {m}
    Outdoors,                !- Ambient Temperature Indicator
    ${temp_sche},                        !- Ambient Temperature Schedule Name
    ,                        !- Ambient Temperature Zone Name
    HPWHOutdoorTank OA Node, !- Ambient Temperature Outdoor Air Node Name
    ${skin_coeff},                   !- Uniform Skin Loss Coefficient per Unit Area to Ambient Temperature {W/m2-K}
    ,                        !- Skin Loss Fraction to Zone
    2.0,                     !- Off Cycle Flue Loss Coefficient to Ambient Temperature {W/K}
    1.0,                     !- Off Cycle Flue Loss Fraction to Zone
    0.000379,                !- Peak Use Flow Rate {m3/s}
    ,                        !- Use Flow Rate Fraction Schedule Name
    ,                        !- Cold Water Supply Temperature Schedule Name
    SWHSys1 Pump-SWHSys1 Water HeaterNode,  !- Use Side Inlet Node Name
    SWHSys1 Supply Equipment Outlet Node,  !- Use Side Outlet Node Name
    1.0,                     !- Use Side Effectiveness
    ,                        !- Use Side Inlet Height {m}
    ,                        !- Use Side Outlet Height {m}
    HPOutdoorWaterOutletNode,!- Source Side Inlet Node Name
    HPOutdoorWaterInletNode, !- Source Side Outlet Node Name
    0.98,                        !- Source Side Effectiveness
    ,                        !- Source Side Inlet Height {m}
    ,                        !- Source Side Outlet Height {m}
    FIXED,                   !- Inlet Mode
    autosize,                !- Use Side Design Flow Rate {m3/s}
    ,                        !- Source Side Design Flow Rate {m3/s}
    ,                        !- Indirect Water Heating Recovery Time {hr}
    6,                       !- Number of Nodes
    0.1,                     !- Additional Destratification Conductivity {W/m-K}
    0.15,                    !- Node 1 Additional Loss Coefficient {W/m2-K}
    ,                        !- Node 2 Additional Loss Coefficient {W/m2-K}
    ,                        !- Node 3 Additional Loss Coefficient {W/m2-K}
    ,                        !- Node 4 Additional Loss Coefficient {W/m2-K}
    ,                        !- Node 5 Additional Loss Coefficient {W/m2-K}
    0.1;                     !- Node 6 Additional Loss Coefficient {W/m2-K}
"""

    return Template(txt_tank), defaults

# TODO- Rough rewrite. Add template variables
def HVAC_HeatPumpWaterHeater():

    defaults={
        #'tank_type': 'WaterHeater:Mixed',
        'tank_type': 'WaterHeater:Stratified',
    }

    temp_heatpump="""
  WaterHeater:HeatPump,
    OutdoorHeatPumpWaterHeater,  !- Name
    PlantHPWHSch,            !- Availability Schedule Name
    HPWHTempSch,             !- Compressor Setpoint Temperature Schedule Name
    2.0,                     !- Dead Band Temperature Difference {deltaC}
    HPOutdoorWaterInletNode, !- Condenser Water Inlet Node Name
    HPOutdoorWaterOutletNode,!- Condenser Water Outlet Node Name
    0.00016,                 !- Condenser Water Flow Rate {m3/s}
    0.2685,                  !- Evaporator Air Flow Rate {m3/s}
    OutdoorAirOnly,          !- Inlet Air Configuration
    ,                        !- Air Inlet Node Name
    ,                        !- Air Outlet Node Name
    HPOutdoorAirInletNode,   !- Outdoor Air Node Name
    HPOutdoorAirOutletNode,  !- Exhaust Air Node Name
    ,                        !- Inlet Air Temperature Schedule Name
    ,                        !- Inlet Air Humidity Schedule Name
    ,                        !- Inlet Air Zone Name
    ${tank_type},       !- Tank Object Type
    SWHSys1 Water Heater,    !- Tank Name
    SWHSys1 Pump-SWHSys1 Water HeaterNode,  !-Tank Use Side Inlet Node Name
    SWHSys1 Supply Equipment Outlet Node,  !- Tank Use Side Outlet Node Name
    Coil:WaterHeating:AirToWaterHeatPump,  !- DX Coil Object Type
    HPWHOutdoorDXCoil,       !- DX Coil Name
    11.0,                    !- Minimum Inlet Air Temperature for Compressor Operation {C}
    Outdoors,                !- Compressor Location
    ,                        !- Compressor Ambient Temperature Schedule Name
    Fan:OnOff,               !- Fan Object Type
    HPWHOutdoorFan,          !- Fan Name
    BlowThrough,             !- Fan Placement
    ,                        !- On Cycle Parasitic Electric Load {W}
    ,                        !- Off Cycle Parasitic Electric Load {W}
    ;                        !- Parasitic Heat Rejection Location

  Coil:WaterHeating:AirToWaterHeatPump,
    HPWHOutdoorDXCoil,       !- Name
    4000.0,                  !- Rated Heating Capacity {W}
    3.2,                     !- Rated COP {W/W}
    0.736,                   !- Rated Sensible Heat Ratio
    29.44,                   !- Rated Evaporator Inlet Air Dry-Bulb Temperature {C}
    22.22,                   !- Rated Evaporator Inlet Air Wet-Bulb Temperature {C}
    55.72,                   !- Rated Condenser Inlet Water Temperature {C}
    0.2685,                  !- Rated Evaporator Air Flow Rate {m3/s}
    0.00016,                 !- Rated Condenser Water Flow Rate {m3/s}
    No,                      !- Evaporator Fan Power Included in Rated COP
    No,                      !- Condenser Pump Power Included in Rated COP
    No,                      !- Condenser Pump Heat Included in Rated Heating Capacity and Rated COP
    150.0,                   !- Condenser Water Pump Power {W}
    0.1,                     !- Fraction of Condenser Pump Heat to Water
    HPOutdoorFanAirOutletNode,  !- Evaporator Air Inlet Node Name
    HPOutdoorAirOutletNode,  !- Evaporator Air Outlet Node Name
    HPOutdoorWaterInletNode, !- Condenser Water Inlet Node Name
    HPOutdoorWaterOutletNode,!- Condenser Water Outlet Node Name
    100.0,                   !- Crankcase Heater Capacity {W}
    5.0,                     !- Maximum Ambient Temperature for Crankcase Heater Operation {C}
    WetBulbTemperature,      !- Evaporator Air Temperature Type for Curve Objects
    HPWHHeatingCapFTemp,     !- Heating Capacity Function of Temperature Curve Name
    ,                        !- Heating Capacity Function of Air Flow Fraction Curve Name
    ,                        !- Heating Capacity Function of Water Flow Fraction Curve Name
    HPWHHeatingCOPFTemp,     !- Heating COP Function of Temperature Curve Name
    ,                        !- Heating COP Function of Air Flow Fraction Curve Name
    ,                        !- Heating COP Function of Water Flow Fraction Curve Name
    HPWHPLFFPLR;             !- Part Load Fraction Correlation Curve Name

  Fan:OnOff,
    HPWHOutdoorFan,          !- Name
    PlantHPWHSch,            !- Availability Schedule Name
    0.7,                     !- Fan Efficiency
    100.0,                   !- Pressure Rise {Pa}
    0.2685,                  !- Maximum Flow Rate {m3/s}
    0.9,                     !- Motor Efficiency
    1.0,                     !- Motor In Airstream Fraction
    HPOutdoorAirInletNode,   !- Air Inlet Node Name
    HPOutdoorFanAirOutletNode;  !- Air Outlet Node Name

  Curve:Quadratic,
    HPWHPLFFPLR,             !- Name
    0.75,                    !- Coefficient1 Constant
    0.25,                    !- Coefficient2 x
    0.0,                     !- Coefficient3 x**2
    0.0,                     !- Minimum Value of x
    1.0;                     !- Maximum Value of x

  Curve:Biquadratic,
    HPWHHeatingCapFTemp,     !- Name
    0.369827,                !- Coefficient1 Constant
    0.043341,                !- Coefficient2 x
    -0.00023,                !- Coefficient3 x**2
    0.000466,                !- Coefficient4 y
    0.000026,                !- Coefficient5 y**2
    -0.00027,                !- Coefficient6 x*y
    0.0,                     !- Minimum Value of x
    40.0,                    !- Maximum Value of x
    20.0,                    !- Minimum Value of y
    90.0,                    !- Maximum Value of y
    ,                        !- Minimum Curve Output
    ,                        !- Maximum Curve Output
    Temperature,             !- Input Unit Type for X
    Temperature,             !- Input Unit Type for Y
    Dimensionless;           !- Output Unit Type

  Curve:Biquadratic,
    HPWHHeatingCOPFTemp,     !- Name
    1.19713,                 !- Coefficient1 Constant
    0.077849,                !- Coefficient2 x
    -0.0000016,              !- Coefficient3 x**2
    -0.02675,                !- Coefficient4 y
    0.000296,                !- Coefficient5 y**2
    -0.00112,                !- Coefficient6 x*y
    0.0,                     !- Minimum Value of x
    40.0,                    !- Maximum Value of x
    20.0,                    !- Minimum Value of y
    90.0,                    !- Maximum Value of y
    ,                        !- Minimum Curve Output
    ,                        !- Maximum Curve Output
    Temperature,             !- Input Unit Type for X
    Temperature,             !- Input Unit Type for Y
    Dimensionless;           !- Output Unit Type
"""

    return Template(temp_heatpump), defaults

def DHW_PipeAdiabatic():

    defaults={
    }

    txt_pipe="""
  Pipe:Adiabatic,
    ${name},  !- Name
    ${inlet},  !- Inlet Node Name
    ${outlet};  !- Outlet Node Name
"""

    return Template(txt_pipe), defaults

def Water_Connections():

    defaults={
    }

    txt_water="""
  WaterUse:Connections,
    ${name},  !- Name
    ${inlet_node},  !- Inlet Node Name
    ${outlet_node},  !- Outlet Node Name
    ,                        !- Supply Water Storage Tank Name
    ,                        !- Reclamation Water Storage Tank Name
    ,                        !- Hot Water Supply Temperature Schedule Name
    ,                        !- Cold Water Supply Temperature Schedule Name
    ,                        !- Drain Water Heat Exchanger Type
    ,                        !- Drain Water Heat Exchanger Destination
    ,                        !- Drain Water Heat Exchanger U-Factor Times Area {W/K}
    ${eq_name};  !- Water Use Equipment 1 Name
"""

    return Template(txt_water), defaults

def HVACtemplate_thermostat():

    temp_therm="""
  HVACTemplate:Thermostat,
    ${thermo_nm},               !- Name
    ${hsp_sche},            !- Heating Setpoint Schedule Name
    ,                        !- Constant Heating Setpoint {C}
    ${csp_sche},            !- Cooling Setpoint Schedule Name
    ;                        !- Constant Cooling Setpoint {C}
"""

    return Template(temp_therm), {}

# SB NOTE: Can reuse a common file between resi/comm. Ex. Setpoints and setbacks, no conditioning on weekends, etc
def HVACtemplate_thermosche_heat_comm():

    defaults={
      'name':     "Htg-SetP-Sch10",
      'setback':  "13.0",
      'ramp':     "18.0",
      'setpoint': "23.0",
      'time_sb':  "6:00",
      'time_rp':  "7:00",
      'time_sp':  "21:00",
      'date_OFF': "6/01",
      'date_ON':  "10/1",
    }

    txt_thermsch="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_OFF},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: WeekEnds Holiday,   !- Field 11
    Until: 24:00,${setback},       !- Field 12
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: ${date_ON},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: WeekEnds Holiday,   !- Field 11
    Until: 24:00,${setback},       !- Field 12
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: 12/31,          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: WeekEnds Holiday,   !- Field 11
    Until: 24:00,${setback},       !- Field 12
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint};       !- Field 18
"""

    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_heat_resi():

    defaults={
      'name':     "Htg-SetP-Sch10",
      'setback':  "17.0",
      'ramp':     "18.0",
      'setpoint': "23.0",
      'time_sb':  "6:00",
      'time_rp':  "7:00",
      'time_sp':  "21:00",
      'date_OFF': "6/01",
      'date_ON':  "10/1",
    }

    txt_thermsch_global_resi="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_OFF},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: WeekEnds Holiday,   !- Field 11
    Until: 24:00,${setpoint},       !- Field 12
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setpoint},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: ${date_ON},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_sp},${setback},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: WeekEnds Holiday,   !- Field 11
    Until: 24:00,${setback},       !- Field 12
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: 12/31,          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: WeekEnds Holiday,   !- Field 11
    Until: 24:00,${setpoint},       !- Field 12
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setpoint},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint};       !- Field 18
"""


    return Template(txt_thermsch_global_resi), defaults


def HVACtemplate_thermosche_cool_comm():

    defaults={
      'name':     "Clg-SetP-Sch10",
      'setback':  "32.0",
      'ramp':     "28.0",
      'setpoint': "25.0",
      'time_sb':  "6:00",
      'time_rp':  "7:00",
      'time_sp':  "21:00",
      'date_OFF': "10/15",
      'date_ON':  "5/15",
    }

    txt_thermsch="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_ON},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: WeekEnds Holiday,   !- Field 9
    Until: 24:00,${setback},       !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: ${date_OFF},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: WeekEnds Holiday,   !- Field 9
    Until: 24:00,${setback},       !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: WeekEnds Holiday,   !- Field 9
    Until: 24:00,${setback},       !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback};       !- Field 16
"""


    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_cool_resi():

    defaults={
      'name':     "Clg-SetP-Sch10",
      'setback':  "32.0",
      'ramp':     "28.0",
      'setpoint': "25.0",
      'time_sb':  "6:00",
      'time_rp':  "7:00",
      'time_sp':  "21:00",
      'date_OFF': "10/15",
      'date_ON':  "5/15",
    }

    txt_thermsch="""
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_ON},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: WeekEnds Holiday,   !- Field 9
    Until: 24:00,${setback},       !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: ${date_OFF},          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setpoint},        !- Field 3
    Until: ${time_rp},${setpoint},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setpoint},       !- Field 7
    For: WeekEnds Holiday,   !- Field 9
    Until: 24:00,${setpoint},       !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: WeekEnds Holiday,   !- Field 9
    Until: 24:00,${setback},       !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback};       !- Field 16
"""

    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_district():

    # District-Loop-Temp-Low-Schedule
    # 'temp_low':  "15.0",
    # 'temp_high':  "30.0",
    #
    # District-Loop-Temp-High-Schedule
    # 'temp_low':  "20.0",
    # 'temp_high':  "40.0",
    defaults={
      'temp_low':  "15.0",
      'temp_high':  "30.0",
      'date_start': "6/1",
      'date_stop':  "10/1",
    }

    txt_thermsch="""
  Schedule:Compact,
    ${name},  !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_start},          !- Field 1
    For: AllDays,            !- Field 2
    Until: 24:00,${temp_low},       !- Field 3
    Through: ${date_stop},          !- Field 4
    For: AllDays,            !- Field 5
    Until: 24:00,${temp_high},       !- Field 6
    Through: 12/31,          !- Field 7
    For: AllDays,            !- Field 8
    Until: 24:00,${temp_low};       !- Field 9
"""

    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_simple():

    defaults={
      # Heating setpoints
      'temp1':  "18.0",
      'temp2':  "13.0",
      'temp3':  "23.0",
      ## Cooling setpoints
      #'temp1':  "30.0",
      #'temp2':  "24.0",
      #'temp3':  "32.0",
      #'date':  "12/31",
    }

    thermo_simple="""
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,${temp1},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${temp2},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${temp3};       !- Field 18
"""

    return Template(thermo_simple), defaults

# SB: Used by VRFnoboiler, VRFdist
def HVACtemplate_schedule_alwaysON():

    #FanAvailSchedVRF
    #ExteriorLights
    defaults={
      'frac':       "1",
      'type':       "Fraction",
      #'type':       "Any Number",
    }

    txt_availsch="""\n
  Schedule:Compact,
    ${name},           !- Name
    ${type},                !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: AllDays,            !- Field 2
    Until: 24:00,${frac};        !- Field 3
"""


    return Template(txt_availsch), defaults

def HVACtemplate_schedule_alwaysON2():

    defaults={
      'frac':       "1",
      'limits':       "Dimensionless",
    }

    #txt_availsch=""" Schedule:Constant,${name},,1.0; """
    txt_availsch="""
  Schedule:Constant,
    ${name},               !- Name
    ${limits},                     !- Schedule Type Limits Name
    ${frac};                       !- Hourly Value
"""

    return Template(txt_availsch), defaults

# SB NOTE: unavailability from 3/31 till 9/30 is consist in all HVACTemplate examples
#   Should this be always ON and let the thermostat handle the setpoint?
def HVACtemplate_schedule_avail():

    defaults={
      'frac_OFF':       "0.0",
      'frac_ON':        "1.0",
      'time_frac':      "6:00",
      'time_ON':        "20:00",
      'date_alwaysON':  "3/31",
      'date_fracON':    "9/30",
    }

    txt_availsch="""\n
  Schedule:Compact,
    ${avail_nm},           !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: ${date_alwaysON},           !- Field 1
    For: AllDays,            !- Field 2
    Until: 24:00,${frac_ON},        !- Field 3
    Through: ${date_fracON},           !- Field 5
    For: WeekDays,           !- Field 6
    Until: ${time_frac},${frac_OFF},         !- Field 7
    Until: ${time_ON},${frac_ON},        !- Field 9
    Until: 24:00,${frac_OFF},        !- Field 11
    For: SummerDesignDay WinterDesignDay, !- Field 13
    Until: 24:00,${frac_ON},        !- Field 14
    For: AllOtherDays,       !- Field 16
    Until: 24:00,${frac_OFF},        !- Field 17
    Through: 12/31,          !- Field 19
    For: AllDays,            !- Field 20
    Until: 24:00,${frac_ON};        !- Field 21
"""

    return Template(txt_availsch), defaults

#   Should this be always ON and let the thermostat handle the setpoint?
def HVACtemplate_OAschedule_avail():

    defaults={ }

    txt_OAavailsch="""\n
  Schedule:Compact,
    ${oa_sche},            !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: WeekDays CustomDay1 CustomDay2, !- Field 2
    Until: 8:00,0.0,         !- Field 3
    Until: 21:00,1.0,        !- Field 5
    Until: 24:00,0.0,        !- Field 7
    For: Weekends Holiday,   !- Field 9
    Until: 24:00,0.0,        !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1.0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1.0;        !- Field 16
"""

    return Template(txt_OAavailsch), defaults

def HVACtemplate_office_essen_avail():

    defaults={
             }

    txt_availsch="""
  Schedule:Compact,
    ${name},        !- Name
    Fraction,              !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: Weekdays,           !- Field 2
    Until: 6:00,0.00,        !- Field 3
    Until: 7:00,0.10,        !- Field 5
    Until: 8:00,0.50,        !- Field 7
    Until: 12:00,0.50,       !- Field 9
    Until: 13:00,0.50,       !- Field 11
    Until: 16:00,0.25,       !- Field 13
    Until: 17:00,0.25,       !- Field 15
    Until: 18:00,0.10,       !- Field 17
    Until: 24:00,0.00,       !- Field 19
    For: Weekends Holidays CustomDay1 CustomDay2, !- Field 21
    Until: 24:00,0.00,       !- Field 22
    For: SummerDesignDay,    !- Field 24
    Until: 24:00,1.00,       !- Field 25
    For: WinterDesignDay,    !- Field 27
    Until: 24:00,0.05;  !- Field 28
"""

    return Template(txt_availsch), defaults

def HVACtemplate_resi_essen_avail():

    defaults={
             }

    txt_availsch="""
  Schedule:Compact,
    ${name},        !- Name
    ANY NUMBER,              !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: Weekdays Weekends Holidays CustomDay1 CustomDay2,           !- Field 2
    Until: 24:00,0.70,       !- Field 19
    For: SummerDesignDay,    !- Field 24
    Until: 24:00,1.00,       !- Field 25
    For: WinterDesignDay,    !- Field 27
    Until: 24:00,0.05;  !- Field 28
"""

    return Template(txt_availsch), defaults

def HVACtemplate_resi_essen_avail():

    defaults={
             }

    txt_availsch="""\n
"""

    return Template(txt_availsch), defaults

def HVACtemplate_boiler():

    defaults={
      'boiler_name': "Main Boiler",
      'boiler_type': "HotWaterBoiler",
      'boiler_eff': "0.8",
      'boiler_fuel': "NaturalGas",
    }

    temp_boiler="""
  HVACTemplate:Plant:Boiler,
    ${boiler_name},             !- Name
    ${boiler_type},          !- Boiler Type
    autosize,                !- Capacity {W}
    ${boiler_eff},                     !- Efficiency
    ${boiler_fuel},              !- Fuel Type
    1,                       !- Priority
    ;                        !- Sizing Factor
"""

    return Template(temp_boiler), defaults


def HVACtemplate_chiller():

    defaults={
      'chiller_name': "Main Chiller",
      'chiller_type': "ElectricReciprocatingChiller",
      'chiller_COP': "3.2",
      'condenser_type': "WaterCooled",
    }

    temp_chiller="""
  HVACTemplate:Plant:Chiller,
    ${chiller_name},            !- Name
    ${chiller_type},  !- Chiller Type
    autosize,                !- Capacity {W}
    ${chiller_COP},                     !- Nominal COP {W/W}
    ${condenser_type},             !- Condenser Type
    1,                       !- Priority
    ;                        !- Sizing Factor
"""

    return Template(temp_chiller), defaults

def HVACtemplate_tower():

    defaults={
      'tower_name': "Main Tower",
      'tower_type': "SingleSpeed",
    }

    temp_tower="""
  HVACTemplate:Plant:Tower,
    ${tower_name},              !- Name
    ${tower_type},             !- Tower Type
    autosize,                !- High Speed Nominal Capacity {W}
    autosize,                !- High Speed Fan Power {W}
    autosize,                !- Low Speed Nominal Capacity {W}
    autosize,                !- Low Speed Fan Power {W}
    autosize,                !- Free Convection Capacity {W}
    1,                       !- Priority
    ;                        !- Sizing Factor
"""

    return Template(temp_tower), defaults

def HVACtemplate_MWL():

    defaults={
      'MWL_name':      "Only Water Loop",
      'temp_hsp_sche': "",
      'temp_hsp':      "30",
      'temp_lsp_sche': "",
      'temp_lsp':      "20",
    }

    temp_MWL="""
  HVACTemplate:Plant:MixedWaterLoop,
    ${MWL_name},         !- Name
    ,                        !- Pump Schedule Name
    Intermittent,            !- Pump Control Type
    Default,                 !- Operation Scheme Type
    ,                        !- Equipment Operation Schemes Name
    ${temp_hsp_sche},                        !- High Temperature Setpoint Schedule Name
    ${temp_hsp},                      !- High Temperature Design Setpoint {C}
    ${temp_lsp_sche},                        !- Low Temperature Setpoint Schedule Name
    ${temp_lsp},                      !- Low Temperature Design Setpoint {C}
    ConstantFlow,            !- Water Pump Configuration
    179352;                  !- Water Pump Rated Head {Pa}
"""

    return Template(temp_MWL), defaults

def HVACtemplate_CWL():

    defaults={
      'CWL_name': "Chilled Water Loop",
      'CWL_config': "ConstantPrimaryNoSecondary",
      # Added for DOAS CWL (default was no limit)
      'outdoor_temp': "7.22",
    }

    temp_CWL="""
  HVACTemplate:Plant:ChilledWaterLoop,
    ${CWL_name},      !- Name
    ,                        !- Pump Schedule Name
    INTERMITTENT,            !- Pump Control Type
    Default,                 !- Chiller Plant Operation Scheme Type
    ,                        !- Chiller Plant Equipment Operation Schemes Name
    ,                        !- Chilled Water Setpoint Schedule Name
    7.22,                    !- Chilled Water Design Setpoint {C}
    ${CWL_config},  !- Chilled Water Pump Configuration
    179352,                  !- Primary Chilled Water Pump Rated Head {Pa}
    179352,                  !- Secondary Chilled Water Pump Rated Head {Pa}
    Default,                 !- Condenser Plant Operation Scheme Type
    ,                        !- Condenser Equipment Operation Schemes Name
    ,                        !- Condenser Water Temperature Control Type
    ,                        !- Condenser Water Setpoint Schedule Name
    29.4,                    !- Condenser Water Design Setpoint {C}
    179352,                  !- Condenser Water Pump Rated Head {Pa}
    OutdoorAirTemperatureReset,  !- Chilled Water Setpoint Reset Type
    12.2,                    !- Chilled Water Setpoint at Outdoor Dry-Bulb Low {C}
    15.6,                    !- Chilled Water Reset Outdoor Dry-Bulb Low {C}
    6.7,                     !- Chilled Water Setpoint at Outdoor Dry-Bulb High {C}
    26.7,                    !- Chilled Water Reset Outdoor Dry-Bulb High {C}
    ,                        !- Chilled Water Primary Pump Type
    ,                        !- Chilled Water Secondary Pump Type
    ,                        !- Condenser Water Pump Type
    ,                        !- Chilled Water Supply Side Bypass Pipe
    ,                        !- Chilled Water Demand Side Bypass Pipe
    ,                        !- Condenser Water Supply Side Bypass Pipe
    ,                        !- Condenser Water Demand Side Bypass Pipe
    ,                        !- Fluid Type
    ,                        !- Loop Design Delta Temperature {deltaC}
    ${outdoor_temp};                    !- Minimum Outdoor Dry Bulb Temperature {C}
"""

    return Template(temp_CWL), defaults

def HVACtemplate_HWL():

    defaults={
      'HWL_name': "Hot Water Loop",
      'HWL_config': "ConstantFlow",
      'HWL_setpoint_reset': "OutdoorAirTemperatureReset",
      'pump_head': "179352",
    }

    temp_HWL="""
  HVACTemplate:Plant:HotWaterLoop,
    ${HWL_name},          !- Name
    ,                        !- Pump Schedule Name
    INTERMITTENT,            !- Pump Control Type
    Default,                 !- Hot Water Plant Operation Scheme Type
    ,                        !- Hot Water Plant Equipment Operation Schemes Name
    ,                        !- Hot Water Setpoint Schedule Name
    82,                      !- Hot Water Design Setpoint {C}
    ${HWL_config},            !- Hot Water Pump Configuration
    ${pump_head},                  !- Hot Water Pump Rated Head {Pa}
    ${HWL_setpoint_reset},  !- Hot Water Setpoint Reset Type
    82.2,                    !- Hot Water Setpoint at Outdoor Dry-Bulb Low {C}
    -6.7,                    !- Hot Water Reset Outdoor Dry-Bulb Low {C}
    65.6,                    !- Hot Water Setpoint at Outdoor Dry-Bulb High {C}
    10;                      !- Hot Water Reset Outdoor Dry-Bulb High {C}
"""

    return Template(temp_HWL), defaults

def HVACtemplate_Ideal_zone():

#    temp_ideal="""
#  HVACTemplate:Zone:IdealLoadsAirSystem,
#    ${zone_name},                !- Zone Name
#    ${thermo_name};               !- Template Thermostat Name
#"""

    temp_ideal="""
  HVACTemplate:Zone:IdealLoadsAirSystem,
    ${zone_name},                !- Zone Name
    ${thermo_name},               !- Template Thermostat Name
    ,                        !- System Availability Schedule Name
    50,                      !- Maximum Heating Supply Air Temperature {C}
    13,                      !- Minimum Cooling Supply Air Temperature {C}
    0.0156,                  !- Maximum Heating Supply Air Humidity Ratio {kgWater/kgDryAir}
    0.0077,                  !- Minimum Cooling Supply Air Humidity Ratio {kgWater/kgDryAir}
    NoLimit,                 !- Heating Limit
    ,                        !- Maximum Heating Air Flow Rate {m3/s}
    ,                        !- Maximum Sensible Heating Capacity {W}
    NoLimit,                 !- Cooling Limit
    ,                        !- Maximum Cooling Air Flow Rate {m3/s}
    ,                        !- Maximum Total Cooling Capacity {W}
    ,                        !- Heating Availability Schedule Name
    ,                        !- Cooling Availability Schedule Name
    ConstantSensibleHeatRatio,  !- Dehumidification Control Type
    0.7,                     !- Cooling Sensible Heat Ratio {dimensionless}
    ,                        !- Dehumidification Setpoint {percent}
    None,                    !- Humidification Control Type
    30,                      !- Humidification Setpoint {percent}
    None,                    !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    ,                        !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Outdoor Air Flow Rate per Zone {m3/s}
    ,                        !- Design Specification Outdoor Air Object Name
    None,                    !- Demand Controlled Ventilation Type
    NoEconomizer,            !- Outdoor Air Economizer Type
    None,                    !- Heat Recovery Type
    0.7,                     !- Sensible Heat Recovery Effectiveness {dimensionless}
    0.65;                    !- Latent Heat Recovery Effectiveness {dimensionless}

"""

    return Template(temp_ideal), {}

def HVACtemplate_VAV_system():

    defaults={
      'vav_name': "DXVAV Sys 1",
      'fan_sch': "FanAvailSchedVAVelec",
      'hcoil_type': "Gas",
      'ccoil_type': "TwoSpeedDX",
      'oa_sche': "Min OA Sched VAVelec",
    }

    temp_sys_vav="""
  HVACTemplate:System:PackagedVAV,
    ${vav_name},             !- Name
    ${fan_sch},           !- System Availability Schedule Name
    autosize,                !- Supply Fan Maximum Flow Rate {m3/s}
    autosize,                !- Supply Fan Minimum Flow Rate {m3/s}
    DrawThrough,             !- Supply Fan Placement
    0.7,                     !- Supply Fan Total Efficiency
    1000,                    !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    1,                       !- Supply Fan Motor in Air Stream Fraction
    ${ccoil_type},              !- Cooling Coil Type
    ,                        !- Cooling Coil Availability Schedule Name
    ,                        !- Cooling Coil Setpoint Schedule Name
    12.8,                    !- Cooling Coil Design Setpoint {C}
    autosize,                !- Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- Cooling Coil Gross Rated Sensible Heat Ratio
    3,                       !- Cooling Coil Gross Rated COP {W/W}
    ${hcoil_type},                     !- Heating Coil Type
    ,                        !- Heating Coil Availability Schedule Name
    ,                        !- Heating Coil Setpoint Schedule Name
    10,                      !- Heating Coil Design Setpoint {C}
    autosize,                !- Heating Coil Capacity {W}
    0.8,                     !- Gas Heating Coil Efficiency
    ,                        !- Gas Heating Coil Parasitic Electric Load {W}
    autosize,                !- Maximum Outdoor Air Flow Rate {m3/s}
    autosize,                !- Minimum Outdoor Air Flow Rate {m3/s}
    ProportionalMinimum,     !- Minimum Outdoor Air Control Type
    ${oa_sche},            !- Minimum Outdoor Air Schedule Name
    DifferentialDryBulb,     !- Economizer Type
    NoLockout,               !- Economizer Lockout
    19,                      !- Economizer Maximum Limit Dry-Bulb Temperature {C}
    ,                        !- Economizer Maximum Limit Enthalpy {J/kg}
    ,                        !- Economizer Maximum Limit Dewpoint Temperature {C}
    4,                       !- Economizer Minimum Limit Dry-Bulb Temperature {C}
    ,                        !- Supply Plenum Name
    ,                        !- Return Plenum Name
    InletVaneDampers,        !- Supply Fan Part-Load Power Coefficients
    CycleOnAny,              !- Night Cycle Control
    ,                        !- Night Cycle Control Zone Name
    None,                    !- Heat Recovery Type
    0.7,                     !- Sensible Heat Recovery Effectiveness
    0.65,                    !- Latent Heat Recovery Effectiveness
    None,                    !- Cooling Coil Setpoint Reset Type
    None,                    !- Heating Coil Setpoint Reset Type
    None,                    !- Dehumidification Control Type
    ,                        !- Dehumidification Control Zone Name
    60,                      !- Dehumidification Setpoint {percent}
    None,                    !- Humidifier Type
    ,                        !- Humidifier Availability Schedule Name
    0.000001,                !- Humidifier Rated Capacity {m3/s}
    2690,                    !- Humidifier Rated Electric Power {W}
    ,                        !- Humidifier Control Zone Name
    30,                      !- Humidifier Setpoint {percent}
    NonCoincident,           !- Sizing Option
    ,                        !- Return Fan
    ,                        !- Return Fan Total Efficiency
    ,                        !- Return Fan Delta Pressure {Pa}
    ,                        !- Return Fan Motor Efficiency
    ,                        !- Return Fan Motor in Air Stream Fraction
    ;                        !- Return Fan Part-Load Power Coefficients
"""

    return Template(temp_sys_vav), defaults


def HVACtemplate_VAV_zone():

    defaults={
      'sys_name': "DXVAV Sys 1",
      'thermo_name': "All Zones10",
      'fan_sch': "FanAvailSchedVAVelec",
      'hcoil_type': "Electric",
    }

    temp_zone_vav="""
  HVACTemplate:Zone:VAV,
    ${zone_name},                !- Zone Name
    ${sys_name},             !- Template VAV System Name
    ${thermo_name},              !- Template Thermostat Name
    autosize,                !- Supply Air Maximum Flow Rate {m3/s}
    ,                        !- Zone Heating Sizing Factor
    ,                        !- Zone Cooling Sizing Factor
    Constant,                !- Zone Minimum Air Flow Input Method
    0.3,                     !- Constant Minimum Air Flow Fraction
    ,                        !- Fixed Minimum Air Flow Rate {m3/s}
    ,                        !- Minimum Air Flow Fraction Schedule Name
    flow/person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    0.0,                     !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    0.0,                     !- Outdoor Air Flow Rate per Zone {m3/s}
    ${hcoil_type},                !- Reheat Coil Type
    ,                        !- Reheat Coil Availability Schedule Name
    Reverse,                 !- Damper Heating Action
    ,                        !- Maximum Flow per Zone Floor Area During Reheat {m3/s-m2}
    ,                        !- Maximum Flow Fraction During Reheat
    ,                        !- Maximum Reheat Air Temperature {C}
    ,                        !- Design Specification Outdoor Air Object Name for Control
    ,                        !- Supply Plenum Name
    ,                        !- Return Plenum Name
    None,                    !- Baseboard Heating Type
    ,                        !- Baseboard Heating Availability Schedule Name
    autosize,                !- Baseboard Heating Capacity {W}
    SystemSupplyAirTemperature,  !- Zone Cooling Design Supply Air Temperature Input Method
    ,                        !- Zone Cooling Design Supply Air Temperature {C}
    ,                        !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SupplyAirTemperature,    !- Zone Heating Design Supply Air Temperature Input Method
    50.0,                    !- Zone Heating Design Supply Air Temperature {C}
    ;                        !- Zone Heating Design Supply Air Temperature Difference {deltaC}
"""

    return Template(temp_zone_vav), defaults


def HVACtemplate_FCU_zone():

    defaults={
      'fan_sch': "FanAvailSchedFCU",
      'doas_name': "",
    }

    temp_zone_fcu="""
  HVACTemplate:Zone:FanCoil,
    ${zone_name},                !- Zone Name
    ${thermo_name},               !- Template Thermostat Name
    autosize,                !- Supply Air Maximum Flow Rate {m3/s}
    1.5,                        !- Zone Heating Sizing Factor
    ,                        !- Zone Cooling Sizing Factor
    flow/person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    0.0,                     !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    0.0,                     !- Outdoor Air Flow Rate per Zone {m3/s}
    ${fan_sch},           !- System Availability Schedule Name
    0.7,                     !- Supply Fan Total Efficiency
    75,                      !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    1,                       !- Supply Fan Motor in Air Stream Fraction
    ChilledWater,            !- Cooling Coil Type
    ,                        !- Cooling Coil Availability Schedule Name
    12.5,                    !- Cooling Coil Design Setpoint {C}
    HotWater,                !- Heating Coil Type
    ,                        !- Heating Coil Availability Schedule Name
    50,                      !- Heating Coil Design Setpoint {C}
    ${doas_name},                        !- Dedicated Outdoor Air System Name
    SupplyAirTemperature,    !- Zone Cooling Design Supply Air Temperature Input Method
    ,                        !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SupplyAirTemperature,    !- Zone Heating Design Supply Air Temperature Input Method
    ,                        !- Zone Heating Design Supply Air Temperature Difference {deltaC}
    ,                        !- Design Specification Outdoor Air Object Name
    ,                        !- Design Specification Zone Air Distribution Object Name
    ,                        !- Capacity Control Method
    ,                        !- Low Speed Supply Air Flow Ratio
    ,                        !- Medium Speed Supply Air Flow Ratio
    ,                        !- Outdoor Air Schedule Name
    ,                        !- Baseboard Heating Type
    ,                        !- Baseboard Heating Availability Schedule Name
    ;                        !- Baseboard Heating Capacity {W}
"""


    return Template(temp_zone_fcu), defaults

def HVACtemplate_PTHP_zone():

    defaults={
      'doas_name': "",
      'heat_COP': "2.75",
      'cool_COP': "3.00",
      'heat_avail': "", # Added for Mexico Privanzas project
      'cool_avail': "",
      'sys_avail': "HVAC Avail Sche", # Added for resiliency studies (need to override)
    }

    # NOTE- This doesn't work since supplemental heat can't be turned off in this object
    ## Override supplemental heating for resiliency studies
    #if defaults['sys_avail']:
    #    defaults['supp_heat']="None"

    #All Zones3,               !- Template Thermostat Name
    #ReverseCycle,            !- Heat Pump Defrost Strategy
    # Default COPs:
    #2.75,                    !- Heat Pump Heating Coil Gross Rated COP {W/W}
    #3,                       !- Cooling Coil Gross Rated COP {W/W}
    # ASHRAE 2007 Recommends:
    #2.81,                    !- Heat Pump Heating Coil Gross Rated COP {W/W}
    #2.7,                       !- Cooling Coil Gross Rated COP {W/W}
    temp_zone_pthp="""\n
  HVACTemplate:Zone:PTHP,
    ${zone_name},                !- Zone Name
    ${thermo_name},               !- Template Thermostat Name
    autosize,                !- Cooling Supply Air Flow Rate {m3/s}
    autosize,                !- Heating Supply Air Flow Rate {m3/s}
    ,                        !- No Load Supply Air Flow Rate {m3/s}
    ,                        !- Zone Heating Sizing Factor
    ,                        !- Zone Cooling Sizing Factor
    flow/person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    ,                        !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Outdoor Air Flow Rate per Zone {m3/s}
    ${sys_avail},                        !- System Availability Schedule Name
    ,                        !- Supply Fan Operating Mode Schedule Name
    DrawThrough,             !- Supply Fan Placement
    0.7,                     !- Supply Fan Total Efficiency
    75,                      !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    SingleSpeedDX,           !- Cooling Coil Type
    ${cool_avail},                        !- Cooling Coil Availability Schedule Name
    autosize,                !- Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- Cooling Coil Gross Rated Sensible Heat Ratio
    ${cool_COP},                       !- Cooling Coil Gross Rated COP {W/W}
    SingleSpeedDXHeatPump,   !- Heat Pump Heating Coil Type
    ${heat_avail},                        !- Heat Pump Heating Coil Availability Schedule Name
    autosize,                !- Heat Pump Heating Coil Gross Rated Capacity {W}
    ${heat_COP},                    !- Heat Pump Heating Coil Gross Rated COP {W/W}
    -8,                      !- Heat Pump Heating Minimum Outdoor Dry-Bulb Temperature {C}
    5,                       !- Heat Pump Defrost Maximum Outdoor Dry-Bulb Temperature {C}
    ReverseCycle,            !- Heat Pump Defrost Strategy
    Timed,                   !- Heat Pump Defrost Control
    0.058333,                !- Heat Pump Defrost Time Period Fraction
    Electric,                !- Supplemental Heating Coil Type
    ,                        !- Supplemental Heating Coil Availability Schedule Name
    autosize,                !- Supplemental Heating Coil Capacity {W}
    21,                      !- Supplemental Heating Coil Maximum Outdoor Dry-Bulb Temperature {C}
    0.8,                     !- Supplemental Gas Heating Coil Efficiency
    ,                        !- Supplemental Gas Heating Coil Parasitic Electric Load {W}
    ${doas_name},                        !- Dedicated Outdoor Air System Name
    SupplyAirTemperature,    !- Zone Cooling Design Supply Air Temperature Input Method
    14.0,                    !- Zone Cooling Design Supply Air Temperature {C}
    ,                        !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SupplyAirTemperature,    !- Zone Heating Design Supply Air Temperature Input Method
    50.0,                    !- Zone Heating Design Supply Air Temperature {C}
    ,                        !- Zone Heating Design Supply Air Temperature Difference {deltaC}
    ,                        !- Design Specification Outdoor Air Object Name
    ,                        !- Design Specification Zone Air Distribution Object Name
    ,                        !- Baseboard Heating Type
    ,                        !- Baseboard Heating Availability Schedule Name
    ;                        !- Baseboard Heating Capacity {W}
"""

    return Template(temp_zone_pthp), defaults


def HVACtemplate_HP_zone():

    defaults={
      'doas_name': "",
      'supp_heat': "Electric",
    }

    #Electric,                !- Supplemental Heating Coil Type
    #,                        !- Zone Heating Sizing Factor
    #2.5,                        !- Zone Heating Sizing Factor
    #,                        !- Zone Cooling Sizing Factor
    #
    #3.5,                     !- Cooling Coil Gross Rated COP {W/W}
    #4.2,                     !- Heat Pump Heating Coil Gross Rated COP {W/W}
    # Omega product Catalogue:
    #3.98,                     !- Cooling Coil Gross Rated COP {W/W}
    #4.54,                     !- Heat Pump Heating Coil Gross Rated COP {W/W}
    temp_zone_hp = """\n

  HVACTemplate:Zone:WaterToAirHeatPump,
    ${zone_name},                !- Zone Name
    ${thermo_name},              !- Template Thermostat Name
    autosize,                !- Cooling Supply Air Flow Rate {m3/s}
    autosize,                !- Heating Supply Air Flow Rate {m3/s}
    ,                        !- No Load Supply Air Flow Rate {m3/s}
    ,                        !- Zone Heating Sizing Factor
    ,                        !- Zone Cooling Sizing Factor
    Flow/Person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    ,                        !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Outdoor Air Flow Rate per Zone {m3/s}
    ,                        !- System Availability Schedule Name
    ,                        !- Supply Fan Operating Mode Schedule Name
    DrawThrough,             !- Supply Fan Placement
    0.7,                     !- Supply Fan Total Efficiency
    75,                      !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    Coil:Cooling:WaterToAirHeatPump:EquationFit,  !- Cooling Coil Type
    autosize,                !- Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- Cooling Coil Gross Rated Sensible Heat Ratio
    3.98,                     !- Cooling Coil Gross Rated COP {W/W}
    Coil:Heating:WaterToAirHeatPump:EquationFit,  !- Heat Pump Heating Coil Type
    autosize,                !- Heat Pump Heating Coil Gross Rated Capacity {W}
    4.54,                     !- Heat Pump Heating Coil Gross Rated COP {W/W}
    ,                        !- Supplemental Heating Coil Availability Schedule Name
    autosize,                !- Supplemental Heating Coil Capacity {W}
    2.5,                     !- Maximum Cycling Rate {cycles/hr}
    60,                      !- Heat Pump Time Constant {s}
    0.01,                    !- Fraction of On-Cycle Power Use
    60,                      !- Heat Pump Fan Delay Time {s}
    ${doas_name},                        !- Dedicated Outdoor Air System Name
    ${supp_heat},                !- Supplemental Heating Coil Type
    SupplyAirTemperature,    !- Zone Cooling Design Supply Air Temperature Input Method
    14.0,                    !- Zone Cooling Design Supply Air Temperature {C}
    ,                        !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SupplyAirTemperature,    !- Zone Heating Design Supply Air Temperature Input Method
    50.0,                    !- Zone Heating Design Supply Air Temperature {C}
    ,                        !- Zone Heating Design Supply Air Temperature Difference {deltaC}
    ,                        !- Heat Pump Coil Water Flow Mode
    ,                        !- Design Specification Outdoor Air Object Name
    ,                        !- Design Specification Zone Air Distribution Object Name
    ,                        !- Baseboard Heating Type
    ,                        !- Baseboard Heating Availability Schedule Name
    ;                        !- Baseboard Heating Capacity {W}

"""

    return Template(temp_zone_hp), defaults

def HVACtemplate_VRF_zone():


    defaults={
      'vrfsys_name': "VRF Sys 1 Water Source",
      'doas_name': "",
      'supp_heat': "Electric",
      'fanavail_sche': "FanAvailSchedVRF",
      'heat_oversize': "",
      'cool_oversize': "",
      'sys_avail': "",

    }

    # SB: Need oversizing factor or HL arent met in Jan-March
    #,                        !- Zone Heating Sizing Factor
    #3.25,                    !- Zone Heating Sizing Factor
    #1.5,                    !- Zone Heating Sizing Factor
    #All Zones2,              !- Template Thermostat Name
    #4.25,                    !- Zone Heating Sizing Factor
    temp_zone_vrf="""\n
  HVACTemplate:Zone:VRF,
    ${zone_name},                !- Zone Name
    ${vrfsys_name},  !- Template VRF System Name
    ${thermo_name},              !- Template Thermostat Name
    ${heat_oversize},                        !- Zone Heating Sizing Factor
    ${cool_oversize},                        !- Zone Cooling Sizing Factor
    1,                       !- Rated Total Heating Capacity Sizing Ratio {W/W}
    autosize,                !- Supply Air Flow Rate During Cooling Operation {m3/s}
    autosize,                !- Supply Air Flow Rate When No Cooling is Needed {m3/s}
    autosize,                !- Supply Air Flow Rate During Heating Operation {m3/s}
    autosize,                !- Supply Air Flow Rate When No Heating is Needed {m3/s}
    autosize,                !- Outdoor Air Flow Rate During Cooling Operation {m3/s}
    autosize,                !- Outdoor Air Flow Rate During Heating Operation {m3/s}
    autosize,                !- Outdoor Air Flow Rate When No Cooling or Heating is Needed {m3/s}
    Flow/Person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    ,                        !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Outdoor Air Flow Rate per Zone {m3/s}
    ,                        !- Design Specification Outdoor Air Object Name
    ,                        !- Design Specification Zone Air Distribution Object Name
    ${sys_avail},                        !- System Availability Schedule Name
    ${fanavail_sche},           !- Supply Fan Operating Mode Schedule Name
    BlowThrough,             !- Supply Air Fan placement
    0.7,                     !- Supply Fan Total Efficiency
    75,                      !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    VariableRefrigerantFlowDX,  !- Cooling Coil Type
    ,                        !- Cooling Coil Availability Schedule Name
    autosize,                !- Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- Cooling Coil Gross Rated Sensible Heat Ratio
    VariableRefrigerantFlowDX,  !- Heat Pump Heating Coil Type
    ,                        !- Heat Pump Heating Coil Availability Schedule Name
    autosize,                !- Heat Pump Heating Coil Gross Rated Capacity {W}
    ,                        !- Zone Terminal Unit On Parasitic Electric Energy Use {W}
    ,                        !- Zone Terminal Unit Off Parasitic Electric Energy Use {W}
    ${doas_name},                        !- Dedicated Outdoor Air System Name
    SupplyAirTemperature,    !- Zone Cooling Design Supply Air Temperature Input Method
    14,                      !- Zone Cooling Design Supply Air Temperature {C}
    11.11,                   !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SupplyAirTemperature,    !- Zone Heating Design Supply Air Temperature Input Method
    50,                      !- Zone Heating Design Supply Air Temperature {C}
    30,                      !- Zone Heating Design Supply Air Temperature Difference {deltaC}
    None,                    !- Baseboard Heating Type
    ,                        !- Baseboard Heating Availability Schedule Name
    autosize;                !- Baseboard Heating Capacity {W}
"""
#    Electric,                !- Baseboard Heating Type
#    None,                    !- Baseboard Heating Type

    return Template(temp_zone_vrf), defaults

def HVACtemplate_PTAC_zone():

    defaults={
      'doas_name': "",
      'supp_heat': "Electric",
      'fanavail_sche': "AlwaysPTAC",
    }

    temp_zone_ptac="""
  HVACTemplate:Zone:PTAC,
    ${zone_name},                !- Zone Name
    ${thermo_name},             !- Template Thermostat Name
    autosize,                !- Cooling Supply Air Flow Rate {m3/s}
    autosize,                !- Heating Supply Air Flow Rate {m3/s}
    ,                        !- No Load Supply Air Flow Rate {m3/s}
    ,                        !- Zone Heating Sizing Factor
    ,                        !- Zone Cooling Sizing Factor
    flow/person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    ,                        !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Outdoor Air Flow Rate per Zone {m3/s}
    ,                        !- System Availability Schedule Name
    ${fanavail_sche},                 !- Supply Fan Operating Mode Schedule Name
    DrawThrough,             !- Supply Fan Placement
    0.7,                     !- Supply Fan Total Efficiency
    75,                      !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    SingleSpeedDX,           !- Cooling Coil Type
    ,                        !- Cooling Coil Availability Schedule Name
    autosize,                !- Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- Cooling Coil Gross Rated Sensible Heat Ratio
    3,                       !- Cooling Coil Gross Rated Cooling COP {W/W}
    HotWater,                !- Heating Coil Type
    ,                        !- Heating Coil Availability Schedule Name
    autosize,                !- Heating Coil Capacity {W}
    0.8,                     !- Gas Heating Coil Efficiency
    ,                        !- Gas Heating Coil Parasitic Electric Load {W}
    ${doas_name},                        !- Dedicated Outdoor Air System Name
    SupplyAirTemperature,    !- Zone Cooling Design Supply Air Temperature Input Method
    14.0,                    !- Zone Cooling Design Supply Air Temperature {C}
    ,                        !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SupplyAirTemperature,    !- Zone Heating Design Supply Air Temperature Input Method
    50.0,                    !- Zone Heating Design Supply Air Temperature {C}
    ,                        !- Zone Heating Design Supply Air Temperature Difference {deltaC}
    ,                        !- Design Specification Outdoor Air Object Name
    ,                        !- Design Specification Zone Air Distribution Object Name
    ,                        !- Baseboard Heating Type
    ,                        !- Baseboard Heating Availability Schedule Name
    ;                        !- Baseboard Heating Capacity {W}
"""

    return Template(temp_zone_ptac), defaults

def HVACtemplate_Baseboard_zone():

    defaults={
      'doas_name': "",
      'type': "Electric",
      'sys_avail': "",
    }

    temp_zone_bboard="""
  HVACTemplate:Zone:BaseboardHeat,
    ${zone_name},                !- Zone Name
    ${thermo_name},              !- Template Thermostat Name
    ,                        !- Zone Heating Sizing Factor
    ${type},                !- Baseboard Heating Type
    ${sys_avail},                        !- Baseboard Heating Availability Schedule Name
    autosize,                !- Baseboard Heating Capacity {W}
    ${doas_name},                       !- Dedicated Outdoor Air System Name
    flow/person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    0.0,                     !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    0.0;                     !- Outdoor Air Flow Rate per Zone {m3/s}
"""

    return Template(temp_zone_bboard), defaults

def HVACtemplate_RTU_zone():

    defaults={
        'baseboard': 'None',
        #'baseboard': 'HotWater',
        'baseboard_availsche': '',
        'baseboard_size': 'autosize',
    }

    temp_zone_rtu="""
  HVACTemplate:Zone:Unitary,
    ${zone_name},                !- Zone Name
    ${rtu_name},          !- Template Unitary System Name
    ${thermo_name},               !- Template Thermostat Name
    autosize,                !- Supply Air Maximum Flow Rate {m3/s}
    ,                        !- Zone Heating Sizing Factor
    ,                        !- Zone Cooling Sizing Factor
    flow/person,             !- Outdoor Air Method
    0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    0.0,                     !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    0.0,                     !- Outdoor Air Flow Rate per Zone {m3/s}
    ,                        !- Supply Plenum Name
    ,                        !- Return Plenum Name
    ${baseboard},                    !- Baseboard Heating Type
    ${baseboard_availsche},                        !- Baseboard Heating Availability Schedule Name
    ${baseboard_size},                !- Baseboard Heating Capacity {W}
    SystemSupplyAirTemperature,  !- Zone Cooling Design Supply Air Temperature Input Method
    ,                        !- Zone Cooling Design Supply Air Temperature {C}
    ,                        !- Zone Cooling Design Supply Air Temperature Difference {deltaC}
    SystemSupplyAirTemperature,  !- Zone Heating Design Supply Air Temperature Input Method
    ,                        !- Zone Heating Design Supply Air Temperature {C}
    ;                        !- Zone Heating Design Supply Air Temperature Difference {deltaC}
"""

    return Template(temp_zone_rtu), defaults

def HVACtemplate_RTU_system():

    defaults={
      'fanavail_sche': 'FanAvailSchedRTU',
      'oa_sche': "Min OA Sched RTU",
      'avail_sche': 'AlwaysOnRTU',
    }

    temp_system_rtu="""
  HVACTemplate:System:Unitary,
    ${rtu_name},          !- Name
    ${avail_sche},                !- System Availability Schedule Name
    ${zone_name},                !- Control Zone or Thermostat Location Name
    autosize,                !- Supply Fan Maximum Flow Rate {m3/s}
    ${fanavail_sche},           !- Supply Fan Operating Mode Schedule Name
    0.7,                     !- Supply Fan Total Efficiency
    600,                     !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    1,                       !- Supply Fan Motor in Air Stream Fraction
    SingleSpeedDX,           !- Cooling Coil Type
    ,                        !- Cooling Coil Availability Schedule Name
    14.0,                    !- Cooling Design Supply Air Temperature {C}
    autosize,                !- Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- Cooling Coil Gross Rated Sensible Heat Ratio
    3,                       !- Cooling Coil Gross Rated COP {W/W}
    Gas,                     !- Heating Coil Type
    ,                        !- Heating Coil Availability Schedule Name
    50.0,                    !- Heating Design Supply Air Temperature {C}
    autosize,                !- Heating Coil Capacity {W}
    0.8,                     !- Gas Heating Coil Efficiency
    0.0,                     !- Gas Heating Coil Parasitic Electric Load {W}
    autosize,                !- Maximum Outdoor Air Flow Rate {m3/s}
    autosize,                !- Minimum Outdoor Air Flow Rate {m3/s}
    ${oa_sche},            !- Minimum Outdoor Air Schedule Name
    DifferentialDryBulb,     !- Economizer Type
    NoLockout,               !- Economizer Lockout
    19,                      !- Economizer Upper Temperature Limit {C}
    ,                        !- Economizer Lower Temperature Limit {C}
    ,                        !- Economizer Upper Enthalpy Limit {J/kg}
    ,                        !- Economizer Maximum Limit Dewpoint Temperature {C}
    ,                        !- Supply Plenum Name
    ,                        !- Return Plenum Name
    BlowThrough,             !- Supply Fan Placement
    StayOff,                 !- Night Cycle Control
    ,                        !- Night Cycle Control Zone Name
    None,                    !- Heat Recovery Type
    0.70,                    !- Sensible Heat Recovery Effectiveness
    0.65,                    !- Latent Heat Recovery Effectiveness
    None,                    !- Dehumidification Control Type
    ,                        !- Dehumidification Control Zone Name
    60.0,                    !- Dehumidification Setpoint {percent}
    None,                    !- Humidifier Type
    ,                        !- Humidifier Availability Schedule Name
    0.000001,                !- Humidifier Rated Capacity {m3/s}
    2690.0,                  !- Humidifier Rated Electric Power {W}
    ,                        !- Humidifier Control Zone Name
    30.0,                    !- Humidifier Setpoint {percent}
    ,                        !- Return Fan
    ,                        !- Return Fan Total Efficiency
    ,                        !- Return Fan Delta Pressure {Pa}
    ,                        !- Return Fan Motor Efficiency
    ;                        !- Return Fan Motor in Air Stream Fraction
"""

    return Template(temp_system_rtu), defaults

def HVACtemplate_VRF_system():

    defaults={
      'vrfsys_name': "VRF Sys 1 Water Source",
      'cond_type': "AirCooled",
      #'cond_type': "WaterCooled",
      'sys_avail': "",
      'heat_COP': "3.4",
      'cool_COP': "3.3",
      'sysheat_oversize': "1.0",

    }

#    No,                      !- Heat Pump Waste Heat Recovery
#    WaterCooled,             !- Condenser Type
    temp_sys_vrf="""\n
  HVACTemplate:System:VRF,
    ${vrfsys_name},  !- Name
    ${sys_avail},                        !- System Availability Schedule Name
    autosize,                !- Gross Rated Total Cooling Capacity {W}
    ${cool_COP},                     !- Gross Rated Cooling COP {W/W}
    -6,                      !- Minimum Outdoor Temperature in Cooling Mode {C}
    43,                      !- Maximum Outdoor Temperature in Cooling Mode {C}
    autosize,                !- Gross Rated Heating Capacity {W}
    ${sysheat_oversize},                       !- Rated Heating Capacity Sizing Ratio {W/W}
    ${heat_COP},                     !- Gross Rated Heating COP {W/W}
    -20,                     !- Minimum Outdoor Temperature in Heating Mode {C}
    30,                      !- Maximum Outdoor Temperature in Heating Mode {C}
    0.15,                    !- Minimum Heat Pump Part-Load Ratio {dimensionless}
    ,                        !- Zone Name for Master Thermostat Location
    LoadPriority,            !- Master Thermostat Priority Control Type
    ,                        !- Thermostat Priority Schedule Name
    Yes,                      !- Heat Pump Waste Heat Recovery
    30,                      !- Equivalent Piping Length used for Piping Correction Factor in Cooling Mode {m}
    10,                      !- Vertical Height used for Piping Correction Factor {m}
    30,                      !- Equivalent Piping Length used for Piping Correction Factor in Heating Mode {m}
    33,                      !- Crankcase Heater Power per Compressor {W}
    2,                       !- Number of Compressors {dimensionless}
    0.5,                     !- Ratio of Compressor Size to Total Compressor Capacity {W/W}
    5,                       !- Maximum Outdoor Dry-bulb Temperature for Crankcase Heater {C}
    Resistive,               !- Defrost Strategy
    Timed,                   !- Defrost Control
    0.058333,                !- Defrost Time Period Fraction {dimensionless}
    autosize,                !- Resistive Defrost Heater Capacity {W}
    5,                       !- Maximum Outdoor Dry-bulb Temperature for Defrost Operation {C}
    ${cond_type},             !- Condenser Type
    autosize,                !- Water Condenser Volume Flow Rate {m3/s}
    0.9,                     !- Evaporative Condenser Effectiveness {dimensionless}
    autosize,                !- Evaporative Condenser Air Flow Rate {m3/s}
    ,                        !- Evaporative Condenser Pump Rated Power Consumption {W}
    ,                        !- Basin Heater Capacity {W/K}
    2,                       !- Basin Heater Setpoint Temperature {C}
    ,                        !- Basin Heater Operating Schedule Name
    Electricity,             !- Fuel Type
    -15,                     !- Minimum Outdoor Temperature in Heat Recovery Mode {C}
    45;                      !- Maximum Outdoor Temperature in Heat Recovery Mode {C}
"""

    return Template(temp_sys_vrf), defaults

def HVACtemplate_DOAS_system():

    defaults={
      'name': "DOAS",
      'cool_coil': "ChilledWater",
      #'cool_coil': "HeatExchangerAssistedDX",
      'heat_coil': "HotWater",
      #'heat_coil': "Electric",
      'coil_avail_sche': "",
    }

    # NOTE: Requires an occupancy schedule
    ## NOTE: Not presently implemented in E+
    #VariableRefrigerantFlowDX,!- Cooling Coil Type
    #VariableRefrigerantFlowDX,!- Heating Coil Type
    temp_sys_DOAS="""\n
  HVACTemplate:System:DedicatedOutdoorAir,
    ${name},                    !- Name
    ${avail_sche},                !- System Availability Schedule Name
    DirectIntoZone,          !- Air Outlet Type
    autosize,                !- Supply Fan Flow Rate {m3/s}
    0.7,                     !- Supply Fan Total Efficiency
    1000,                    !- Supply Fan Delta Pressure {Pa}
    0.9,                     !- Supply Fan Motor Efficiency
    1,                       !- Supply Fan Motor in Air Stream Fraction
    DrawThrough,             !- Supply Fan Placement
    ${cool_coil},            !- Cooling Coil Type
    ${coil_avail_sche},                        !- Cooling Coil Availability Schedule Name
    FixedSetpoint,           !- Cooling Coil Setpoint Control Type
    12.8,                    !- Cooling Coil Design Setpoint {C}
    ,                        !- Cooling Coil Setpoint Schedule Name
    15.6,                    !- Cooling Coil Setpoint at Outdoor Dry-Bulb Low {C}
    15.6,                    !- Cooling Coil Reset Outdoor Dry-Bulb Low {C}
    12.8,                    !- Cooling Coil Setpoint at Outdoor Dry-Bulb High {C}
    23.3,                    !- Cooling Coil Reset Outdoor Dry-Bulb High {C}
    autosize,                !- DX Cooling Coil Gross Rated Total Capacity {W}
    autosize,                !- DX Cooling Coil Gross Rated Sensible Heat Ratio
    3,                       !- DX Cooling Coil Gross Rated COP {W/W}
    ${heat_coil},                !- Heating Coil Type
    ${coil_avail_sche},                        !- Heating Coil Availability Schedule Name
    FixedSetpoint,           !- Heating Coil Setpoint Control Type
    12.2,                    !- Heating Coil Design Setpoint {C}
    ,                        !- Heating Coil Setpoint Schedule Name
    15,                      !- Heating Coil Setpoint at Outdoor Dry-Bulb Low {C}
    7.8,                     !- Heating Coil Reset Outdoor Dry-Bulb Low {C}
    12.2,                    !- Heating Coil Setpoint at Outdoor Dry-Bulb High {C}
    12.2,                    !- Heating Coil Reset Outdoor Dry-Bulb High {C}
    0.8,                     !- Gas Heating Coil Efficiency
    ,                        !- Gas Heating Coil Parasitic Electric Load {W}
    Enthalpy,                !- Heat Recovery Type
    0.7,                     !- Heat Recovery Sensible Effectiveness
    0.65,                    !- Heat Recovery Latent Effectiveness
    Plate,                   !- Heat Recovery Heat Exchanger Type
    MinimumExhaustTemperature,  !- Heat Recovery Frost Control Type
    None,                    !- Dehumidification Control Type
    0.00924,                 !- Dehumidification Setpoint {kgWater/kgDryAir}
    None,                    !- Humidifier Type
    ,                        !- Humidifier Availability Schedule Name
    0.000001,                !- Humidifier Rated Capacity {m3/s}
    2690,                    !- Humidifier Rated Electric Power {W}
    0.003,                   !- Humidifier Constant Setpoint {kgWater/kgDryAir}
    ,                        !- Dehumidification Setpoint Schedule Name
    ;                        !- Humidifier Setpoint Schedule Name
"""

    return Template(temp_sys_DOAS), defaults

# Used with 'WaterHeater:Mixed',
def Plant_EquipmentList():

    defaults={
      'name': 'SWHSys1 Equipment List',
      'type': 'WaterHeater:Mixed',
      'eq_name': 'SWHSys1 Water Heater',
    }

    txt_planteqlst="""
  PlantEquipmentList,
    ${name},  !- Name
    ${type},       !- Equipment 1 Object Type
    ${eq_name};    !- Equipment 1 Name
"""

    return Template(txt_planteqlst), defaults

def Plant_EquipmentOperationList():

    defaults={
      'name':   'SWHSys1 Loop Operation Scheme List',
      'type':   'PlantEquipmentOperation:HeatingLoad',
      'scheme': 'SWHSys1 Operation Scheme',
      'sche':    'ALWAYS ON DHWNG',
    }

    txt_plantcntrl="""
  PlantEquipmentOperationSchemes,
    ${name},  !- Name
    ${type},  !- Control Scheme 1 Object Type
    ${scheme},!- Control Scheme 1 Name
    ${sche};               !- Control Scheme 1 Schedule Name
"""

    return Template(txt_plantcntrl), defaults

def Plant_EquipmentOperationHeating():

    defaults={
      'name':    'SWHSys1 Operation Scheme',
      'lower':   '0.0',
      'upper':  '1000000000000000',
      'list_nm': 'SWHSys1 Equipment List',
    }

    txt_load="""
  PlantEquipmentOperation:HeatingLoad,
    ${name},!- Name
    ${lower},                     !- Load Range 1 Lower Limit {W}
    ${upper},        !- Load Range 1 Upper Limit {W}
    ${list_nm};  !- Range 1 Equipment List Name
"""

    return Template(txt_load), defaults

def Plant_Sizing():

    defaults={
      'loop_name':'SWHSys1',
      'loop_type':'Heating',
      'temp':     '60',
      'deltaC':   '5.0',
    }

    txt_plantsz="""
  Sizing:Plant,
    ${loop_name},                 !- Plant or Condenser Loop Name
    ${loop_type},                 !- Loop Type
    ${temp},                      !- Design Loop Exit Temperature {C}
    ${deltaC};                     !- Loop Design Temperature Difference {deltaC}
"""

    return Template(txt_plantsz), defaults

def Plant_Loop():

    defaults={
      'loop_name': 'SWHSys1',
      'loop_type': 'Water',
      'supply_inlet': 'SWHSys1 Supply Inlet Node',
      'supply_outlet': 'SWHSys1 Supply Outlet Node',
      'supply_branch': 'SWHSys1 Supply Branches',
      'supply_connect': 'SWHSys1 Supply Connectors',
      'demand_inlet': 'SWHSys1 Demand Inlet Node',
      'demand_outlet': 'SWHSys1 Demand Outlet Node',
      'demand_branch': 'SWHSys1 Demand Branches',
      'demand_connect': 'SWHSys1 Demand Connectors',
      'scheme': 'SWHSys1 Loop Operation Scheme List',
      'outlet_node': 'SWHSys1 Supply Outlet Node',
    }

    txt_plantlp="""
  PlantLoop,
    ${loop_name},                 !- Name
    ${loop_type},                   !- Fluid Type
    ,                        !- User Defined Fluid Type
    ${scheme},  !- Plant Equipment Operation Scheme Name
    ${outlet_node},  !- Loop Temperature Setpoint Node Name
    60.0,                    !- Maximum Loop Temperature {C}
    10.0,                    !- Minimum Loop Temperature {C}
    AUTOSIZE,                !- Maximum Loop Flow Rate {m3/s}
    0.0,                     !- Minimum Loop Flow Rate {m3/s}
    AUTOSIZE,                !- Plant Loop Volume {m3}
    ${supply_inlet},  !- Plant Side Inlet Node Name
    ${supply_outlet},  !- Plant Side Outlet Node Name
    ${supply_branch}, !- Plant Side Branch List Name
    ${supply_connect},  !- Plant Side Connector List Name
    ${demand_inlet},  !- Demand Side Inlet Node Name
    ${demand_outlet},  !- Demand Side Outlet Node Name
    ${demand_branch}, !- Demand Side Branch List Name
    ${demand_connect},  !- Demand Side Connector List Name
    Optimal;                 !- Load Distribution Scheme
"""

    return Template(txt_plantlp), defaults

def Pump():

    defaults={
      'name': 'SWHSys1 Pump',
      'inlet_node': 'SWHSys1 Supply Inlet Node',
      'outlet_node': 'SWHSys1 Pump-SWHSys1 Water HeaterNodeviaConnector',
    }

    txt_pump="""
  Pump:ConstantSpeed,
    ${name},            !- Name
    ${inlet_node},  !- Inlet Node Name
    ${outlet_node},  !- Outlet Node Name
    AUTOSIZE,                !- Rated Flow Rate {m3/s}
    179352,                  !- Rated Pump Head {Pa}
    AUTOSIZE,                !- Rated Power Consumption {W}
    0.85,                    !- Motor Efficiency
    0.0,                     !- Fraction of Motor Inefficiencies to Fluid Stream
    Intermittent,            !- Pump Control Type
    ;                        !- Pump Flow Rate Schedule Name
"""

    return Template(txt_pump), defaults

def Branch():

    defaults={
      'contrl_type': 'Active',
      #'contrl_type': 'Bypass',
    }

    temp_branch="""
  Branch,
    ${name},  !- Name
    ,                        !- Maximum Flow Rate {m3/s}
    ,                        !- Pressure Drop Curve Name
    ${type},    !- Component 1 Object Type
    ${comp_nm},!- Component 1 Name
    ${inlet_node},  !- Component 1 Inlet Node Name
    ${outlet_node},  !- Component 1 Outlet Node Name
    ${contrl_type};                  !- Component 1 Branch Control Type
"""

    return Template(temp_branch), defaults


def HVAC_RoomAirModel():

    defaults={
      'type': 'UnderFloorAirDistributionExterior',
      #'type': 'ThreeNodeDisplacementVentilation',
    }

    temp_roomair="""
  RoomAirModelType,
    ${zone_name} RoomAir Model,  !- Name
    ${zone_name},                !- Zone Name
    ${type},  !- Room-Air Modeling Type
    DIRECT;                  !- Air Temperature Coupling Strategy
"""

    return Template(temp_roomair), defaults

def HVAC_UFAD_RoomAirSettings():

    defaults={
    }

#    LinearBarGrille,         !- Floor Diffuser Type
    temp_UFAD="""
  RoomAirSettings:UnderFloorAirDistributionInterior,
    ${zone_name},                !- Zone Name
    Autocalculate,           !- Number of Diffusers
    Autocalculate,           !- Power per Plume {W}
    Autocalculate,           !- Design Effective Area of Diffuser {m2}
    Autocalculate,           !- Diffuser Slot Angle from Vertical {deg}
    ,                        !- Thermostat Height {m}
    ,                        !- Comfort Height {m}
    0.001,                   !- Temperature Difference Threshold for Reporting {deltaC}
    Swirl,                   !- Floor Diffuser Type
    1.7,                     !- Transition Height {m}
    Autocalculate,           !- Coefficient A
    Autocalculate,           !- Coefficient B
    Autocalculate,           !- Coefficient C
    Autocalculate,           !- Coefficient D
    Autocalculate;           !- Coefficient E
"""

    return Template(temp_UFAD), defaults

def HVAC_DV_RoomAirSettings():

    defaults={
    }

    # TODO- Where is the 'Constant - .2' Schedule defined?
    temp_DV="""
  RoomAirSettings:ThreeNodeDisplacementVentilation,
    ${zone_name},                !- Zone Name
    Constant - .2,           !- Gain Distribution Schedule Name
    1,                       !- Number of Plumes per Occupant
    1.1,                     !- Thermostat Height {m}
    1.1,                     !- Comfort Height {m}
    0.3;                     !- Temperature Difference Threshold for Reporting {deltaC}
"""

    return Template(temp_DV), defaults

def HVAC_ZoneVentilation():

    defaults={
      'flow_rate': "1.0",
      'avail_sche': "VentSchedCont",
      'fan_pressure': "300", #Pa
      'method': "flow/zone",
    }

    temp_zone_exh="""
  ZoneVentilation:DesignFlowRate,
    ${name},        !- Name
    ${zone_name},              !- Zone or ZoneList Name
    ${avail_sche},               !- Schedule Name
    ${method},               !- Design Flow Rate Calculation Method
    ${flow_rate},                 !- Design Flow Rate {m3/s}
    ,                        !- Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Flow Rate per Person {m3/s-person}
    ,                        !- Air Changes per Hour {1/hr}
    Exhaust,                  !- Ventilation Type
    ${fan_pressure},                     !- Fan Pressure Rise {Pa}
    0.8,                     !- Fan Total Efficiency
    1,                       !- Constant Term Coefficient
    0,                       !- Temperature Term Coefficient
    0,                       !- Velocity Term Coefficient
    0,                       !- Velocity Squared Term Coefficient
    18.0,                    !- Minimum Indoor Temperature {C}
    ,                        !- Minimum Indoor Temperature Schedule Name
    ,                        !- Maximum Indoor Temperature {C}
    ,                        !- Maximum Indoor Temperature Schedule Name
    1.0;                     !- Delta Temperature {deltaC}
"""

    return Template(temp_zone_exh), defaults

def NaturalVentilation():

    defaults={
      'sche_name': "Night Free Cooling Schedule",
    }

    temp_zone_NV="""
    ZoneVentilation:DesignFlowRate,
    ${zone_name} Free Cooling,         !- Name
    ${zone_name},                      !- Zone Name
    ${sche_name},   !- Schedule Name
    AirChanges/Hour,         !- Design Flow Rate Calculation Method
    ,                        !- Design Flow Rate {m3/s}
    ,                        !- Flow Rate per Zone Floor Area {m3/s-m2}
    ,                        !- Flow Rate per Person {m3/s-person}
    5.0,                       !- Air Changes per Hour
    Intake,                  !- Ventilation Type
    ,                        !- Fan Pressure Rise {Pa}
    1.0,                     !- Fan Total Efficiency
    0.6060000,               !- Constant Term Coefficient
    0.03636,                 !- Temperature Term Coefficient
    0.1177,                  !- Velocity Term Coefficient
    0.0,                     !- Velocity Squared Term Coefficient
    25,                      !- Minimum Indoor Temperature {C}
    ,                        !- Minimum Indoor Temperature Schedule Name
    100,                      !- Maximum Indoor Temperature {C}
    ,                        !- Maximum Indoor Temperature Schedule Name
    2,                       !- Delta Temperature {deltaC}
    ,                        !- Delta Temperature Schedule Name
    10,                      !- Minimum Outdoor Temperature {C}
    ,                        !- Minimum Outdoor Temperature Schedule Name
    23,                      !- Maximum Outdoor Temperature {C}
    ,                        !- Maximum Outdoor Temperature Schedule Name
    40;                      !- Maximum Wind Speed {m/s}
"""

    return Template(temp_zone_NV), defaults

def ZoneMixing():

    defaults={
      'sche_name': "Night Free Cooling Schedule",
    }

    # Setting up Zone mixing objects:
    # Zones that require mixing:
    # SQL: SELECT ZoneName,IsPartOfTotalArea from Zones WHERE ExtGrossWallArea<7;
    # Zones with good NV potential
    # SQL: SELECT ZoneName, OriginX, OriginY, OriginZ from Zones WHERE ExtGrossWallArea>15;
    # Get all nearby zones (within effective NV distance (x or y) with poor NV characteristics OR with any NV utilization
    # Zones to iterate over and add ZoneMixing objects
    #   ALWAYS ON,               !- Schedule Name
    #   Flow/Zone,               !- Design Flow Rate Calculation Method
    #   %0.2f,                   !- Design Flow Rate {m3/s}
    ZM_temp="""
   ZoneMixing,
       ${zoneA} to ${zoneB},                !- Name
       ${zoneB},                      !- Sink Zone Name
       ${sche_name}, !- Schedule Name
       AirChanges/Hour,         !- Design Flow Rate Calculation Method
       ,                        !- Design Flow Rate {m3/s}
       ,                        !- Flow Rate per Zone Floor Area {m3/s-m2}
       ,                        !- Flow Rate per Person {m3/s-person}
       3,                       !- Air Changes per Hour
       ${zoneA},                      !- Source Zone Name
       0;                       !- Delta Temperature {deltaC}
"""

    return Template(ZM_temp), defaults

def Simulation_HeatBalanceCFD():

    defaults={
    }

   # Other types: CrankNicholsonSecondOrder
    temp_FD_opt="""
  HeatBalanceSettings:ConductionFiniteDifference,
    FullyImplicitFirstOrder, !- Difference Scheme
    3.0,                     !- Space Discretization Constant
    1.0,                     !- Relaxation Factor
    0.002;                   !- Inside Face Surface Temperature Convergence Criteria
"""

    return Template(temp_FD_opt), defaults

def Material_PCMSurfaceProperty():

    defaults={
      'surf_type': "AllInteriorWalls",
    }

    temp_PCM_surf="""
  SurfaceProperty:HeatTransferAlgorithm:MultipleSurface,
    PCM Surfaces ${surf_num},             !- Name
    ${surf_type},         !- Surface Type
    ConductionFiniteDifference; !- Algorithm
"""

    return Template(temp_PCM_surf), defaults


def Material_InteriorFinish():

    defaults={
      'name': "InteriorFurnishings",
      'mat_name': "Std Wood 6inch",
    }

    temp_const="""
  Construction,
    ${name},     !- Name
    ${mat_name};          !- Outside Layer

  Material,
    ${mat_name},          !- Name
    MediumSmooth,            !- Roughness
    0.15,                    !- Thickness {m}
    0.12,                    !- Conductivity {W/m-K}
    540.0000,                !- Density {kg/m3}
    1210,                    !- Specific Heat {J/kg-K}
    0.9000000,               !- Thermal Absorptance
    0.7000000,               !- Solar Absorptance
    0.7000000;               !- Visible Absorptance
"""

    return Template(temp_const), defaults

def Material_WindowShade():

    defaults={
      'name': "Shade",
    }

    temp_shade="""\n
  WindowMaterial:Shade,
      ${name},                     !- Name
      0.00,                      !- Solar Transmittance
      0.80,                      !- Solar Reflectance
      0.00,                      !- Visible Transmittance
      0.80,                      !- Visible Reflectance
      0.9,                       !- Thermal Hemispherical Emissivity
      0.05,                      !- Thermal Transmittance
      0.01,                      !- Thickness {m}
      0.300,                     !- Conductivity {W/m-K}
      0.05,                      !- Shade to Glass Distance {m}
      0.0,                       !- Top Opening Multiplier
      0.0,                       !- Bottom Opening Multiplier
      0.0,                       !- Left-Side Opening Multiplier
      0.0,                       !- Right-Side Opening Multiplier
      0.2;                       !- Airflow Permeability
"""

    return Template(temp_shade), defaults

def ShadingSiteObstruction():

    defaults={
      'name': "Shade",
      'x11': "0.0", 'x12': "0.0", 'x13': "0.0",
      'x21': "0.0", 'x22': "0.0", 'x23': "0.0",
      'x31': "0.0", 'x32': "0.0", 'x33': "0.0",
      'x41': "0.0", 'x42': "0.0", 'x43': "0.0",
    }

    temp_shade_obstr="""
  Shading:Site:Detailed,
    ${name},     !- Name
    ,                      !- Transmittance Schedule Name
    4,                     !- Number of Vertices
    ${x11},${x12},${x13},  !- X,Y,Z ==> Vertex 1 {m}
    ${x21},${x22},${x23},  !- X,Y,Z ==> Vertex 2 {m}
    ${x31},${x32},${x33},  !- X,Y,Z ==> Vertex 3 {m}
    ${x41},${x42},${x43};  !- X,Y,Z ==> Vertex 4 {m}
"""

    return Template(temp_shade_obstr), defaults

def ShadingBallastPV():

    defaults={
      'azi':    "0.0",
      'length': "0.0",
      'height': "0.0",
      'tilt': "45.0",
      'x': "0.0", 'y': "0.0", 'z': "0.0",
    }

    temp_PV_shade="""
  Shading:Building,
    Row ${row_num} Ballast,           !- Name
    ${azi},                       !- Azimuth Angle {deg}
    ${tilt},                      !- Tilt Angle {deg}
    ${x},                       !- Starting X Coordinate {m}
    ${y},                       !- Starting Y Coordinate {m}
    ${z},                       !- Starting Z Coordinate {m}
    ${length},                       !- Length {m}
    ${height};                       !- Height {m}
"""

    return Template(temp_PV_shade), defaults

def ShadingZoneDetailed():

    defaults={
      'name': "Shade",
    }

    temp_extshd="""
  Shading:Zone:Detailed,
    ${name} Overhang,     !- Name
    ${surf_name},                 !- Base Surface Name
    ,               !- Transmittance Schedule Name
    ${vert},              !- Number of Vertices
"""

    return Template(temp_extshd), defaults

def WindowControl():

    defaults={
      'name': "Shade",
      #'type': "InteriorShade",
      'type': "ExteriorShade",
      'max_temp': "25",
      'max_SR': "400",
    }

    #OnIfHighSolarOnWindow,!- Shading Control Type
    # SB: Order is significant in this object. Temperature and then SR
    temp_shcntl="""\n
  WindowProperty:ShadingControl,
    ${name},         !- Name
    ${type},           !- Shading Type
    ${constr_name},       !- Construction with Shading Name
    OnIfHighOutdoorAirTempAndHighSolarOnWindow,!- Shading Control Type
    ,                        !- Schedule Name
    ${max_temp},                   !- Setpoint {W/m2, W or deg C}
    No,                      !- Shading Control Is Scheduled
    No,                      !- Glare Control Is Active
    ,                        !- Shading Device Material Name
    ,                        !- Type of Slat Angle Control for Blinds
    ,                        !- Slat Angle Schedule Name
    ${max_SR};                   !- Setpoint 2 {W/m2 or deg C}
"""

    return Template(temp_shcntl), defaults

def DaylightControl():

    defaults={
      'glare_azi': "0",
    }

    temp_daylight="""
  Daylighting:Controls,
    ${zone_name},        !- Zone Name
    1,                       !- Total Daylighting Reference Points
    ${x},                  !- X-Coordinate of First Reference Point {m}
    ${y},                   !- Y-Coordinate of First Reference Point {m}
    ${z},                   !- Z-Coordinate of First Reference Point {m}
    0.000,                   !- X-Coordinate of Second Reference Point {m}
    0.000,                   !- Y-Coordinate of Second Reference Point {m}
    0.000,                   !- Z-Coordinate of Second Reference Point {m}
    1.0000,                  !- Fraction of Zone Controlled by First Reference Point
    0.0000,                  !- Fraction of Zone Controlled by Second Reference Point
    400.0000,                !- Illuminance Setpoint at First Reference Point {lux}
    400.0000,                !- Illuminance Setpoint at Second Reference Point {lux}
    2,                       !- Lighting Control Type
    ${glare_azi},                     !- Glare Calculation Azimuth Angle of View Direction Clockwise from Zone y-Axis {deg}
    20,                      !- Maximum Allowable Discomfort Glare Index
    0.3000,                  !- Minimum Input Power Fraction for Continuous Dimming Control
    0.2000,                  !- Minimum Light Output Fraction for Continuous Dimming Control
    3,                       !- Number of Stepped Control Steps
    1.0000;                  !- Probability Lighting will be Reset When Needed in Manual Stepped Control
"""

    return Template(temp_daylight), defaults

def Material_InternalMass():

    defaults={
      'const_name': "InteriorFurnishings",
      'suffix': "",
    }

    temp_intmass="""
  InternalMass,
    ${zone_name} Internal Mass${suffix},  !- Name
    ${const_name},     !- Construction Name
    ${zone_name},                !- Zone Name
    ${surf_area};               !- Surface Area {m2}

"""

    return Template(temp_intmass), defaults

def Schedule_DHWLoad():

    defaults={
      'frac': "1.0",
    }

    sche_dhw="""
  Schedule:Compact,
    APT_DHW_SCH FRAC ${frac},             !- Name
    Fraction,                !- Schedule Type Limits Name
    THROUGH: 12/31,          !- Field 1
    FOR: AllDays,            !- Field 2
    UNTIL: 1:00,0.08,        !- Field 3
    UNTIL: 2:00,0.04,        !- Field 5
    UNTIL: 3:00,0.01,        !- Field 7
    UNTIL: 4:00,0.01,        !- Field 9
    UNTIL: 5:00,0.04,        !- Field 11
    UNTIL: 6:00,0.27,        !- Field 13
    UNTIL: 7:00,0.94,        !- Field 15
    UNTIL: 8:00,1.00,        !- Field 17
    UNTIL: 9:00,0.96,        !- Field 19
    UNTIL: 10:00,0.84,       !- Field 21
    UNTIL: 11:00,0.76,       !- Field 23
    UNTIL: 12:00,0.61,       !- Field 25
    UNTIL: 13:00,0.53,       !- Field 27
    UNTIL: 14:00,0.47,       !- Field 29
    UNTIL: 15:00,0.41,       !- Field 31
    UNTIL: 16:00,0.47,       !- Field 33
    UNTIL: 17:00,0.55,       !- Field 35
    UNTIL: 18:00,0.73,       !- Field 37
    UNTIL: 19:00,0.86,       !- Field 39
    UNTIL: 20:00,0.82,       !- Field 41
    UNTIL: 21:00,0.75,       !- Field 43
    UNTIL: 22:00,0.61,       !- Field 45
    UNTIL: 23:00,0.53,       !- Field 47
    UNTIL: 24:00,0.29;       !- Field 49
"""

    return Template(sche_dhw), defaults

def Schedule_WaterUse():

    defaults={
      'peak_flow': "100.0",
      'frac': "1.0",
      'water_sche': "Apartment Water Equipment Temp Sched",
      'supply_sche': "Apartment Water Equipment Hot Supply Temp Sched",
      'lat_sche': "Apartment Water Equipment Latent fract sched",
      'sens_sche': "Apartment Water Equipment Sensible fract sched",
    }

#!    6.198e-006,               !- Peak Flow Rate {m3/s}
#!    3.66e-006,               !- Peak Flow Rate {m3/s}
# SB NOTE: End-Use Subcategory creates an 'Output:Meter' object
#    ,                        !- End-Use Subcategory
#    DHW,                    !- End-Use Subcategory
    #DHW Eq %s Frac %.1f,  !- Name
    temp_dhw_zone="""
  WaterUse:Equipment,
    DHW Eq ${zone_name},  !- Name
    DHW,                        !- End-Use Subcategory
    ${peak_flow},               !- Peak Flow Rate {m3/s}
    APT_DHW_SCH FRAC ${frac},             !- Flow Rate Fraction Schedule Name
    ${water_sche},  !- Target Temperature Schedule Name
    ${supply_sche},  !- Hot Water Supply Temperature Schedule Name
    ,                        !- Cold Water Supply Temperature Schedule Name
    ${zone_name},          !- Zone Name
    ${sens_sche},  !- Sensible Fraction Schedule Name
    ${lat_sche};  !- Latent Fraction Schedule Name
"""

    return Template(temp_dhw_zone), defaults

def Schedule_Elevators():

    defaults={
      'sche_name': "BLDG_ELEVATORS",
    }

    temp_sch_elev="""
  Schedule:Compact,
    ${sche_name},          !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: AllDays,            !- Field 2
    Until: 04:00,0.05,       !- Field 3
    Until: 05:00,0.10,       !- Field 5
    Until: 06:00,0.20,       !- Field 7
    Until: 07:00,0.40,       !- Field 9
    Until: 09:00,0.50,       !- Field 11
    Until: 10:00,0.35,       !- Field 13
    Until: 16:00,0.15,       !- Field 15
    Until: 17:00,0.35,       !- Field 17
    Until: 19:00,0.50,       !- Field 19
    Until: 21:00,0.40,       !- Field 21
    Until: 22:00,0.30,       !- Field 23
    Until: 23:00,0.20,       !- Field 25
    Until: 24:00,0.10;       !- Field 27
"""

    return Template(temp_sch_elev), defaults

def Schedule_NV():

    defaults={
      'sche_name': "Night Free Cooling Schedule",
    }

    temp_sch_NV="""
  Schedule:Compact,
    ${sche_name},          !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 4/15,           !- Field 1
    For: Alldays,            !- Field 2
    Until: 24:00,0.00,       !- Field 3
    Through: 10/1,           !- Field 5
    For: WeekDays Sunday, !- Field 6
    Until: 5:00,1.00,        !- Field 7
    Until: 22:00,0.00,        !- Field 9
    Until: 24:00,1.00,       !- Field 11
    For: Saturday Holidays SummerDesignDay WinterDesignDay CustomDay1 CustomDay2, !- Field 13
    Until: 24:00,0.00,       !- Field 14
    Through: 12/31,          !- Field 16
    For: Alldays,            !- Field 17
    Until: 24:00,0.00;       !- Field 18
"""

    return Template(temp_sch_NV), defaults

def Equipment_InteriorElevators():

    defaults={
      'sche_name': "BLDG_ELEVATORS",
    }

    # NOTE- Implementation based on: RefBldgSmallHotelNew2004_Chicago.idf
    #  * Equipment gains are only associated with one zone in this model
    temp_elev_eq="""
  ElectricEquipment,
    ${elev_name},  !- Name
    ${zone_name},        !- Zone or ZoneList Name
    ${sche_name},          !- Schedule Name
    EquipmentLevel,          !- Design Level Calculation Method
    ${power},        !- Design Level {W}
    ,                        !- Watts per Zone Floor Area {W/m2}
    ,                        !- Watts per Person {W/person}
    0.0000,                  !- Fraction Latent
    0.5000,                  !- Fraction Radiant
    0.0000,                  !- Fraction Lost
    Elevators;               !- End-Use Subcategory
"""

    return Template(temp_elev_eq), defaults

def Equipment_ExteriorElevators():

    defaults={
      'elev_name': "Elevators",
      'sche_name': "BLDG_ELEVATORS",
    }

    # NOTE- Implementation based on: RefBldgSmallHotelNew2004_Chicago.idf
    #  * Equipment gains are only associated with one zone in this model
    temp_elev_eq="""
  Exterior:FuelEquipment,
    ${elev_name},               !- Name
    Electricity,             !- Fuel Use Type
    ${sche_name},          !- Schedule Name
    ${power},        !- Design Level {W}
    Elevators;               !- End-Use Subcategory
"""

    return Template(temp_elev_eq), defaults

def Equipment_ParkFans():

    defaults={
      'name': "Parking Garage Fans",
      'sche_name': "PARKFAN_ALWAYS_ON",
    }

    #1000,                    !- Design Level {W}
    temp_park_fan="""
  Exterior:FuelEquipment,
    ${name},     !- Name
    Electricity,             !- Fuel Use Type
    ${sche_name},           !- Schedule Name
    ${power},                    !- Design Level {W}
    Parking Garage Ventilation;  !- End-Use Subcategory
"""

    return Template(temp_park_fan), defaults

def Equipment_Baseload():

    defaults={
        'enduse': "ElectricEquipment",
        'load': "2.15278",
        'suffix': "",
        'frac_lost':"",
    }

    temp_bload_eq="""
  ElectricEquipment,
    Baseload ${zone_name}${suffix}, !- Name
    ${zone_name}, !- Zone or ZoneList Name
    ${avail_sche},                        !- Schedule Name
    Watts/Area,                             !- Design Level Calculation Method
    ,                                       !- Design Level {W}
    ${load},                                !- Watts per Zone Floor Area {W/m2}
    ,                                       !- Watts per Person {W/person}
    ,                                       !- Fraction Latent
    ,                                       !- Fraction Radiant
    ${frac_lost},                                !- Fraction Lost
    ${enduse};                      !- End-Use Subcategory
"""

    return Template(temp_bload_eq), defaults


def Equipment_ExteriorLighting():

    defaults={
      'name': "Exterior Facade Lighting",
      'avail_name': "EXTLIGHT_ALWAYS_ON",
      'control_opt': "AstronomicalClock",
      'category': "Exterior Facade Lighting",
      'power': "100.0",
    }

    temp_extlight="""
  Exterior:Lights,
    ${name},!- Name
    ${avail_name},               !- Schedule Name
    ${power},                   !- Design Level {W}
    ${control_opt},       !- Control Option
    ${category};!- End-Use Subcategory
"""

    return Template(temp_extlight), defaults

def Equipment_InteriorLighting():

    defaults={
      'avail_name': "ScheduleParkingCont",
      'watt_per_area': "2.0",
    }

    # ASHRAE 90.1: 0.2 W/ft2 OR 2.1527821 W/m2
    temp_lights="""
  Lights,
    ${name}, !- Name
    ${zone_name},    !- Zone or ZoneList Name
    ${avail_name},                    !- Schedule Name
    Watts/Area,                             !- Design Level Calculation Method
    ,                                       !- Lighting Level {W}
    ${watt_per_area},                       !- Watts per Zone Floor Area {W/m2}
    ,                                       !- Watts per Person {W/person}
    ,                                       !- Return Air Fraction
    ,                                       !- Fraction Radiant
    ;                                       !- Fraction Visible
"""

    return Template(temp_lights), defaults

def Equipment_PVGenerator():

    defaults={
      'watt_per_area': "2.0",
      'pv_type': "PhotovoltaicPerformance:Simple",
      'pv_name': "16percentEffPV0.8Area2",
      'mode': "Decoupled",
    }

    temp_PVgen="""\n
  Generator:Photovoltaic,
    ${name},!- Name
    ${surf_name},    !- Surface Name
    ${pv_type},  !- Photovoltaic Performance Object Type
    ${pv_name},   !- Module Performance Name
    ${mode},               !- Heat Transfer Integration Mode
    1.0,                     !- Number of Series Strings in Parallel {dimensionless}
    1.0;                     !- Number of Modules in Series {dimensionless}
"""

    return Template(temp_PVgen), defaults

def Equipment_PV():

    defaults={
      'frac': "0.8",
      'pv_eff': "0.16",
    }

    # SB NOTE: This object can also refer to an efficiency schedule
    #  * Change 'Fixed' to 'Scheduled', add in 'PVefficiency; !- Efficiency Schedule Name'
    #0.8,                  !- Fraction of Surface Area with Active Solar Cells {dimensionless}
    #1.0,                  !- Fraction of Surface Area with Active Solar Cells {dimensionless}
    temp_PV="""\n
  PhotovoltaicPerformance:Simple,
    ${name},!- Name
    ${frac},                  !- Fraction of Surface Area with Active Solar Cells {dimensionless}
    Fixed,                !- Conversion Efficiency Input Mode
    ${pv_eff};                 !- Value for Cell Efficiency if Fixed
"""

    return Template(temp_PV), defaults

def Equipment_PVonediode():

    defaults={
    }

    # One-Diode PV Model
    # SB TODO: Update PV parameters here
    temp_OD_PV="""
  PhotovoltaicPerformance:EquivalentOne-Diode,
    ${name}, !- Name
    CrystallineSilicon,      !- Cell type
    36,                      !- Number of Cells in Series {dimensionless}
    0.63,                    !- Active Area {m2}
    0.9,                     !- Transmittance Absorptance Product {dimensionless}
    1.12,                    !- Semiconductor Bandgap {eV}
    1000000,                 !- Shunt Resistance {ohms}
    4.75,                    !- Short Circuit Current {A}
    21.4,                    !- Open Circuit Voltage {V}
    25.0,                    !- Reference Temperature {C}
    1000.0,                  !- Reference Insolation {W/m2}
    4.45,                    !- Module Current at Maximum Power {A}
    17,                      !- Module Voltage at Maximum Power {V}
    0.00065,                 !- Temperature Coefficient of Short Circuit Current {A/K}
    -0.08,                   !- Temperature Coefficient of Open Circuit Voltage {V/K}
    20,                      !- Nominal Operating Cell Temperature Test Ambient Temperature {C}
    47,                      !- Nominal Operating Cell Temperature Test Cell Temperature {C}
    800.0,                   !- Nominal Operating Cell Temperature Test Insolation {W/m2}
    30.0,                    !- Module Heat Loss Coefficient {W/m2-K}
    50000;                   !- Total Heat Capacity {J/m2-K}
"""

    return Template(temp_OD_PV), defaults

def Equipment_PVsandia():

    defaults={
    }

    # Sandia model
    # SB TODO: Update PV parameters here
    temp_Sandia_PV="""
  PhotovoltaicPerformance:Sandia,
    ${name},          !- Name
    0.63,                    !- Active Area {m2}
    36,                      !- Number of Cells in Series {dimensionless}
    1,                       !- Number of Cells in Parallel {dimensionless}
    4.75,                    !- Short Circuit Current {A}
    21.4,                    !- Open Circuit Voltage {V}
    4.45,                    !- Current at Maximum Power Point {A}
    17,                      !- Voltage at Maximum Power Point {V}
    0.0004,                  !- Sandia Database Parameter aIsc {1/K}
    -0.0005,                 !- Sandia Database Parameter aImp {1/K}
    0.991,                   !- Sandia Database Parameter c0 {dimensionless}
    0.009,                   !- Sandia Database Parameter c1 {dimensionless}
    -0.085,                  !- Sandia Database Parameter BVoc0 {V/K}
    0.0,                     !- Sandia Database Parameter mBVoc {V/K}
    -0.085,                  !- Sandia Database Parameter BVmp0 {V/K}
    0,                       !- Sandia Database Parameter mBVmp {V/K}
    1.38,                    !- Diode Factor {dimensionless}
    0.091575,                !- Sandia Database Parameter c2 {dimensionless}
    -8.79359,                !- Sandia Database Parameter c3 {dimensionless}
    0.9408,                  !- Sandia Database Parameter a0 {dimensionless}
    0.054204,                !- Sandia Database Parameter a1 {dimensionless}
    -0.011043,               !- Sandia Database Parameter a2 {dimensionless}
    -0.0008075,              !- Sandia Database Parameter a3 {dimensionless}
    -0.00002097,             !- Sandia Database Parameter a4 {dimensionless}
    1,                       !- Sandia Database Parameter b0 {dimensionless}
    -0.002438,               !- Sandia Database Parameter b1 {dimensionless}
    0.0003103,               !- Sandia Database Parameter b2 {dimensionless}
    -0.00001246,             !- Sandia Database Parameter b3 {dimensionless}
    2.112E-07,               !- Sandia Database Parameter b4 {dimensionless}
    -1.359E-09,              !- Sandia Database Parameter b5 {dimensionless}
    3,                       !- Sandia Database Parameter Delta(Tc) {deltaC}
    1,                       !- Sandia Database Parameter fd {dimensionless}
    -3.56,                   !- Sandia Database Parameter a {dimensionless}
    -0.075,                  !- Sandia Database Parameter b {dimensionless}
    0.993,                   !- Sandia Database Parameter c4 {dimensionless}
    0.007,                   !- Sandia Database Parameter c5 {dimensionless}
    4.7,                     !- Sandia Database Parameter Ix0
    3.22,                    !- Sandia Database Parameter Ixx0
    1.105,                   !- Sandia Database Parameter c6
    -0.105;                  !- Sandia Database Parameter c7
"""

    return Template(temp_Sandia_PV), defaults

def Equipment_PVInverter():

    defaults={
      'avail_sche': "ALWAYS ON PV",
      'inv_eff': "0.90",
    }

    temp_PVinv="""\n
  ElectricLoadCenter:Inverter:Simple,
    ${name},   !- Name
    ${avail_sche},            !- Availability Schedule Name
    ,                        !- Zone Name
    0.0,                     !- Radiative Fraction
    ${inv_eff};                     !- Inverter Efficiency
"""

    return Template(temp_PVinv), defaults

def Equipment_LoadCenterGenerators():

    defaults={
      'gen_type': "Generator:Photovoltaic",
      'pk_power': "200000",
      'avail_sche': "ALWAYS ON PV",
    }

    temp_gen="""\n
  ElectricLoadCenter:Generators,
    ${name},                 !- Name
    ${gen_name},    !- Generator Name
    ${gen_type},  !- Generator Object Type
    ${pk_power},                  !- Generator Rated Electric Power Output {W}
    ${avail_sche},            !- Generator Availability Schedule Name
    ;                        !- Generator Rated Thermal to Electrical Power Ratio
"""

    return Template(temp_gen), defaults

def Equipment_LoadCenterGeneratorsParts():

    defaults={
      'gen_type': "Generator:Photovoltaic",
      'avail_sche': "ALWAYS ON PV",
    }

    temp_genlist="""
    PV ${name},    !- Generator ${iter} Name
    Generator:Photovoltaic,  !- Generator ${iter} Object Type
    200000,                  !- Generator ${iter} Rated Electric Power Output {W}
    ALWAYS ON PV ${azi},         !- Generator ${iter} Availability Schedule Name
    ,                        !- Generator ${iter} Rated Thermal to Electrical Power Ratio"""

    return Template(temp_genlist), defaults



def Equipment_LoadCenterDistribution():

    defaults={
      'bus_type': "DirectCurrentWithInverter",
    }

    temp_dist="""\n
  ElectricLoadCenter:Distribution,
    ${name},  !- Name
    ${gen_name},                 !- Generator List Name
    Baseload,                !- Generator Operation Scheme Type
    0,                       !- Demand Limit Scheme Purchased Electric Demand Limit {W}
    ,                        !- Track Schedule Name Scheme Schedule Name
    ,                        !- Track Meter Scheme Meter Name
    ${bus_type},  !- Electrical Buss Type
    ${inv_name};   !- Inverter Object Name
"""

    return Template(temp_dist), defaults

def add_ngas_PEF():

    defaults={
      'source_PEF': 1.0,
    }

    # WAS: 1.092
    # DEFAULT: 1.092
    #$37631000,                !- Energy per Unit Factor
    # kWh2m3 conversion?: NOTE: 37631000/3,600,000 = 10.45
    temp_ngas_PEF="""
  FuelFactors,
    NaturalGas,              !- Existing Fuel Resource Name
    m3,                      !- Units of Measure
    ,                        !- Energy per Unit Factor
    ${source_PEF},                   !- Source Energy Factor {J/J}
    ,                        !- Source Energy Schedule Name
    5.21E+01,                !- CO2 Emission Factor {g/MJ}
    ,                        !- CO2 Emission Factor Schedule Name
    3.99E-02,                !- CO Emission Factor {g/MJ}
    ,                        !- CO Emission Factor Schedule Name
    1.06E-03,                !- CH4 Emission Factor {g/MJ}
    ,                        !- CH4 Emission Factor Schedule Name
    4.73E-02,                !- NOx Emission Factor {g/MJ}
    ,                        !- NOx Emission Factor Schedule Name
    1.06E-03,                !- N2O Emission Factor {g/MJ}
    ,                        !- N2O Emission Factor Schedule Name
    2.68E-04,                !- SO2 Emission Factor {g/MJ}
    ,                        !- SO2 Emission Factor Schedule Name
    0.0,                     !- PM Emission Factor {g/MJ}
    ,                        !- PM Emission Factor Schedule Name
    3.59E-03,                !- PM10 Emission Factor {g/MJ}
    ,                        !- PM10 Emission Factor Schedule Name
    0.0,                     !- PM2.5 Emission Factor {g/MJ}
    ,                        !- PM2.5 Emission Factor Schedule Name
    0,                       !- NH3 Emission Factor {g/MJ}
    ,                        !- NH3 Emission Factor Schedule Name
    2.61E-03,                !- NMVOC Emission Factor {g/MJ}
    ,                        !- NMVOC Emission Factor Schedule Name
    1.11E-07,                !- Hg Emission Factor {g/MJ}
    ,                        !- Hg Emission Factor Schedule Name
    2.13E-07,                !- Pb Emission Factor {g/MJ}
    ,                        !- Pb Emission Factor Schedule Name
    0,                       !- Water Emission Factor {L/MJ}
    ,                        !- Water Emission Factor Schedule Name
    0,                       !- Nuclear High Level Emission Factor {g/MJ}
    ,                        !- Nuclear High Level Emission Factor Schedule Name
    0;                       !- Nuclear Low Level Emission Factor {m3/MJ}

"""

    return Template(temp_ngas_PEF), defaults

def add_elec_PEF():

    defaults={
      'source_PEF': 1.0,
    }

    #3.546,                   !- Source Energy Factor {J/J}
    temp_elec_PEF="""
  FuelFactors,
    Electricity,             !- Existing Fuel Resource Name
    kg,                      !- Units of Measure
    ,                        !- Energy per Unit Factor
    ${source_PEF},                   !- Source Energy Factor {J/J}
    ,                        !- Source Energy Schedule Name
    3.417E+02,               !- CO2 Emission Factor {g/MJ}
    ,                        !- CO2 Emission Factor Schedule Name
    1.186E-01,               !- CO Emission Factor {g/MJ}
    ,                        !- CO Emission Factor Schedule Name
    7.472E-01,               !- CH4 Emission Factor {g/MJ}
    ,                        !- CH4 Emission Factor Schedule Name
    6.222E-01,               !- NOx Emission Factor {g/MJ}
    ,                        !- NOx Emission Factor Schedule Name
    8.028E-03,               !- N2O Emission Factor {g/MJ}
    ,                        !- N2O Emission Factor Schedule Name
    1.872E+00,               !- SO2 Emission Factor {g/MJ}
    ,                        !- SO2 Emission Factor Schedule Name
    0.0,                     !- PM Emission Factor {g/MJ}
    ,                        !- PM Emission Factor Schedule Name
    1.739E-02,               !- PM10 Emission Factor {g/MJ}
    ,                        !- PM10 Emission Factor Schedule Name
    0.0,                     !- PM2.5 Emission Factor {g/MJ}
    ,                        !- PM2.5 Emission Factor Schedule Name
    0.0,                     !- NH3 Emission Factor {g/MJ}
    ,                        !- NH3 Emission Factor Schedule Name
    1.019E-02,               !- NMVOC Emission Factor {g/MJ}
    ,                        !- NMVOC Emission Factor Schedule Name
    5.639E-06,               !- Hg Emission Factor {g/MJ}
    ,                        !- Hg Emission Factor Schedule Name
    2.778E-05,               !- Pb Emission Factor {g/MJ}
    ,                        !- Pb Emission Factor Schedule Name
    0.4309556,               !- Water Emission Factor {L/MJ}
    ,                        !- Water Emission Factor Schedule Name
    0,                       !- Nuclear High Level Emission Factor {g/MJ}
    ,                        !- Nuclear High Level Emission Factor Schedule Name
    0;                       !- Nuclear Low Level Emission Factor {m3/MJ}
"""

    return Template(temp_elec_PEF), defaults

def add_misc_PEF():

    defaults={
      'name': 'OtherFuel1',
      'unit': 'm3',
      'energy_unit': '1000',
      'source_PEF': '1000',
    }

    temp_misc_PEF="""
  FuelFactors,
    ${name},              !- Existing Fuel Resource Name
    ${unit},                      !- Units of Measure
    ${energy_unit},                        !- Energy per Unit Factor
    ${source_PEF},                   !- Source Energy Factor {J/J}
    ,                        !- Source Energy Schedule Name
    5.21E+01,                !- CO2 Emission Factor {g/MJ}
    ,                        !- CO2 Emission Factor Schedule Name
    3.99E-02,                !- CO Emission Factor {g/MJ}
    ,                        !- CO Emission Factor Schedule Name
    1.06E-03,                !- CH4 Emission Factor {g/MJ}
    ,                        !- CH4 Emission Factor Schedule Name
    4.73E-02,                !- NOx Emission Factor {g/MJ}
    ,                        !- NOx Emission Factor Schedule Name
    1.06E-03,                !- N2O Emission Factor {g/MJ}
    ,                        !- N2O Emission Factor Schedule Name
    2.68E-04,                !- SO2 Emission Factor {g/MJ}
    ,                        !- SO2 Emission Factor Schedule Name
    0.0,                     !- PM Emission Factor {g/MJ}
    ,                        !- PM Emission Factor Schedule Name
    3.59E-03,                !- PM10 Emission Factor {g/MJ}
    ,                        !- PM10 Emission Factor Schedule Name
    0.0,                     !- PM2.5 Emission Factor {g/MJ}
    ,                        !- PM2.5 Emission Factor Schedule Name
    0,                       !- NH3 Emission Factor {g/MJ}
    ,                        !- NH3 Emission Factor Schedule Name
    2.61E-03,                !- NMVOC Emission Factor {g/MJ}
    ,                        !- NMVOC Emission Factor Schedule Name
    1.11E-07,                !- Hg Emission Factor {g/MJ}
    ,                        !- Hg Emission Factor Schedule Name
    2.13E-07,                !- Pb Emission Factor {g/MJ}
    ,                        !- Pb Emission Factor Schedule Name
    0,                       !- Water Emission Factor {L/MJ}
    ,                        !- Water Emission Factor Schedule Name
    0,                       !- Nuclear High Level Emission Factor {g/MJ}
    ,                        !- Nuclear High Level Emission Factor Schedule Name
    0;                       !- Nuclear Low Level Emission Factor {m3/MJ}
"""

    return Template(temp_misc_PEF), defaults


def add_district_PEF():

    #0.663,                   !- District Heating Efficiency
    #4.18,                    !- District Cooling COP {W/W}
    #%.3f,                   !- District Heating Efficiency
    #1.0,                    !- District Cooling COP {W/W}
    #1.000,                   !- District Heating Efficiency
    #0.585,                   !- Steam Conversion Efficiency
    #
    #2.000,                   !- District Heating Efficiency
    #1.000,                   !- District Heating Efficiency
    #3.982,                   !- District Heating Efficiency
    temp_dist_PEF="""
  EnvironmentalImpactFactors,
    ${dist_PEF},                   !- District Heating Efficiency
    1.00,                    !- District Cooling COP {W/W}
    1.00,                   !- Steam Conversion Efficiency
    80.7272,                 !- Total Carbon Equivalent Emission Factor From N2O {kg/kg}
    6.2727,                  !- Total Carbon Equivalent Emission Factor From CH4 {kg/kg}
    0.2727;                  !- Total Carbon Equivalent Emission Factor From CO2 {kg/kg}
"""

    return Template(temp_dist_PEF), {}

def zone_capacitance_research():

    defaults={
      'temp_cap': "1",
      'humid_cap': "15",
    }

    temp_zonecap="""
  ZoneCapacitanceMultiplier:ResearchSpecial,
     ${temp_cap},    !- Temperature Capacitance Multiplier
     ${humid_cap},   !- Humidity Capacitance Multiplier  Note: Adding a default moisture capacitance multiplier of 15 per Hugh Henderson ACEEE 2008 Summer Study Paper
     1;    !- Carbon Dioxide Capacity Multiplier
"""

    return Template(temp_zonecap), defaults

# Version 9.6 or higher ONLY
def Material_InternalMassv96():

    defaults={
      'const_name': "InteriorFurnishings",
      'suffix': "",
    }

    temp_intmass="""
  InternalMass,
    ${zone_name} Internal Mass${suffix},  !- Surface Name
    ${const_name},     !- Construction Name
    ${zone_name},      !- Zone or ZoneList Name
    ,                         !- Total Area Exposed to Zone {m2}
    ${surf_area};         !- Extended Field
"""
    return Template(temp_intmass), defaults


if __name__ == '__main__':

    print("Testing")

    #defs1={}
    #vals1={"one": 1, "two": 2}
    #temp1=Template("Template1,\n  I will test: ${one},\n  till you fail: ${two};")

    defs1={"three": 3}
    vals1={"one": 1, "two": 2, "three": 4}
    temp1=Template("Template1,\n  I will test: ${one},\n  till you fail: ${two},\n  or I go with you: ${three};")

    print( temp1.template )

    print( templater( vals1, temp1, defs1 ) )
