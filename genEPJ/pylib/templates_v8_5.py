#!/usr/bin/env python3
"Templates for E+ version 8.5 (and onwards). Templates are overloaded by later versions if changes to templates are required."

from string import Template # Allows for substitutions using {}

from templater import templater

# HVACTemplates havent changes since v8.1
from templates_v8_1 import *

#print("USING VERSION 8.5")

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

