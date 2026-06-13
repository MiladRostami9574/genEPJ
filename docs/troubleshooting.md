# genEPJ troubleshooting

## FileNotFoundError: templates_9.0.1.json

This error means that genEPJ could not locate the epJSON template resource used
by the epJSON templating utilities. In the revised package, the file is included
as package data at:

```text
genEPJ/templateGenerator_epJSON/templates_9.0.1.json
```

Recommended fix from a fresh clone:

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pytest tests/test_installation.py -q
python -m genEPJ.standalone.check_model examples/sim-tinyhome/nomad_3RV96.idf
```

On Windows PowerShell, use backslashes for the final path:

```powershell
python -m genEPJ.standalone.check_model examples\sim-tinyhome\nomad_3RV96.idf
```

If the test still fails, confirm that the repository was cloned completely and
that the `genEPJ/templateGenerator_epJSON/` directory is present.

## EnergyPlus-related checks fail

The lightweight smoke check does not require EnergyPlus. The detailed check with
`--full` does require EnergyPlus and weather files. Confirm that the following
environment variables are set:

```text
ENERGYPLUS_DIR
ENERGYPLUS_WEATHER
```

Also confirm that the selected EPW file has a corresponding DDY file in the
weather directory.

## Optional Modelkit or OpenStudio checks fail

Modelkit and OpenStudio are optional integrations. A fresh installation can be
imported and smoke-tested without them. Install these tools only when running
workflows that explicitly require them.
