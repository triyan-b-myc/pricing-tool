import yaml
from pathlib import Path
from collections import defaultdict
import re
import math

TRANSLATIONS = defaultdict(dict)
APP_LANGUAGES = set()

def read_yaml(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return next(yaml.safe_load_all(f))

def load_translations():
    lang_folders = [p for p in Path("translations").iterdir() if p.is_dir()]
    for lf in lang_folders:
        for f in lf.iterdir():
            if not f.name.endswith(".yaml"):
                continue
            TRANSLATIONS[lf.name].update(read_yaml(f))
    APP_LANGUAGES.update(TRANSLATIONS.keys())

def translate(path:str, lang): 
    value = TRANSLATIONS[lang]
    for p in path.split("."):
        try:
            value = value[p]
        except KeyError:
            raise KeyError(f"Could not find translation in {lang} for '{path}'")
    return value

def load_questionnaire() -> dict[dict]:
    return read_yaml("input/questionnaire.yaml")

def load_pricing_logic() -> dict:
    files_to_load = read_yaml("logic/_init.yaml")
    logic = {}
    for filename in files_to_load:
        logic.update(read_yaml(f"logic/{filename}"))
    return logic

def load_output_tables() -> dict:
    return read_yaml("output/tables.yaml")

# Safe built-in functions for expressions
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}

def eval_expr(expr, qdata):
    if expr in [None, ""]:
        return None
    try:
        parsed = re.sub(r"\$([A-Za-z0-9_]+)", rf"qdata.get('\1')", expr)
        
        eval_globals = {
            "__builtins__": {},
            "qdata": qdata,
            "math": math,
            **SAFE_BUILTINS,
        }
        
        return eval(parsed, eval_globals)
    except NameError as e:
        raise Exception(f"{e.args[0]} (Did you forget a '$' before the variable name?): {expr}")
    except Exception as e:
        raise Exception(f"Invalid expression: {expr}, {parsed}, {e}")