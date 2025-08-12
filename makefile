HOST=127.0.0.1
TEST_PATH=./

# PHONY: Tell Makefile that these are tests, not files
.PHONY: clean-pyc clean-build init test

init:
	virtualenv -p /usr/bin/python venv
	./venv/bin/pip install -r  requirements.txt
	echo "source venv/bin/activate"
	#pip install -r requirements.txt

test:
	py.test tests


clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

#isort:
#	sh -c "isort --skip-glob=.tox --recursive . "
#
#lint:
#	flake8 --exclude=.tox

test: clean-pyc
	py.test --verbose --color=yes $(TEST_PATH)

#docker-run:
#	docker build \
#	  --file=./Dockerfile \
#	  --tag=my_project ./
#	docker run \
#	  --detach=false \
#	  --name=my_project \
#	  --publish=$(HOST):8080 \
#	  my_project
#

#paper:
#	@echo "	Making JOSS paper"
#	docker run --rm \
#	    --volume $PWD/paper:/data \
#	    --user $(id -u):$(id -g) \
#	    --env JOURNAL=joss \
#	    openjournals/paperdraft

help:
	@echo "	clean-pyc"
	@echo "		Remove python artifacts."
	@echo "	clean-build"
	@echo "		Remove build artifacts."
	@echo "	isort"
	@echo "		Sort import statements."
	@echo "	lint"
	@echo "		Check style with flake8."
	@echo "	test"
	@echo "		Run py.test"
	@echo '	run'
	@echo '		Run the `my_project` service on your local machine.'
	@echo '	docker-run'
	@echo '		Build and run the `my_project` service in a Docker container.'

doc: doc-clean
	pdoc3 -f --html genEPJ

doc-clean:
	rm -rf html/genEPJ

clean:
	rm -rf __pycache__ genEPJ/__pycache__ genEPJ/pylib/__pycache__ genEPJ/Modelkit/__pycache__ temp/EPSchematic/test/__pycache__

cleanall: clean
	rm -rf venv

copy:
	rm -rf /tmp/$(notdir $(CURDIR)) /tmp/$(notdir $(CURDIR)).tar.gz
	-cp -avL  ../$(notdir $(CURDIR)) /tmp/
	cd /tmp/$(notdir $(CURDIR)) && rm -rf venv rubybkup_.gem_ruby_2.6.0 results paper compile_paper.sh temp __pycache__ jupyter/{Untitled.ipynb,.ipynb_checkpoints} .pytest_cache examples/sim-tinyhome/genEPJ examples/opti/{genEPJ,opti_inputs.json,startsim.sh,sim,LOGS_Modelkit.txt} data
	cd /tmp/$(notdir $(CURDIR))/examples/sim-tinyhome && ln -s ../../genEPJ .
	cd /tmp/$(notdir $(CURDIR))/examples/opti && ln -s ../sim-tinyhome sim && ln -s ../sim-tinyhome/{genEPJ,opti_inputs.json,startsim.sh} .

# Push code to GitLab (main branch)
push-git:
	@git push -u origin main
