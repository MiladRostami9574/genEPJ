
--https://stackoverflow.com/questions/36308801/sqlite3-pragma-synchronous-not-persistent
-- PRAGMAs apply only to the connection. NOT the database. Need to set in database.clj
PRAGMA journal_mode=WAL;
--PRAGMA journal_mode;
---- SB: fix 'database is locked' issue in clojure
--PRAGMA locking_mode; -- print existing setting
--PRAGMA locking_mode=EXCLUSIVE; -- Works with WAL
--PRAGMA busy_timeout;
--PRAGMA busy_timeout = 30000; -- in 'ms', ie. 30sec delay
--PRAGMA wal_checkpoint(PASSIVE); -- by default...
--PRAGMA synchronous = NORMAL; -- https://www.sqlite.org/pragma.html#pragma_synchronous

CREATE TABLE indiv (
    pkey INTEGER PRIMARY KEY,
    vmapkey INTEGER,
    runkey INTEGER,
    indiv   VARCHAR(200),
    keyvar   TEXT,
    sim_variables   TEXT,
    gen      INTEGER,
    heat     REAL,
    pk_heat  REAL,
    cool     REAL,
    pk_cool  REAL,
    light    REAL,
    dhw      REAL,
    fan      REAL,
    app      REAL,
    pv       REAL,
    fit      REAL,
    cvrmse,  REAL,
    min      INTEGER, -- BOOL Flag: 1 True, 0 False
    --apprxfit REAL DEFAULT -1000000000000000, -- SB: see comm.clj/nzeh.clj, get-prev-fit->(max apprxfit fit)
    apprxfit REAL DEFAULT 1000000000000000, -- SB: see comm.clj/nzeh.clj, get-prev-fit->(max apprxfit fit)
    ff REAL,
    sensfit  REAL,
    simtime  REAL,    -- Simulation Time in MIN
    eplustime  REAL,    -- Simulation Time in MIN
    -- mnth_pv TEXT, -- Breakdown of monthly PV generation
    -- pk_mnth_pv TEXT, -- Breakdown of monthly PV generation
    -- mnth_load TEXT, -- Breakdown of monthly LOAD consumption
    -- pk_mnth_load TEXT, -- Breakdown of monthly LOAD consumption
    -- mnth_hc TEXT, -- Breakdown of monthly HEATING/COOLING LOAD consumption
    -- pk_mnth_hc TEXT, -- Breakdown of monthly HEATING/COOLING LOAD consumption
    -- Utility Consumption/Demand and Cost
     elec_util_month       TEXT, -- Breakdown of monthly elec consumption
     ng_util_month        TEXT, -- Breakdown of monthly gas consumption
     dhwtr_util_month      TEXT, -- Breakdown of monthly water consumption
     elecdmd_util_month    TEXT, -- Breakdown of monthly elec demand
     elec_utilcst_month    TEXT, -- Breakdown of monthly elec cost
     elecdmd_utilcst_month TEXT, -- Breakdown of monthly demand cost
     ng_utilcst_month     TEXT, -- Breakdown of monthly gas cost
     dhwtr_utilcst_month   TEXT, -- Breakdown of monthly water cost
     ghg_monthly_total   TEXT, -- Breakdown of monthly GHG emisions
     ghg_annual_total   TEXT, -- Breakdown of monthly GHG emisions
     ghg_monthly_cost    TEXT, -- Breakdown of annual GHG cost     (as per federal tax policy/calculations)
     ghg_annual_cost   TEXT, -- Breakdown of annual GHG cost     (as per federal tax policy/calculations)
    -- STARTING INITIAL COSTS
    tot_inicst          REAL, -- Construction Costs, in $
    conscst             REAL, -- Construction Costs. Same as tot_inicst, in $
    maint_cst REAL, -- Maintenance Costs, in $
    pv_inicst REAL, -- Initial PV cost
    mech_inicst REAL, -- Initial mech cost
    light_inicst REAL, -- Initial lighting cost
    wall_inicst REAL, -- Initial wall cost
    infil_inicst REAL, -- Initial wall cost
    dhw_inicst REAL, -- Initial wall cost
    win_inicst REAL, -- Initial window cost
    plug_inicst REAL, -- Initial plug cost
    shd_inicst REAL, -- Initial shading cost
    -- END INITIAL COSTS
    -- START UTILITIES
    elec_utilcst REAL, --
    elecdmd_utilcst REAL, --
    ng_utilcst REAL, --
    dhwtr_utilcst REAL, --
    oper_utilcst REAL, --
    elec_util REAL, --
    elecdmd_util REAL, --
    ng_util REAL, --
    dhwtr_util REAL, --
    meters BLOB, -- Zipped meter file. Used for community optimization studies
    -- END UTILITIES
    unmet_heat_hrs REAL, --
    unmet_cool_hrs REAL, --
    mech_pkheat  REAL, -- Peak Mechanical Heating Sizing
    mech_pkcool  REAL, -- Peak Mechanical Cooling Sizing
    pvpk REAL, -- Peak PV kW output (approx @ STC)
    ecst REAL, -- Annual Energy Costs, assume % growth
    pvrev REAL, -- PV revenue from feed-in tariff
    co2 REAL, -- CO2/yr (operations, tonnes)
    co2cst REAL, -- CO2 tax, $/tonne
    npv REAL, -- Net Present Value of all the above
    apprxnpv REAL,
    cf_npvvec TEXT, -- Net Present Value of all the above
    cf_diff TEXT, -- Difference in NPVs (ref and prop)
    cf_cumsum TEXT, -- Cummulative sum of cf_diff. Shows payback
    cf_mrs TEXT, -- Cash flow for Maint, Replacement, Salvage. Need for community LCC
    irr REAL, -- IRR relative to reference building
    payback REAL, -- capital payback relative to reference building
    cbr REAL, -- Cost-Benefit ratio relative to reference building
    t_lc REAL, -- Time of life cycle
    elec_rate TEXT, -- Electricty rates used, on,mid,off peak
    pv_rebate REAL, -- PV intial cost rebate
    mort_rate REAL, -- Amortization rate
    pv_feedin REAL, -- PV Feed-in tariff
    count INTEGER, -- Number of times this entry is read
    eui_nopv  REAL,
    pktot_nopv  REAL,
    eui  REAL,
    area  REAL,
    elec_enduse TEXT, -- Electricity End-use breakdown 
    elec_enduse_cst TEXT, -- Electricity End-use breakdown 
    ng_enduse TEXT, -- NGas End-use breakdown 
    ng_enduse_cst TEXT, -- NGas End-use breakdown 
    elec_suite_frac TEXT, -- Breakdown of suite usage versus common area
    suite_frac TEXT, -- Breakdown of suite usage versus common area
    pktot  REAL,
    vulner    REAL,
    resil     REAL,
    robust    REAL,
    relia     REAL,
    LoFmax    REAL,
    t_decay   REAL,
    t_recov   REAL,
    t_outage  REAL,
    VoLL_kWh  REAL,
    VoLL_cost REAL,
    risk REAL,
    --datetime DATETIME--,
    datetime DATETIME
    --UNIQUE (indiv) -- This works, but a fit-eval will fail if <java.lang.Exception: transaction rolled back: column indiv is not unique> is thrown...
--  age TIME -- how old is the individual?  what run/gen was it last run (need memory of all previous runs too)?  First run, last run?
		-- Test using two debug terminals, create two populations and try and map-eval at the same time
);

-- Reduced order database made for Shawn Shi- Fri Mar  2 13:21:43 EST 2018
CREATE TABLE reduced (
    pkey INTEGER PRIMARY KEY,
    indiv   VARCHAR(200),
    keyvar   TEXT,
    fit      REAL,
    eui  REAL,
    eui_nopv  REAL,
    loads BLOB, -- Zipped meter file. Used for community optimization studies
    datetime CURRENT_TIMESTAMP
);

-- ** TRIGGER for datetime update **
CREATE TRIGGER insert_indiv_datetime AFTER INSERT ON indiv
BEGIN
  UPDATE indiv SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
END;
-- **
---- ** TRIGGER for datetime update **
--CREATE TRIGGER insert_reduced_datetime AFTER INSERT ON reduced
--BEGIN
--  UPDATE fit SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
--END;
---- **

-- -- ** TRIGGER for operational energy calc**
CREATE TRIGGER insert_indiv_oper_cost AFTER INSERT ON indiv
BEGIN
  UPDATE indiv SET oper_utilcst=elec_utilcst+elecdmd_utilcst+ng_utilcst+dhwtr_utilcst WHERE elec_utilcst = new.elec_utilcst OR elecdmd_utilcst=new.elecdmd_utilcst OR ng_utilcst=new.ng_utilcst OR dhwtr_utilcst=new.dhwtr_utilcst;
END;
-- **

---- -- ** TRIGGER for construction cost. Added for community LCC**
--CREATE TRIGGER insert_indiv_conscost AFTER INSERT ON indiv
--BEGIN
--  UPDATE indiv SET conscst=tot_inicst WHERE tot_inicst = new.tot_inicst;
--END;

---- -- ** TRIGGER for fitness calc**
--CREATE TRIGGER insert_indiv_fitness AFTER INSERT ON indiv
--BEGIN
--  UPDATE indiv SET apprxfit = fit WHERE fit = new.fit;
--END;
---- **


-- -- ** TRIGGER increment on INDIV for each data read; Set to 0 when started**
-- CREATE TRIGGER insert_indiv_fitness AFTER INSERT ON indiv
-- BEGIN
--   UPDATE indiv SET fit = heat+cool+light+dhw+fan+app+pv WHERE heat = new.heat;
-- END;
-- -- **

-- table for variable name mapping to greycode/value
CREATE TABLE vmap (
    pkey INTEGER PRIMARY KEY,
    varkey INTEGER, -- I can't see why this is necessary, used to initiate trigger only
    vmap TEXT, -- contains LISP indivsentation of all variable mappings
    rmap TEXT, -- contains LISP indivsentation of all RAW variable mappings
    sim TEXT, -- ex: ep5, esp14.3, ...
    kbmap TEXT, -- contains LISP indivsentation of all KEYWORD to LEN(BINARY) mappings for each allocated variable
    num INTEGER, -- total length of binary indivsentation
    datetime DATETIME,
    UNIQUE (varkey),
    UNIQUE (vmap),
    UNIQUE (rmap)
);

-- ** TRIGGER for datetime update **
CREATE TRIGGER insert_vmap_datetime AFTER INSERT ON vmap
BEGIN
  UPDATE vmap SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
END;
-- **
    
-- table for sub-population/population runs (individuals will refer to this) 
CREATE TABLE run (
    pkey INTEGER PRIMARY KEY,
    rkey INTEGER,
    vmapkey INTEGER, -- Associate run to variable mapping (vmap)
    datetime DATETIME,
    UNIQUE (rkey)
);

-- ** TRIGGER for datetime update **
CREATE TRIGGER insert_run_datetime AFTER INSERT ON run
BEGIN
  UPDATE run SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
END;
-- **

CREATE TABLE gen (
    pkey INTEGER PRIMARY KEY,
    runid INTEGER, -- Run ID (see run table)
    gen INTEGER, -- Generation Number
    data TEXT, -- ( ( 21 10 3 4 ...) (mASB ASB K mut-r mut-inc) )
    psize INTEGER, -- Population Size (intentionally redundant)
    datetime DATETIME
);

-- ** TRIGGER for datetime update **
CREATE TRIGGER insert_gen_datetime AFTER INSERT ON gen
BEGIN
  UPDATE gen SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
END;
-- **

-- ** Storage of each reverse gradient search (using start and reference indiv as a lookup). Returns the contents of fn build-best-order-stats.
-- ** TODO: ADD order of keys, relative to signifigance of rel fractions
-- ** TODO: ADD signifigance of rel fractions, which match order of keys
CREATE TABLE grad (
    pkey INTEGER PRIMARY KEY,
    vmapkey INTEGER, -- VarMap ID (see vmap table)
    genome VARCHAR(200), -- Genome in question. TODO: Relate this to indiv REF-ID
    refgen TEXT, -- Reference Genome
    best_order TEXT, -- "((varkeys) (fit-changes) (fits-per-var) (var-changes))"
    datetime DATETIME
);

-- ** TRIGGER for datetime update **
CREATE TRIGGER insert_grad_datetime AFTER INSERT ON grad
BEGIN
  UPDATE grad SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
END;
-- **

CREATE TABLE leed (
    pkey INTEGER PRIMARY KEY,
    indiv   VARCHAR(200),
    savings REAL, -- Savings over ASHRAE 90.1
    ener_savings REAL, -- Energy Savings over ASHRAE 90.1
    points REAL, -- LEED Points: Version 3
    datetime DATETIME
);
-- ** TRIGGER for datetime update **
CREATE TRIGGER insert_leed_datetime AFTER INSERT ON leed
BEGIN
  UPDATE leed SET datetime = DATETIME('NOW') WHERE pkey = new.pkey;
END;
-- **

.exit
