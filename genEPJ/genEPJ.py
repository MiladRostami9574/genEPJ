# Goal: Allow a genEPJ project to run from a central library


# Add flags so you don't need following files to run:
# costing.json
# resiliency_events.json
# weather.json

# genEPJ --parameters=opti_variables.json --process=process.json --use-resil=true -use-outage=true

# TODO- how to apply JSON variables to task?
# > Might be better to specify skeleton genEPJ instruction set which get imported into genEPJ.py as variables

# process.json
#```
#{
#  "IDF": "EvePark.idf",
#  "EPW": "CAN_ON_London.716230_CWEC.epw",
#  "EPversion": "22-1-0",
#  "building_type": "multi-residential",
#  "building_location": "Ontario",
#  "heat_thermo": "HVACtemplate_thermosche_heat_resi",
#  "cool_thermo": "HVACtemplate_thermosche_cool_resi",
#  "fn_list": [
#            "multi-residential",
#             ]
#  "run_eplus": "False",
#  "force_recreate": "True",
#  "tasks": [
#            "prep",
#             ]
#}
#```

#Apply Process here (similar to any other genEPJ file)
# * use heat_thermo/cool_thermo or None
# * if use_resil: 

