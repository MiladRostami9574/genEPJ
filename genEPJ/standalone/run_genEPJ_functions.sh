#!/bin/sh

# Exemplar use:
# genEPJ/tests/run_genEPJ_functions.sh > tests/OUTPUT.txt

# TODO-
# 0. add_HVAC: fix global thermostat (try/except and set to multires)
# 1. CHECK setup SQL files (in data_temp?)
# 2. Option: run E+ (?). Have stats for % converted, % ran
# 3. set better options for within genEPJ fns. Give more useful feedback as to why failures are occuring
# 4. TEST- try to see what % are for most of your sim-* dirs
# 5. Option: update E+ dir to match Version in IDF




idf=$1
genEPJ=generate_EPJ.py
tmpdir=tests/temp
cstcsv=costing.csv
script=standalone/apply_function.py
#script="python2 standalone/apply_function.py"

# Running from sim-* directory
if [[ ! -f $genEPJ ]]; then
  echo "Running from sim-* directory"
  genEPJ=genEPJ/generate_EPJ.py
  script=genEPJ/standalone/apply_function.py
  #script="python2 genEPJ/standalone/apply_function.py"
  tmpdir=tests # placed in sim-* which is cleaner
fi

echo

# TODO- refactor
# SB- sed 's/ {2,}/ /g' matches two or more spaces
#fns1=`perl -nle'print if m{def \w+_file\(}' $genEPJ | sed -e 's/def //g; s/(.*//g; s/#.*//g; s/ {2,}/ /g;' | tr '\n' ' '`
fns=$(grep -E 'def \w+_file\(' "$genEPJ" | \
      sed -e 's/def //g; s/(.*//g; s/#.*//g; s/ {2,}/ /g;' | \
      tr '\n' ' ')
# Remove check_model_file to avoid recursive call to this script called from `genEPJ/standalone/check_model.py`
fns=`echo $fns | sed -e 's/  / /g; s/^  //g; s/check_model_file//g;'`

# HVAC tests
#fns=`echo add_HVAC_ideal_file add_HVAC_VAVelec_file add_HVAC_VAVgas_file add_HVAC_PTAC_file add_HVAC_VRF_file add_HVAC_FCU_file add_HVAC_PTHP_file add_HVAC_HP_file add_HVAC_Baseboard_file add_HVAC_RTU_file`
# SQL tests
#fns=`echo mod_wintype_file mod_WWR_file add_exteriorlights_file add_floor_multiplier_file add_PV_by_azi_file add_DHW_loads_file add_natural_ventilation_file add_Daylight_zones_file add_ExtShading_file add_internalmass_file add_window_shading_file add_ballastedPVrack add_exhaust_file scale_xyz_file diagnostic_output_areas_file`
# JSON tests
#fns=`echo mod_JSON_file add_JSON_file  remove_types_from_JSON_file swap_IDFJSON_file swap_EPPYIDF_file`

echo $fns
sleep 5s

mkdir -p $tmpdir
touch costing.csv

passed=0
total_tests=`echo $fns | tr ' ' '\n' | wc -l`
tests=0
#TODO if json in name; use $epjson NOT $idf
for fn in $fns; do
  echo "Testing Function: $fn"
  echo $script $fn $idf;
  output=`$script $fn $idf`;
  tmpfn=$tmpdir/${fn}.txt
  # sed removes colors/bold
  $script $fn $idf | sed -r "s/\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]//g" > $tmpfn
  # Run only if script completes
  if [[ $output == *"Saving new file to"* ]]; then
  	newfile=`grep 'Saving new file to' $tmpfn | cut -d':' -f 2`
  	echo $newfile
  	mv $newfile $tmpdir
  	passed=$((passed+1))
  else
  	mv $tmpfn `echo $tmpfn | sed -e 's/.txt/_FAILED.txt/g'`
  fi
  tests=$((tests+1))
  echo
done;

echo "TOTAL TESTS: " $total_tests
perc_passed=`echo "scale=1; 100*$passed/$total_tests" | bc -l`
echo "% Passes: " $perc_passed
rm -f costing.csv

echo "TOTAL TESTS: " $total_tests > $tmpdir/RESULTS.txt
echo "% Passes: " $perc_passed >> $tmpdir/RESULTS.txt
