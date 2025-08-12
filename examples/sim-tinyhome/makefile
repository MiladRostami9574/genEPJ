#!/usr/bin/make -f

genEPJ=`ls *_genEPJ.py`

all:
	echo "Running genEPJ simulation"
	mkdir data_temp && ln -s /MetalMan/Output data_temp/Output
	cp *idf data_temp/
	# Runs Annual Simulation
	touch sim_errors.txt
	sleep 0.5
	# Runs basefile and prep in Output
	-python3 ${genEPJ}
	cp data_temp/*opti.idf .
	-${ENERGYPLUS_DIR}/runenergyplus *prep_opti.idf CAN_ON_Ottawa.716280_CWEC.epw
	-rm -f data_temp/Output

clean:
	rm -rf expandedidf* data_temp *opti.idf *sql *idd eplus* Energy+* in.* OptiHouse_errors.txt *_optiNPV.csv OptiHouse_results.txt GenOpt.log OutputListingAll.txt OutputListingMain.txt Output tmp-genopt* opt_soln *epw basement_regression_equation.m *pyc sim_errors.txt
