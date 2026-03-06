import yaml
from pathlib import Path
from collections import defaultdict
import re
import math
import streamlit as st

TRANSLATIONS = defaultdict(dict)
APP_LANGUAGES = set()

def read_yaml(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return next(yaml.safe_load_all(f))

def load_translations():
    lang_folders = [p for p in Path("translations").iterdir() if p.is_dir()]
    for folder in lang_folders:
        for f in folder.iterdir():
            if not f.name.endswith(".yaml"):
                continue
            TRANSLATIONS[folder.name].update(read_yaml(f))
    APP_LANGUAGES.update(TRANSLATIONS.keys())

    def t(s): 
        return translate(s, st.session_state.lang)

    def t_safe(s):
        try:
            return t(s)
        except:
            return "" if isinstance(s, str) and re.match(r"^[\w_]+(\.[\w_]+)+[\w_]+$", s) else s
    
    return t, t_safe

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
    "math": math,
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

def eval_expr(expr, identifier, qdata):
    if expr in [None, ""]:
        return None
    try:
        parsed = re.sub(r"\$([A-Za-z0-9_]+)", rf"qdata['\1']", expr)
        
        eval_globals = {
            "__builtins__": {},
            "qdata": qdata,
            **SAFE_BUILTINS,
        }
        
        return eval(parsed, eval_globals)
    except KeyError as e:
        raise KeyError(f"In {identifier}: {e.args[0]} is being used before it was defined: {expr}")
    except NameError as e:
        raise NameError(f"In {identifier}: {e.args[0]} (Did you forget a '$' before the variable name?): {expr}")
    except Exception as e:
        raise Exception(f"In {identifier}: Invalid expression: {expr}, {e}")
