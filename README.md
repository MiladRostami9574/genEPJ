# genEPJ

Templates + tools for generating, modifying, and optimizing EnergyPlus models (IDF/epJSON) at scale. The library assembles HVAC/controls/templates, supports parametric and optimization workflows, and exposes metrics such as energy use, peak loads, GHGs, daylight, and life-cycle cost. See the eSim paper for background: [“genEPJ IBPSA eSim 2022”](https://publications.ibpsa.org/proceedings/esim/2022/papers/esim2022_205.pdf).

---

## What this library does

- **Template-driven model generation** for EnergyPlus using IDF and epJSON templates.
- **Programmatic edits** (add/modify/remove) to models via a structured API.
- **Checks & validation** for model suitability before running simulations.
- **Parametrics & optimization** via integration with `platypus` for multi-objective search.
- **Metrics pipeline** for energy/GHGs/daylight/LCC and more.

> Internals: key modules include `genEPJ/generate_EPJ.py` (orchestrates template changes) and `genEPJ/opti_EPJ.py` (glue to optimization workflows).
  
---

## Requirements

- **Python:** 3.x
- **EnergyPlus:** 9.x–25.x supported; default configuration targets **25.1.0**. Ensure `energyplus` is on your PATH.  
- **Python packages:** pinned in `requirements.txt` (install steps below).
- **Optional system tools (for certain workflows):**
  - `sqlite3` (DB logging for optimization runs)
  - Ruby + OpenStudio ModelKit (optional integration)

> See `requirements.txt` for Python deps; OS tools are listed there as comments.

---

## Installation

```bash
# 1) Clone
git clone https://gitlab.com/c5613/genEPJ.git
cd genEPJ

# 2) (Recommended) Create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Install Python dependencies
pip install -r requirements.txt

Quick start
1) Validate an EnergyPlus model
Use the standalone check script to confirm a model is suitable for genEPJ:

python genEPJ/standalone/check_model.py path/to/YourBuilding.idf
    The script will perform checks and can run interactively.

    Some checks assume access to an EPW file (default is Chicago O’Hare TMY3).

    Passing tests may require creating *_prep.idf files and running at least one simulation (to generate an EnergyPlus SQL database).

****2) Explore examples****
An examples directory is referenced for

**Usage (overview)**
The high-level pattern is:

     Prepare: start from a base IDF/epJSON and validate with check_model.py.

     Configure: specify EnergyPlus version, weather file, and tasks (template adds/mods).

     Generate: call the generation routine to materialize scenario(s) and, optionally, run EnergyPlus.

     Iterate: vary parameters for parametric studies or hook into the optimization workflow.

**Optimization (Platypus)**
For optimization studies, genEPJ/opti_EPJ.py provides:

Input handling via a JSON parameters file (e.g., sim/opti_inputs.json).

A workflow that writes per-run parameters, launches simulations (sim/startsim.sh), and logs results to db/data.db3.

Helper utilities to decode/encode candidate solutions and to compute fitness values (e.g., EUI).

Typical structure for opti runs: sim/ (scripts/templates) and db/ (SQLite).

genEPJ/
  ├─ generate_EPJ.py           # Orchestrates template-based changes & generation
  ├─ opti_EPJ.py               # Optimization glue (Platypus, sqlite logging)
  ├─ standalone/
  │   └─ check_model.py        # Model validation CLI
  ├─ pylib/                    # Template machinery, epJSON templater, helpers
  ├─ Modelkit/                 # (If present) OpenStudio ModelKit integration
examples/                      # Example setups and starter workflows
LICENSE

License
This project is licensed under MIT. See the LICENSE file.


