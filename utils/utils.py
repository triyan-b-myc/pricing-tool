import yaml
import os
import re
import math

TRANSLATIONS = {}
APP_LANGUAGES = set()

def read_yaml(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return next(yaml.safe_load_all(f))

def load_translations():
    translations_dir = "translations"
    for filename in os.listdir(translations_dir):
        if not filename.endswith(".yaml"):
            continue
        lang = filename.split(".")[0]
        TRANSLATIONS[lang] = read_yaml(f"{translations_dir}/{filename}")
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

def evaluate_expr(expr, qdata):
    if expr in [None, ""]:
        return None
    try:
        parsed = re.sub(r"\$([A-Za-z0-9_]+)", rf"qdata.get('\1')", expr)
        return eval(parsed, {"qdata": qdata, "math": math})
    except NameError:
        raise Exception(f"Invalid reference (Did you forget a '$' before the variable name?): {expr}")
    except Exception as e:
        raise Exception(f"Invalid expression: {expr}, {parsed}, {e}")