#!/usr/bin/env python3
"Templates for E+ version 9 (and onwards)."

from string import Template # Allows for substitutions using {}

from templater import templater
#from genEPJ.templater import templater

# HVACTemplates havent changes since v8.1
from templates_v8_1 import *
#from genEPJ.templates_v8_1 import *

#print("USING VERSION 9.0")

# SB: Add for Tiny House
def Sizing_SimulationControl():

    defaults={
      'zone_size':   "Yes" ,
      'system_size': "Yes" ,
      'plant_size':  "Yes" ,
      'run_size':    "No"  ,
      'run_model':   "Yes" ,
    }

    temp_SimCon="""\n
  SimulationControl,
    ${zone_size},                     !- Do Zone Sizing Calculation
    ${system_size},                     !- Do System Sizing Calculation
    ${plant_size},                     !- Do Plant Sizing Calculation
    ${run_size},                      !- Run Simulation for Sizing Periods
    ${run_model};                     !- Run Simulation for Weather File Run Periods
"""

    return Template(temp_SimCon), defaults

# TODO- Take this from the weather file
def Sizing_DesignDay():

    defaults={
      'location': "CHICAGO_IL_USA",
      'season': "WinterDesignDay",
    }

    temp_DDay="""\n
  SizingPeriod:DesignDay,
    CHICAGO_IL_USA Annual Heating 99% Design Conditions DB,  !- Name
    1,                       !- Month
    21,                      !- Day of Month
    WinterDesignDay,         !- Day Type
    -17.3,                   !- Maximum Dry-Bulb Temperature {C}
    0.0,                     !- Daily Dry-Bulb Temperature Range {deltaC}
    ,                        !- Dry-Bulb Temperature Range Modifier Type
    ,                        !- Dry-Bulb Temperature Range Modifier Day Schedule Name
    Wetbulb,                 !- Humidity Condition Type
    -17.3,                   !- Wetbulb or DewPoint at Maximum Dry-Bulb {C}
    ,                        !- Humidity Condition Day Schedule Name
    ,                        !- Humidity Ratio at Maximum Dry-Bulb {kgWater/kgDryAir}
    ,                        !- Enthalpy at Maximum Dry-Bulb {J/kg}
    ,                        !- Daily Wet-Bulb Temperature Range {deltaC}
    99063.,                  !- Barometric Pressure {Pa}
    4.9,                     !- Wind Speed {m/s}
    270,                     !- Wind Direction {deg}
    No,                      !- Rain Indicator
    No,                      !- Snow Indicator
    No,                      !- Daylight Saving Time Indicator
    ASHRAEClearSky,          !- Solar Model Indicator
    ,                        !- Beam Solar Day Schedule Name
    ,                        !- Diffuse Solar Day Schedule Name
    ,                        !- ASHRAE Clear Sky Optical Depth for Beam Irradiance (taub) {dimensionless}
    ,                        !- ASHRAE Clear Sky Optical Depth for Diffuse Irradiance (taud) {dimensionless}
    0.0;                     !- Sky Clearness
"""

    return Template(temp_PVinv), defaults

def Branch():

    defaults={
      'contrl_type': 'Active',
      #'contrl_type': 'Bypass',
    }

    temp_branch="""
  Branch,
    ${name},  !- Name
    ,                        !- Pressure Drop Curve Name
    ${type},          !- Component 1 Object Type
    ${comp_nm},  !- Component 1 Name
    ${inlet_node},  !- Component 1 Inlet Node Name
    ${outlet_node};  !- Component 1 Outlet Node Name
"""

    return Template(temp_branch), defaults

# SB: Updated for Privanas project
def MXHVACtemplate_thermosche_heat_resi():

    defaults={}

    txt_thermsch_global_resi="""\n
  Schedule:Compact,
    Htg-SetP-Sch10,            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,21.1,        !- Field 3
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,21.1,       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,21.1;       !- Field 18
"""


    return Template(txt_thermsch_global_resi), defaults

# SB: Updated for Privanas project
def MXHVACtemplate_thermosche_cool_resi():

    defaults={}

    txt_thermsch="""
  Schedule:Compact,
    Clg-SetP-Sch10,            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,23.9,        !- Field 3
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,23.9,       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,23.9;       !- Field 18
"""

    return Template(txt_thermsch), defaults

def HeatingCoilAvailALWAYSON():
    defaults={}

    txt_sch="""
  Schedule:Constant,
    HeatAvailSched,               !- Name
    ANY,                     !- Schedule Type Limits Name
    1;                       !- Hourly Value
"""
    return Template(txt_sch), defaults

def CoolingCoilAvailALWAYSON():
    defaults={}

    txt_sch="""
  Schedule:Constant,
    CoolAvailSched,               !- Name
    ANY,                     !- Schedule Type Limits Name
    1;                       !- Hourly Value
"""
    return Template(txt_sch), defaults

def HeatingCoilAvail():

    defaults={}

    txt_sch="""
  Schedule:Compact,
    HeatAvailSched,           !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 3/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 4:00,0.0,         !- Field 3
    Until: 6:00,0.3,        !- Field 4
    Until: 19:00,0.0,        !- Field 5
    Until: 24:00,0.1,        !- Field 6
    Through: 11/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0.0,         !- Field 3
    Through: 12/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 5:00,0.0,         !- Field 3
    Until: 6:00,0.1,        !- Field 4
    Until: 24:00,0.0,        !- Field 5
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 4:00,0.0,         !- Field 3
    Until: 6:00,0.3,        !- Field 4
    Until: 19:00,0.0,        !- Field 5
    Until: 24:00,0.1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1.0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1.0;        !- Field 16
"""

    return Template(txt_sch), defaults

def CoolingCoilAvail():
    defaults={}

    txt_sch="""
  Schedule:Compact,
    CoolAvailSched,           !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 3/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 6:00,0.1,        !- Field 4
    Until: 19:00,0.3,        !- Field 6
    Until: 24:00,0.5,         !- Field 3
    Through: 7/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 19:00,0.05,        !- Field 4
    Until: 24:00,0.5,         !- Field 3
    Through: 9/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 6:00,1.0,         !- Field 3
    Until: 19:00,0.3,        !- Field 5
    Until: 24:00,0.7,        !- Field 5
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 19:00,0.3,        !- Field 5
    Until: 24:00,0.0,        !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1.0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1.0;        !- Field 16
"""
#    txt_sch="""
#  Schedule:Compact,
#    CoolAvailSched,           !- Name
#    Fraction,                !- Schedule Type Limits Name
#    Through: 3/1,          !- Field 1
#    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
#    Until: 24:00,0.0,         !- Field 3
#    Through: 7/1,          !- Field 1
#    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
#    Until: 5:00,0.05,        !- Field 4
#    Until: 6:00,0.0,        !- Field 5
#    Until: 21:00,0.2,        !- Field 6
#    Until: 24:00,0.05,         !- Field 3
#    Through: 9/1,          !- Field 1
#    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
#    Until: 5:00,0.3,         !- Field 3
#    Until: 6:00,0.4,        !- Field 4
#    Until: 18:00,0.0,        !- Field 5
#    Until: 20:00,0.3,        !- Field 5
#    Until: 24:00,0.1,        !- Field 5
#    Through: 12/31,          !- Field 1
#    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
#    Until: 24:00,0.0,        !- Field 10
#    For: SummerDesignDay,    !- Field 12
#    Until: 24:00,1.0,        !- Field 13
#    For: WinterDesignDay,    !- Field 15
#    Until: 24:00,1.0;        !- Field 16
#"""

    return Template(txt_sch), defaults

# SB: NOTE: Heat MORE available than 'HIGH' scenario (makes no sense)
def HeatingCoilAvailLOW():

    defaults={}

    txt_sch="""
  Schedule:Compact,
    HeatAvailSched,           !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 3/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 4:00,0.0,         !- Field 3
    Until: 6:00,0.3,        !- Field 4
    Until: 19:00,0.0,        !- Field 5
    Until: 24:00,0.1,        !- Field 6
    Through: 11/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0.0,         !- Field 3
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 4:00,0.0,         !- Field 3
    Until: 6:00,0.3,        !- Field 4
    Until: 19:00,0.0,        !- Field 5
    Until: 24:00,0.1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1.0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1.0;        !- Field 16
"""

    return Template(txt_sch), defaults

def CoolingCoilAvailLOW():
    defaults={}

    txt_sch="""
  Schedule:Compact,
    CoolAvailSched,           !- Name
    Fraction,                !- Schedule Type Limits Name
    Through: 3/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0.0,         !- Field 3
    Through: 7/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 5:00,0.05,        !- Field 4
    Until: 18:00,0.0,        !- Field 4
    Until: 20:00,0.2,        !- Field 4
    Until: 24:00,0.05,         !- Field 3
    Through: 9/1,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 5:00,0.3,         !- Field 3
    Until: 6:00,0.4,         !- Field 3
    Until: 18:00,0.0,        !- Field 5
    Until: 20:00,0.3,        !- Field 5
    Until: 24:00,0.1,        !- Field 5
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0.0,        !- Field 10
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1.0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1.0;        !- Field 16
"""

    return Template(txt_sch), defaults



def zone_capacitance_research():

    defaults={
      'temp_cap': "1",
      'humid_cap': "15",
    }

    temp_zonecap="""
  ZoneCapacitanceMultiplier:ResearchSpecial,
    Multiplier,              !- Name
    ,                        !- Zone or ZoneList Name
    ${temp_cap},                     !- Temperature Capacity Multiplier
    ${humid_cap},                     !- Humidity Capacity Multiplier
    1.0,                     !- Carbon Dioxide Capacity Multiplier
    ;                        !- Generic Contaminant Capacity Multiplier
"""

    return Template(temp_zonecap), defaults

# Version 9.6 or higher ONLY
#def Material_InternalMass():
#
#    defaults={
#      'const_name': "InteriorFurnishings",
#      'suffix': "",
#    }
#
#    temp_intmass="""
#  InternalMass,
#    ${zone_name} Internal Mass${suffix},  !- Surface Name
#    ${const_name},     !- Construction Name
#    ${zone_name},      !- Zone or ZoneList Name
#    ,                         !- Total Area Exposed to Zone {m2}
#    ${surf_area};         !- Extended Field
#
#
#"""
#    return Template(temp_intmass), defaults

def HVACtemplate_thermosche_heat_forces():
    """
    Required heating schedule for military project.
    """

    defaults={
      'name':     "Htg-SetP-Sch10",
      'setback':  "16.0",
      'ramp':     "20.0",
      'setpoint': "23.0",
      'time_sb':  "5:30",
      'time_rp':  "6:00",
      'time_sp':  "18:00",
      'date_OFF': "6/01",
      'date_ON':  "10/1",
    }

    txt_thermsch="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_OFF},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: ${date_ON},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint};       !- Field 18
"""

    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_cool_forces():
    """
    Required cooling schedule for military project.
    """

    defaults={
      'name':     "Clg-SetP-Sch10",
      'setback':  "32.0",
      'ramp':     "28.0",
      'setpoint': "25.0",
      'time_sb':  "5:30",
      'time_rp':  "6:00",
      'time_sp':  "18:00",
      'date_OFF': "10/15",
      'date_ON':  "5/15",
    }

    txt_thermsch="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_ON},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: ${date_OFF},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback};       !- Field 16
"""
    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_heat_BGIS():
    """
    Required cooling schedule for BGIS buildings
    """

    defaults={
      'name':     "Htg-SetP-Sch10",
      'setback':  "16.0",
      'ramp':     "20.0",
      'setpoint': "22.0",
      'time_sb':  "5:30",
      'time_rp':  "6:00",
      'time_sp':  "18:00",
      'date_OFF': "5/15",
      'date_ON':  "10/15",
    }

    txt_thermsch="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_OFF},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: ${date_ON},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint},       !- Field 18
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 5
    Until: ${time_sp},${setpoint},       !- Field 7
    Until: 24:00,${setback},       !- Field 9
    For: SummerDesignDay,    !- Field 14
    Until: 24:00,${setback},       !- Field 15
    For: WinterDesignDay,    !- Field 17
    Until: 24:00,${setpoint};       !- Field 18
"""

    return Template(txt_thermsch), defaults

def HVACtemplate_thermosche_cool_BGIS():
    """
    Required cooling schedule for BGIS buildings
    """

    defaults={
      'name':     "Clg-SetP-Sch10",
      'setback':  "28.0",
      'ramp':     "25.0",
      'setpoint': "23.0",
      'time_sb':  "5:30",
      'time_rp':  "6:00",
      'time_sp':  "18:00",
      'date_OFF': "10/15",
      'date_ON':  "5/15",
    }

    txt_thermsch="""\n
  Schedule:Compact,
    ${name},            !- Name
    Temperature,             !- Schedule Type Limits Name
    Through: ${date_ON},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: ${date_OFF},          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback},       !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays WeekEnds Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_sb},${setback},        !- Field 3
    Until: ${time_rp},${ramp},        !- Field 3
    Until: ${time_sp},${setpoint},       !- Field 5
    Until: 24:00,${setback},       !- Field 7
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,${setpoint},       !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,${setback};       !- Field 16
"""

    return Template(txt_thermsch), defaults

def HVAC_HeatPumpWaterHeater():

    defaults={
        #'tank_type': 'WaterHeater:Mixed',
        'tank_type': 'WaterHeater:Stratified',
    }

    temp_heatpump="""
  WaterHeater:HeatPump:PumpedCondenser,
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
    Coil:WaterHeating:AirToWaterHeatPump:Pumped,  !- DX Coil Object Type
    HPWHOutdoorDXCoil,       !- DX Coil Name
    11.0,                    !- Minimum Inlet Air Temperature for Compressor Operation {C}
    ,                        !- Maximum Inlet Air Temperature for Compressor Operation {C}
    Outdoors,                !- Compressor Location
    ,                        !- Compressor Ambient Temperature Schedule Name
    Fan:SystemModel,               !- Fan Object Type
    HPWHOutdoorFan,          !- Fan Name
    BlowThrough,             !- Fan Placement
    ,                        !- On Cycle Parasitic Electric Load {W}
    ,                        !- Off Cycle Parasitic Electric Load {W}
    ;                        !- Parasitic Heat Rejection Location

  Coil:WaterHeating:AirToWaterHeatPump:Pumped,
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

    Fan:SystemModel,
      HPWHOutdoorFan,            !- Name
      PlantHPWHSch,            !- Availability Schedule Name
      HPOutdoorAirInletNode,     !- Air Inlet Node Name
      HPOutdoorFanAirOutletNode, !- Air Outlet Node Name
      0.2685,                  !- Design Maximum Air Flow Rate {m3/s}
      Discrete,                !- Speed Control Method
      0.0,                     !- Electric Power Minimum Flow Rate Fraction
      100.0,                   !- Design Pressure Rise {Pa}
      0.9,                     !- Motor Efficiency
      1.0,                     !- Motor In Air Stream Fraction
      AUTOSIZE,                !- Design Electric Power Consumption {W} 
      TotalEfficiencyAndPressure,  !- Design Power Sizing Method
      ,                        !- Electric Power Per Unit Flow Rate {W/(m3/s)}
      ,                        !- Electric Power Per Unit Flow Rate Per Unit Pressure {W/((m3/s)-Pa)}
      0.7;                     !- Fan Total Efficiency

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

def Equipment_ONOFFGrid_Transformer():
    """
    Specify building electrical supply using a transformer with schedule
    """

    defaults={
      'name':     "Transformer 1",
      'name2':     "Transformer 2",
      'battery_name':     "Battery 1",
      'avail_sche':     "Loss of Power Schedule",
      'battavail_sche':  "ALWAYS ON PV 2",
      'capacity':  "95000", # kW
      'phase':  "3", # kW
      'inverter_name': "Simple Ideal Inverter big array",
      'sensor_elec': "Electric", # version 9.0
      #'sensor_elec': "Electricity", # >version 9.4
      'sensor_suffix': "Power", # version 9.0
      #'sensor_suffix': "Rate", # version >9.4
      'batt_type': "Battery", #  'Battery' or 'Simple'
    }

    txt_transformer="""\n
  !- ElectricLoadCenter:Transformer,
  !-   ${name},           !- Name
  !-   ${avail_sche},               !- Availability Schedule Name
  !-   PowerInFromGrid,         !- Transformer Usage
  !-   ,                        !- Zone Name
  !-   ,                        !- Radiative Fraction
  !-   ${capacity},                   !- Rated Capacity {VA}
  !-   ${phase},                       !- Phase
  !-   Aluminum,                !- Conductor Material
  !-   150,                     !- Full Load Temperature Rise {C}
  !-   0.1,                     !- Fraction of Eddy Current Losses
  !-   NominalEfficiency,       !- Performance Input Method
  !-   ,                        !- Rated No Load Loss {W}
  !-   ,                        !- Rated Load Loss {W}
  !-   0.985,                   !- Nameplate Efficiency
  !-   0.35,                    !- Per Unit Load for Nameplate Efficiency
  !-   75,                      !- Reference Temperature for Nameplate Efficiency {C}
  !-   ,                        !- Per Unit Load for Maximum Efficiency
  !-   Yes,                     !- Consider Transformer Loss for Utility Cost
  !-   Electricity:Building;    !- Meter 1 Name

  ElectricLoadCenter:Transformer,
    ${name2},             !- Name
    ${battavail_sche},          !- Availability Schedule Name
    LoadCenterPowerConditioning,  !- Transformer Usage
    ${zone_name},  !- Zone Name
    ,                        !- Radiative Fraction
    15000,                   !- Rated Capacity {VA}
    ${phase},                       !- Phase
    Aluminum,                !- Conductor Material
    150,                     !- Full Load Temperature Rise {C}
    0.1,                     !- Fraction of Eddy Current Losses
    RatedLosses,             !- Performance Input Method
    ,                        !- Rated No Load Loss {W}
    ,                        !- Rated Load Loss {W}
    0.98,                    !- Nameplate Efficiency
    0.35,                    !- Per Unit Load for Nameplate Efficiency
    75,                      !- Reference Temperature for Nameplate Efficiency {C}
    ,                        !- Per Unit Load for Maximum Efficiency
    Yes;                     !- Consider Transformer Loss for Utility Cost

  ElectricLoadCenter:Distribution,
    simple electric load distributer,  !- Name
    ${pv_list},                 !- Generator List Name
    Baseload,                !- Generator Operation Scheme Type
    0,                       !- Generator Demand Limit Scheme Purchased Electric Demand Limit {W}
    ,                        !- Generator Track Schedule Name Scheme Schedule Name
    ,                        !- Generator Track Meter Scheme Meter Name
    DirectCurrentWithInverterACStorage,  !- Electrical Buss Type
    ${inverter_name},   !- Inverter Name
    ${battery_name},                 !- Electrical Storage Object Name
    ${name2},             !- Transformer Object Name
    TrackFacilityElectricDemandStoreExcessOnSite,  !- Storage Operation Scheme
    ,                        !- Storage Control Track Meter Name
    converter;               !- Storage Converter Object Name

EnergyManagementSystem:Sensor,
    batterycapacity,         !- Name
    ${battery_name},                 !- Output:Variable or Output:Meter Index Key Name
    Electric Storage ${batt_type} Charge State ;  !- Output:Variable or Output:Meter Name

  ElectricLoadCenter:Storage:Converter,
    converter,               !- Name
    ${battavail_sche},          !- Availability Schedule Name
    SimpleFixed,             !- Power Conversion Efficiency Method
    0.95,                    !- Simple Fixed Efficiency
    ,                        !- Design Maximum Continuous Input Power {W}
    ,                        !- Efficiency Function of Power Curve Name
    ,                        !- Ancillary Power Consumed In Standby {W}
    ${zone_name},  !- Zone Name
    0.25;                    !- Radiative Fraction

  EnergyManagementSystem:ProgramCallingManager,
    ENERGYMANAGMENT,         !- Name
    BeginTimestepBeforePredictor,  !- EnergyPlus Model Calling Point
    strategy1;               !- Program Name 1

  EnergyManagementSystem:Program,
    strategy1,               !- Name
    SET a= InverterOutput,   !- Program Line 1
    SET b= BuildingDemand,   !- Program Line 2
    SET c= a-b,              !- A4
    SET d= b-a,              !- A5
    ,                        !- A6
    IF a > b,                !- A7
    ,                        !- A8
    SET battery_discharge = 0,  !- A9
    SET battery_Charge = c,  !- A10
    ELSE,                    !- A11
    ,                        !- A12
    SET battery_Charge =  0, !- A13
    SET battery_discharge = d,  !- A14
    ENDIF;                   !- A15

  EnergyManagementSystem:Program,
    strategy2,         !- Name
    SET a= InverterOutput,         !- Program Line 1
    SET b= BuildingDemand,    !- Program Line 2
    SET c= a-b,              !- A4
    SET d= b-a,              !- A5
    SET avail=outage_schedule,!- echo out for debug
    SET recov=recovered_schedule,!- echo out for debug
    SET isnight=IsNighttime,!- echo out for debug
    IF avail==0,          !- A4 USE STRATEGY 1
      IF a > b,                !- A7
        SET battery_discharge = 0,  !- A9
        SET battery_Charge = c,  !- A10
      ELSE,                    !- A11
        SET battery_Charge =  0, !- A13
        SET battery_discharge = d,  !- A14
      ENDIF,                   !- A15
    ELSE,                 !- A7 CHARGE DURING EVENINGS (cheaper)
      IF isnight==1,          !- A4
        SET battery_Charge= 4000,!- A5
        SET battery_discharge = 0,  !- A6
      ELSE,                    !- A7
        IF a > b,                !- A8
          SET battery_Charge= c,!- A9
          SET battery_discharge = 0,  !- A10
        ELSE,                    !- A11
          SET battery_Charge= 0,  !- A12
          SET battery_discharge = d,  !- A13
        ENDIF,                   !- A14
      ENDIF,                   !- A15
    ENDIF;                   !- A15

  Schedule:Compact,
    Allow Battery Charging,               !- Name
    Fraction,      !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 07:00,            !- Field 3
    1,                       !- Field 4
    Until:19:00,             !- Field 5
    0,                       !- Field 6
    Until:24:00,             !- Field 5
    1,                       !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0;        !- Field 16

  EnergyManagementSystem:Sensor,
    IsNighttime,                !- Name
    Allow Battery Charging,  !- Output:Variable or Output:Meter Index Key Name
    Schedule Value;          !- Output:Variable or Output:Meter Name


  EnergyManagementSystem:Sensor,
    InverterOutput,          !- Name
    ${inverter_name},   !- Output:Variable or Output:Meter Index Key Name
    Inverter AC Output ${sensor_elec} ${sensor_suffix};  !- Output:Variable or Output:Meter Name

  EnergyManagementSystem:Sensor,
    BuildingDemand,          !- Name
    Whole Building,          !- Output:Variable or Output:Meter Index Key Name
    Facility Total Building ${sensor_elec} Demand ${sensor_suffix};  !- Output:Variable or Output:Meter Name
"""

    return Template(txt_transformer), defaults

def Equipment_ONOFFGrid_BatterySimple():
    """
    Specify building electrical supply using a transformer with schedule
    """

    defaults={
      'name':     "Battery 1",
      'schedule':  "ALWAYS ON PV 2", # TODO- change
      'init_charge_joule':  "1.0",
      'capacity_joule':  "24", # Battery Storage Capacity (Units J)
      'max_power':  "1e10", # Maximum Power for Discharging/Charging {W}
    }


    txt_battery="""\n
  ElectricLoadCenter:Storage:Simple,
    ${name},                 !- Name
    ${schedule},          !- Availability Schedule Name
    ,                        !- Zone Name
    0.0,                     !- Radiative Fraction for Zone Heat Gains
    0.9,                     !- Nominal Energetic Efficiency for Charging
    0.9,                     !- Nominal Discharging Energetic Efficiency
    ${capacity_joule},                  !- Maximum Storage Capacity {J}
    ${max_power},                 !- Maximum Power for Discharging {W}
    ${max_power},                 !- Maximum Power for Charging {W}
    ${init_charge_joule};                  !- Initial State of Charge {J}

"""

    return Template(txt_battery), defaults

def Equipment_ONOFFGrid_Battery():
    """
    Specify building electrical supply using a transformer with schedule
    """

    defaults={
      'name':     "Battery 1",
      'schedule':  "ALWAYS ON PV 2", # TODO- change
      'init_charge':  "1.0",
      'num_batt':  "1", # Number of batteries in series
      'capacity':  "24", # Battery Storage Capacity (Units Ah)
    }

    txt_battery="""\n
  ElectricLoadCenter:Storage:Battery,
    ${name},                 !- Name
    ${schedule},          !- Availability Schedule Name
    ${zone_location},  !- Zone Name
    0.075,                   !- Radiative Fraction
    1,                       !- Number of Battery Modules in Parallel
    ${num_batt},                       !- Number of Battery Modules in Series
    ${capacity},                      !- Maximum Module Capacity {Ah}
    ${init_charge},                     !- Initial Fractional State of Charge
    0.37,                    !- Fraction of Available Charge Capacity
    0.5871,                  !- Change Rate from Bound Charge to Available Charge {1/hr}
    350,                     !- Fully Charged Module Open Circuit Voltage {V}
    350,                     !- Fully Discharged Module Open Circuit Voltage {V}
    Charging,                !- Voltage Change Curve Name for Charging
    Discharging,             !- Voltage Change Curve Name for Discharging
    0.05,                    !- Module Internal Electrical Resistance {ohms}
    100,                     !- Maximum Module Discharging Current {A}
    300,                     !- Module Cut-off Voltage {V}
    1,                       !- Module Charge Rate Limit
    No,                      !- Battery Life Calculation
    10;                      !- Number of Cycle Bins

  Curve:RectangularHyperbola2,
    Charging,                !- Name
    -.2765,                  !- Coefficient1 C1
    -93.27,                  !- Coefficient2 C2
    0.0068,                  !- Coefficient3 C3
    0,                       !- Minimum Value of x
    1,                       !- Maximum Value of x
    ,                        !- Minimum Curve Output
    ,                        !- Maximum Curve Output
    Dimensionless,           !- Input Unit Type for x
    Dimensionless;           !- Output Unit Type

  Curve:RectangularHyperbola2,
    Discharging,             !- Name
    0.0899,                  !- Coefficient1 C1
    -98.24,                  !- Coefficient2 C2
    -.0082,                  !- Coefficient3 C3
    0,                       !- Minimum Value of x
    1,                       !- Maximum Value of x
    ,                        !- Minimum Curve Output
    ,                        !- Maximum Curve Output
    Dimensionless,           !- Input Unit Type for x
    Dimensionless;           !- Output Unit Type
"""

    return Template(txt_battery), defaults

def SchedulesOutagesSameDay():

    defaults={
      'outage_name':     "Loss of Power Schedule",
      'recov_name':     "Recovered Schedule",
      'date_start_b4':     "1/09",
      'date_start':     "1/10",
      'time_start':     "6:00",
      #'date_end':     "1/12",
      #'date_end_b4':     "1/11",
      'time_end':     "20:00",
    }

#    Fraction,                !- Schedule Type Limits Name
    txt_sch="""
  Schedule:Compact,
    ${outage_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_start_b4},          !- Field 1
    For: AllDays, !- Field 2
    Until: 24:00,1,        !- Field 3
    Through: ${date_start},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_start},1,         !- Field 2
    Until: ${time_end},0,        !- Field 3
    Until: 24:00,1,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1,        !- Field 16
    Through: 12/31,          !- Field 1
    For: AllDays, !- Field 2
    Until: 24:00,1;        !- Field 6

  Schedule:Compact,
    ${recov_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_end_b4},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: ${date_end},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_end},0,         !- Field 3
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0;        !- Field 16

  EnergyManagementSystem:Sensor,
    outage_schedule, !Name
    Loss of Power Schedule, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

  EnergyManagementSystem:Sensor,
    recovered_schedule, !Name
    Recovered Schedule, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

   EnergyManagementSystem:ProgramCallingManager,
     My Schedule Calculator Example,
     InsideHVACSystemIterationLoop,
${ems_progblob};
"""

    return Template(txt_sch), defaults

def SchedulesOutagesOneDay():

    defaults={
      'outage_name':     "Loss of Power Schedule",
      'recov_name':     "Recovered Schedule",
      'date_start_b4':     "1/09",
      'date_start':     "1/10",
      'time_start':     "6:00",
      'date_end':     "1/12",
      'date_end_b4':     "1/11",
      'time_end':     "20:00",
    }

#    Fraction,                !- Schedule Type Limits Name
    txt_sch="""
  Schedule:Compact,
    ${outage_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_start_b4},          !- Field 1
    For: AllDays, !- Field 2
    Until: 24:00,1,        !- Field 3
    Through: ${date_start},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_start},1,         !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1,        !- Field 16
    Through: ${date_end},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_end},0,         !- Field 3
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1,        !- Field 16
    Through: 12/31,          !- Field 1
    For: AllDays, !- Field 2
    Until: 24:00,1;        !- Field 6

  Schedule:Compact,
    ${recov_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_start},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: ${date_end},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_end},0,         !- Field 3
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0;        !- Field 16

  EnergyManagementSystem:Sensor,
    outage_schedule, !Name
    Loss of Power Schedule, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

  EnergyManagementSystem:Sensor,
    recovered_schedule, !Name
    Recovered Schedule, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

   EnergyManagementSystem:ProgramCallingManager,
     My Schedule Calculator Example,
     InsideHVACSystemIterationLoop,
${ems_progblob};
"""

    return Template(txt_sch), defaults


def SchedulesOutagesMultiDay():

    defaults={
      'outage_name':     "Loss of Power Schedule",
      'recov_name':     "Recovered Schedule",
      'date_start_b4':     "1/09",
      'date_start':     "1/10",
      'time_start':     "6:00",
      'date_end':     "1/12",
      'date_end_b4':     "1/11",
      'time_end':     "20:00",
    }

#    Fraction,                !- Schedule Type Limits Name
    txt_sch="""
  Schedule:Compact,
    ${outage_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_start_b4},          !- Field 1
    For: AllDays, !- Field 2
    Until: 24:00,1,        !- Field 3
    Through: ${date_start},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_start},1,         !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1,        !- Field 16
    Through: ${date_end_b4},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1,        !- Field 16
    Through: ${date_end},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_end},0,         !- Field 3
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,1,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,1,        !- Field 16
    Through: 12/31,          !- Field 1
    For: AllDays, !- Field 2
    Until: 24:00,1;        !- Field 6

  Schedule:Compact,
    ${recov_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_start},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: ${date_end_b4},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: ${date_end},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_end},0,         !- Field 3
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0;        !- Field 16

  EnergyManagementSystem:Sensor,
    outage_schedule, !Name
    Loss of Power Schedule, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

  EnergyManagementSystem:Sensor,
    recovered_schedule, !Name
    Recovered Schedule, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

   EnergyManagementSystem:ProgramCallingManager,
     My Schedule Calculator Example,
     InsideHVACSystemIterationLoop,
${ems_progblob};
"""

    return Template(txt_sch), defaults

def EMS_SensorActuator_perLoad():

    defaults={
      'act_outage':   "0",
      'act_batt':     "0",
      'act_recov':    "1",
      'min_SoC':    "0.1",
    }

#    Fraction,                !- Schedule Type Limits Name
    txt_ems="""
   EnergyManagementSystem:Actuator,
     ${act_name},
     ${sche_name},${sche_type},Schedule Value;

   EnergyManagementSystem:Sensor,
    ${sens_name}, !Name
    ${sche_name}, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

   EnergyManagementSystem:Program,
     ${prog_name},
     Set SoC=batterycapacity,  !- echo out for debug
     Set avail=outage_schedule,!- echo out for debug
     Set recov=recovered_schedule,!- echo out for debug
     Set my${sens_name}=${sens_name},!- echo out for debug
     IF (SoC <= ${min_SoC}) && (avail == 0),  !- Outage, NO charge available
       Set ${act_name} = ${act_outage},
     ELSEIF (SoC > ${min_SoC}) && (avail == 0), !- Outage, but charge available
       Set ${act_name} = ${act_batt}, !- End user supplied
     ELSEIF (avail == 1) && (recov == 1), !- Behaviour after Recover
       Set ${act_name} = ${act_recov}, !- End user supplied
     ENDIF;
"""

    return Template(txt_ems), defaults


def EMS_VerboseOutputs():
    defaults={
    }

    txt_ems="""
  Output:EnergyManagementSystem,
    Verbose,                    !- Actuator Availability Dictionary Reporting
    Verbose,                    !- Internal Variable Availability Dictionary Reporting
    Verbose;              !- EMS Runtime Language Debug Output Level
"""
    return Template(txt_ems), defaults

def HVACtemplate_thermosche_preoutagemod():

# NOTE- Use built-in variables from ERL
# https://bigladdersoftware.com/epx/docs/9-1/ems-application-guide/variables.html
# Hour # 0-23 (whole hours only)
# DayOfYear # 1-365

    defaults={
      'name':     "Htg-SetP-Sch10",
      'modtemp':  "23", #degC
      'temp':     "20", #degC

      'day_str':  "36",  # Day that preset starts
      'time_str':  "8", # Time that preset starts

      'day_stp':  "36",  #  Day that preset stops
      'time_stp':  "14", # Time that preset stops

    }
    txt_EMS_thermsch_override="""\n

  EnergyManagementSystem:Program,
     MyComputedOverrideSetpoint, !- Program Name
     Set mysetp_sche=setp_sche,  !- echo out for debug
     IF (Hour >= ${time_str}) && (Hour <= ${time_stp}) && (DayOfYear == ${day_str}),  !- Triggered preset going into outage
       Set mySetPSch_Override = ${modtemp},
     ELSEIF (Hour > ${time_stp}) && (DayOfYear == ${day_str}),  !- Preset expired due to outage. Set back to default
       Set mySetPSch_Override = ${temp},
     ENDIF;

   EnergyManagementSystem:Actuator,
     mySetPSch_Override,
     ${name},Schedule:Compact,Schedule Value;

   EnergyManagementSystem:Sensor,
    setp_sche, !Name
    ${name}, ! Output:Variable Index Key Name
    Schedule Value; ! Output:Variable or Output:Meter Name

"""

    return Template(txt_EMS_thermsch_override), defaults

def GENEPJ_TEMPLATE_NAME():


    defaults={
      'thermal_mass': 100, #kg
      'peak_temp': 60,     #degC
    }

    txt_template="""\n
  IDFOBJ_heater
    1,     !- IDF INFO 1
    2,     !- IDF INFO 2
    3;     !- IDF INFO 3

  Schedule:Compact,
    ${recov_name},           !- Name
    On/Off,                !- Schedule Type Limits Name
    Through: ${date_start},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: ${date_end_b4},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,0,        !- Field 3
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: ${date_end},          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: ${time_end},0,         !- Field 3
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0,        !- Field 16
    Through: 12/31,          !- Field 1
    For: WeekDays Weekends Holiday CustomDay1 CustomDay2, !- Field 2
    Until: 24:00,1,        !- Field 6
    For: SummerDesignDay,    !- Field 12
    Until: 24:00,0,        !- Field 13
    For: WinterDesignDay,    !- Field 15
    Until: 24:00,0;        !- Field 16


"""

    return Template(txt_template), defaults

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

