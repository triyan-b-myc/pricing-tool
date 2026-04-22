# Pricing Tool Documentation

This repository implements a *low‑code* pricing calculator for the myclimate offering.  
All questions, calculations and the way results are presented are driven by YAML
configuration files. The only Python code required to run the tool focuses on
loading data, evaluating expressions and rendering a Streamlit user interface.

Because the logic is edited as plain text, people who are not familiar with
programming can add or adapt questionnaires, cost formulas and output tables;
developers can extend functionality by adding new helpers or validators.

## Overview

```
pricing-tool/
├── app.py                           # Main application code
├── core/
│   ├── __init__.py                  # Core module initialization
│   ├── utils.py                     # I/O and expression evaluator
│   └── debugger.py                  # Interactive debugger for logic variables
├── input/
│   └── questionnaire.yaml           # Definition of the user questions
├── logic/
│   ├── _init.yaml                   # load order for logic files
│   ├── constants.yaml               # constant/lookup values
│   ├── cost_components.yaml         # Cost logic
│   ├── summary_aufwand_h.yaml       # More cost logic
│   └── …                            # future logic may be split in additional files
├── output/
│   └── tables.yaml                  # layout of the summary / detailed tables
├── translations/                    # translations
├── assets/                          # images, logos, etc.
└── config.json                      # Configuration for debugger graph
```

The page is initialised by app.py which:

1. sets the page configuration and session state,
2. loads translations, questionnaire, pricing logic and output tables through
   helper functions in core/utils.py,
3. renders the sidebar where the user answers questions, and
4. evaluates every expression defined in the logic files against the collected
   answers (`qdata`).

Variables follow the naming convention `QUESTIONID_costcomponent` where
`QUESTIONID` is e.g. `C4` and `costcomponent` is any of the identifiers listed
in constants.yaml. Most of the complicated formulas appear in
cost_components.yaml; the summary file aggregates them into modules A–F
and the various output keys that the tables in tables.yaml reference.


## Configuration files

### Questionnaire

Each section and question is declared in questionnaire.yaml.  
Example entry:

```yaml
C4:
  type: num_slider
  slider: "1:75:1:1"
  required_if: "$B1 in [0, 2]"
```

* `type` controls the widget (`text`, `select`, `num_slider`).
* `options` may refer to a translation key, e.g. `options.yes_no`.
* `required_if` is a boolean expression evaluated against the current `qdata`.
  A hidden question is removed from the session state.

The UI generator in app.py converts the YAML into Streamlit widgets.  
Translations for question text and descriptions are kept in the language files.

### Logic

Logic is split into several files but merged at runtime.

* constants.yaml defines fixed numbers and lookup tables
* cost_components.yaml contains the main decision tree; the value of any
  variable may be an expression using `$`‑prefixed references, Python syntax
  and previously defined variables.  For example:

  ```yaml
  c4_liz_ia_adv: |
    $c4_s3_basis_lizenz_adv + $c4_s3_standort_lizenz_adv if $Z4 == 0 else \
    $c4_ec_basis_lizenz_adv if $Z4 == 1 else \
    0
  ```

  The file is organised by question blocks (e.g. `### C4`) to make it easier to
  navigate.

* summary_aufwand_h.yaml computes aggregates, converts hours to days/costs
  and calculates margins.  It also builds lists of component totals that the
  output tables consume.

A logical variable is evaluated once; later expressions can reference it by
name.  The evaluation engine in core/utils.py performs a regular‑expression
substitution to turn `$VAR` into `qdata.get('VAR')` and then executes the
resulting Python code in a restricted namespace (`qdata`, `math`).

### Output tables

tables.yaml defines which rows appear in the summary and detailed
tables, the order of columns, the style for individual rows and optional
`required_if` conditions.  Each value in the row may be an expression; the
application evaluates them before rendering.

Translations for titles, column headers and terminology are managed under the
`output:` key in the language files.

## Debugger

The application includes an interactive debugger accessible via an expandable section in the UI. It allows users to:

- Browse all variables and their current values and expressions.
- Visualize dependency trees and graphs for any variable.
- Inspect individual variables in detail, including their types and full values.

The debugger uses `streamlit-agraph` for graph visualization, configured via `config.json`.

## Translation

The folder translations contains one YAML file per language.  The helper
`translate(path, lang)` traverses the nested dictionaries.  Languages present
in the directory are automatically registered (`APP_LANGUAGES`).

## Adding or extending logic

To adapt the pricing tool you do **not** need to touch Python code.  follow
these steps:

1. **Question or option**
   * Insert a new question under an existing (or new) section in
     questionnaire.yaml.
   * Provide a translation string for its text and description in each language
     file.
   * If it is a `select`, add the corresponding option list under `options:`.

2. **Logic variable**
   * Add expressions to cost_components.yaml or another file listed in
     `_init.yaml`.  Prefer grouping by question or feature.
   * Use `$QUESTIONID` to refer to answers; use previously computed variables by
     name.  Multi‑line expressions should be given as `|`‑quoted blocks.

3. **Constants / helper functions**
   * If you require a constant value, insert it into constants.yaml.
   * You may define a new lambda helper; for example:

     ```yaml
     fn_square: 'lambda x: x * x'
     ```

     and then use `$fn_square($C4)` elsewhere.

4. **Output**
   * Modify tables.yaml to display new variables.  Add rows, change
     titles, or add `required_if` clauses.
   * Update translation files for any new output labels.

5. **Re‑evaluation**
   * The application recalculates every expression on each interaction, so no
     refresh or restart is required.
### Tips

* Keep naming consistent: use lowercase with underscores for computed
  variables, prefix them with the question when appropriate.
* When a formula becomes complex, consider adding intermediate variables for
  clarity.
* Use the `debugger` (expandable section in the UI) to inspect current
  values, expressions, and dependency trees/graphs; it is invaluable for debugging.
* If you add dependencies between questions (e.g. `required_if` conditions),
  remember to handle the case where the answered value is removed from
  `qdata`.

## Running the application

Install the requirements (Streamlit, PyYAML, pandas, …) and start the app:

```cmd
pip install -r requirements.txt
streamlit run app.py
```

The sidebar contains the questionnaire; once answers are provided the computed
metrics `C20` and `C21` appear, followed by the tables and the debugger section.

## Developer notes

* core/utils.py is the main Python module used by application logic.  It
  handles YAML loading and expression evaluation.
* core/debugger.py provides an interactive debugger for exploring logic variables and their dependencies.
* The evaluation context deliberately exposes only `qdata` and `math` to
  minimise unintended side effects.
* The project is intentionally lightweight to ease maintenance by
  non‑programmers.

By keeping the bulk of the business rules in YAML, the pricing tool is both
transparent and extensible.  New contributors can add services or adjust
calculations without writing code; developers can extend the engine when more
complexity is required.