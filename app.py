import streamlit as st
import utils.utils as ut
import pandas as pd
import os
import re

#########################
# Setup
#########################
print("-"*50)
def init_st():
    st.set_page_config(
        layout="wide",
        initial_sidebar_state=475,
        page_title="Pricing Tool",
        page_icon=":material/functions:"
    )
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "qdata" not in st.session_state:
        st.session_state.qdata = {}
init_st()
ut.load_translations()
questionnaire = ut.load_questionnaire()
logic = ut.load_pricing_logic()

def t(s): 
    return ut.translate(s, st.session_state.lang)

def t_safe(s):
    try:
        return t(s)
    except:
        return "" if isinstance(s, str) and re.match(r"^[\w_]+(\.[\w_]+)+[\w_]+$", s) else s

qdata:dict = st.session_state.qdata

#########################
# Global UI
#########################
st.logo("assets/logo.png", size="large", link="https://www.myclimate.org")
if os.getenv("MYC_APP_ENV") != "PROD":
    st.button("Reload", key="debug_reload")

#########################
# Questionnaire
#########################
with st.sidebar:
    title_col, lang_col = st.columns([70, 30])
    with title_col:
        st.title(t("questionnaire.title"))
    with lang_col:
        st.radio(t("ui.language.title"), ut.APP_LANGUAGES, key="lang", horizontal=True)
    
    st.info(t("questionnaire.description"))
    
    for section_id in questionnaire:
        st.divider()
        st.subheader(f"{t(f"questionnaire.sections.{section_id}.title")}")
        is_empty_section = True

        for question_id, question in questionnaire[section_id].items():        
            if ut.eval_expr(question.get("required_if"), qdata) == False:
                qdata.pop(question_id, None)
                continue
            is_empty_section = False

            qtext = f"{question_id}: {t(f"questionnaire.sections.{section_id}.qs.{question_id}.text")}"
            try: qhelp = t(f"questionnaire.sections.{section_id}.qs.{question_id}.description")
            except: qhelp = None

            match question["type"]:
                case "text":
                    value = st.text_input(qtext, value=qdata.get(question_id, ""), help=qhelp)
                case "select":
                    opts_display = t(question["options"])
                    if len("".join(opts_display)) > 60:
                        value = st.selectbox(
                        qtext,
                        options=list(range(len(opts_display))),
                        format_func=lambda i: opts_display[i],
                        index=None,
                        help=qhelp
                    )
                    else:
                        value = st.pills(
                            qtext,
                            options=list(range(len(opts_display))),
                            format_func=lambda i: opts_display[i],
                            help=qhelp
                        )
                case "num_slider":
                    min_val, max_val, step_val, start_val = tuple(int(i) for i in question["slider"].split(":"))
                    value = st.slider(qtext, min_val, max_val, start_val, step_val, help=qhelp)
                case _:
                    continue

            qdata[question_id] = value
        
        if is_empty_section:
            st.write(t("questionnaire.empty_section"))


#########################
# Logic & display
#########################
for var_name in logic:
    qdata[var_name] = ut.eval_expr(logic[var_name], qdata)

col1, col2, col3 = st.columns([3, 3, 1])
with col1: st.metric(t("ui.C20.title"), qdata.get("C20"), help=t("ui.C20.description"))
with col2: st.metric(t("ui.C21.title"), qdata.get("C21"), help=t("ui.C21.description"))
with col3: st.metric("Margin Year 1 (CHF)", qdata.get("margin_year1"))

with st.expander(t("ui.data_explorer.title")):
    st.write(t("ui.data_explorer.description"))
    df_data_explorer =  pd.DataFrame.from_dict(
        {k: [str(v), logic.get(k)] for k, v in qdata.items()},
        columns=[t("ui.data_explorer.col_value"), t("ui.data_explorer.col_expr")],
        orient="index"
    )
    st.dataframe(df_data_explorer)

for table in ut.load_output_tables():
    st.subheader(t(table["title"]))
    df_table = pd.DataFrame(
        [map(lambda expr: ut.eval_expr(expr, qdata), row["data"]) for row in table["rows"] if ut.eval_expr(row.get("required_if", 'True'), qdata)],
        columns=t(table["columns"])
    )
    df_table = df_table.map(t_safe)
    df_table = df_table.style.format(precision=2)
    df_table = df_table.apply(lambda row: ["color: black; " + table["rows"][row.name].get("style", "")] * len(row), axis=1)
    st.dataframe(df_table, hide_index=True)
