#!/usr/bin/env bash

# Run this script from opti dir
# > ./sim/script/write2db.sh sim/tmp-run-uP7Vs1YJCq

# NOTE: This script is run AFTER EnergyPlus finishes. Used to interpret results into sqlite database

# Simulation directory
simdir=$1
##TODO SB: check if in tmp-run OR link to db in directory
mydb=db/data.db3

myressql=${simdir}/Output/*ref_opti.sql
myhtml=${simdir}/Output/*optiTable.html
mycommands=${simdir}/sql_commands.txt
myindiv=`cat ${simdir}/indiv.txt`

echo $myres $myhtml $mycommands

rm -f $mycommands

##############
## Write EUIs to file
##############
echo  "Get EUI results directly from HTML file"
neteui=`grep 'Net Site Energy' ${myhtml} --after-context=3 | sed -e 's/<td align="right">//g; s/<\/td>//g; s/[ ]//g' | sed -n 3p`
grosseui=`grep 'Total Site Energy' ${myhtml} --after-context=3 | sed -e 's/<td align="right">//g; s/<\/td>//g; s/[ ]//g' | sed -n 3p`
echo "eui,$neteui" > ${myres}
echo "fit,$neteui" >> ${myres}
echo "eui_nopv,$grosseui"  >> ${myres}

# Write hours of heating/cooling not met
echo "unmet_heat_hrs,"`grep 'Time Setpoint Not Met During Occupied Heating' ${myhtml} --after-context=3 | sed -e 's/<td align="right">//g; s/<\/td>//g; s/[ ]*//g' | sed -n 2p` >> ${myres}
echo "unmet_cool_hrs,"`grep 'Time Setpoint Not Met During Occupied Cooling' ${myhtml} --after-context=3 | sed -e 's/<td align="right">//g; s/<\/td>//g; s/[ ]*//g' | sed -n 2p` >> ${myres}

# Floor area is actually an input. Want in database to be used in community simulation (eg. weighted EUI for all buildings)
myarea=`grep '>Total Building Area' ${myhtml} --after-context=3 | sed -e 's/<td align="right">//g; s/<\/td>//g; s/[ ]//g' | sed -n 2p`
echo "area,${myarea}" >> $myres

# Extract how long eplus took to run
hrminsec=`grep -Eo "Elapsed Time=.*([0-9])" ${simdir}/Output/*opti.err  | sed -e 's/[a-z]//g; s/[A-Z]//g; s/=//g; s/^ //g'`
echo "EPlus Time: " $hrminsec
stime=`echo $hrminsec | awk '{printf "%f", $1*60 + $2 + $3/60}'`
echo "eplustime,$stime" >> $myres

keys=(
    "eui" # Changed this script output. Was Net-EUI
    "fit" # Changed this script output. Was Net-EUI
    "eui_nopv" # Changed this script output. Was Gross-EUI
    "area"
    "eplustime" # Extracted in this file
     )

for k in "${keys[@]}"; do
  # Read variable value from file using keyword
  v=`grep -e "^${k}," $myres | cut -d, -f2`
  if [[ $v = *[[:space:]]* ]]; then
    echo "UPDATE indiv SET ${k} = '${v}' WHERE indiv = '$myindiv';" >> $mycommands
  else
    echo "UPDATE indiv SET ${k} = ${v} WHERE indiv = '$myindiv';" >> $mycommands
  fi
done

sqlite3 $mydb < $mycommands
