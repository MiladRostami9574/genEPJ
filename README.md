# genEPJ

genEPJ is an open-source Python library for generating, modifying, and
organizing EnergyPlus model variants in IDF and epJSON formats. It supports
reproducible workflows for parametric analysis, optimization, and resilience
studies by applying reusable functions, templates, and task files to a common
base model.

## Main capabilities

- Template-driven EnergyPlus model generation in IDF and epJSON workflows.
- Programmatic model edits for envelope, HVAC, schedules, controls, renewable
  systems, storage, and simulation-output objects.
- Task-based model generation for preparatory, reference, proposed, and
  optimized cases.
- Parametric and optimization workflows using JSON-defined input variables.
- Resilience-oriented workflows, including outage-event and control-strategy
  scenario generation.
- Installation smoke tests and a tiny-home demonstration model for fresh setups.

## Requirements

- Python 3.9 or newer.
- EnergyPlus is required for full simulation workflows. The installation smoke
  tests do not require EnergyPlus.
- Optional external tools are required only for specific integrations, such as
  OpenStudio, Modelkit, Ruby, and SQLite-based optimization logging.

## Windows installation from a fresh clone

Open PowerShell and run the following commands:

```powershell
git clone https://github.com/MiladRostami9574/genEPJ.git
cd genEPJ

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .[dev]

python -m pytest tests/test_installation.py -q
python -m genEPJ.standalone.check_model examples\sim-tinyhome\nomad_3RV96.idf
```

The last command runs a lightweight installation smoke check. It confirms that
`genEPJ` imports correctly, the packaged `templates_9.0.1.json` file is found,
and the tiny-home IDF model can be parsed.

## macOS/Linux installation from a fresh clone

```bash
git clone https://github.com/MiladRostami9574/genEPJ.git
cd genEPJ

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .[dev]

python -m pytest tests/test_installation.py -q
python -m genEPJ.standalone.check_model examples/sim-tinyhome/nomad_3RV96.idf
```

## Optional Nix development shell

A Nix flake is provided as a secondary reproducibility route for users who use
Nix. From the repository root, run:

```bash
nix develop
python -m pip install -e .[dev]
python -m pytest tests/test_installation.py -q
```

## Running the detailed model check

The default `check_model` command is intentionally lightweight so that users can
verify installation on Windows without requiring EnergyPlus weather files or
simulation outputs. To run the legacy detailed model validation, use `--full`:

```powershell
python -m genEPJ.standalone.check_model examples\sim-tinyhome\nomad_3RV96.idf --full --epw CAN_ON_Ottawa.716280_CWEC.epw
```

The full check requires:

- `ENERGYPLUS_DIR` set to the EnergyPlus installation directory.
- `ENERGYPLUS_WEATHER` set to the directory containing EPW and DDY files.
- The EPW and corresponding DDY file named in `--epw`.
- Any project output files required by the detailed validation.

## Tiny-home demonstration example

The reviewer-facing example is located at:

```text
examples/sim-tinyhome/
```

Important files are:

- `nomad_3RV96.idf`: base EnergyPlus model.
- `Nomad_genEPJ.py`: example genEPJ workflow.
- `opti_inputs.json`: sample JSON input variables.

A Jupyter notebook walkthrough is provided at:

```text
notebooks/01_windows_tinyhome_demo.ipynb
```

## Troubleshooting

See `docs/troubleshooting.md` for common installation and path issues, including
the `FileNotFoundError: templates_9.0.1.json` issue that can occur when package
data are not installed correctly.

## Repository structure

```text
genEPJ/
  generate_EPJ.py                  # Core generation and modification utilities
  opti_EPJ.py                      # Optimization workflow utilities
  resources.py                     # Package-data resource helpers
  standalone/check_model.py        # Windows-safe smoke check and full check CLI
  pylib/                           # Template and IDF/epJSON helper modules
  templateGenerator_epJSON/        # Packaged epJSON template resource
examples/
  sim-tinyhome/                    # Reviewer-facing demonstration example
notebooks/
  01_windows_tinyhome_demo.ipynb   # Step-by-step notebook demonstration
tests/
  test_installation.py             # Installation smoke tests
  test_energyplus_available.py     # Optional EnergyPlus availability test
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.
