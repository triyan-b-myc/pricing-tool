import streamlit as st
import core.utils as ut
from core.debugger import render_debugger
import pandas as pd
import os
import yaml

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
    st.session_state.setdefault("lang", "en")
    st.session_state.setdefault("qdata", {})
init_st()

qdata:dict = st.session_state.qdata
t, t_safe = ut.load_translations()

#########################
# Global UI
#########################
st.logo("assets/logo.png", size="large", link="https://www.myclimate.org")

#########################
# Questionnaire
#########################
questionnaire = ut.load_questionnaire()

@st.dialog(t("questionnaire.export"))
def export_preset():
    values = {question_id: qdata[question_id] for section_id in questionnaire for question_id in questionnaire[section_id]}
    export_data = yaml.dump(values, sort_keys=False, allow_unicode=False)
    
    with st.container(horizontal=True, vertical_alignment="bottom"):
        export_name = st.text_input(t("questionnaire.export_name"))
        st.text(".yaml")
        st.download_button(":material/save:", help=t("questionnaire.export_download"), data=export_data, file_name=f"{export_name}.yaml", disabled=len(export_name) == 0)
    with st.container(height=300, border=False):
        st.code(export_data, language="yaml")

with st.sidebar:
    title_col, lang_col = st.columns([70, 30])
    with title_col:
        st.title(t("questionnaire.title"))
    with lang_col:
        st.radio(t("ui.language.title"), ut.APP_LANGUAGES, key="lang", horizontal=True)
    
    st.info(t("questionnaire.description"))

    with st.container(horizontal=True, vertical_alignment="center"):
        preset = st.file_uploader(t("questionnaire.import"), type="yaml", max_upload_size=1)
        st.button(":material/cloud_download:", key="export_preset", help=t("questionnaire.export"), on_click=export_preset)
    
    if preset is not None:
        preset_data = yaml.safe_load(preset)
        for section_id in questionnaire:
            for question_id in questionnaire[section_id]:
                 qdata[question_id] = preset_data[question_id]  

    for section_id in questionnaire:
        st.divider()
        st.subheader(f"{t(f"questionnaire.sections.{section_id}.title")}")
        is_empty_section = True

        for question_id, question in questionnaire[section_id].items():        
            var_name = f"questionnaire.sections.{section_id}.qs.{question_id}.required_if"
            if ut.eval_expr(question.get("required_if"), var_name, qdata) == False:
                qdata[question_id] = None
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
                        index=qdata.get(question_id),
                        help=qhelp
                    )
                    else:
                        value = st.pills(
                            qtext,
                            options=list(range(len(opts_display))),
                            format_func=lambda i: opts_display[i],
                            help=qhelp,
                            default=qdata.get(question_id)
                        )
                case "num_slider":
                    min_val, max_val, step_val, start_val = tuple(int(i) for i in question["slider"].split(":"))
                    value = st.slider(qtext, min_val, max_val, qdata.get(question_id, start_val), step_val, help=qhelp)
                case _:
                    continue

            qdata[question_id] = value
        
        if is_empty_section:
            st.write(t("questionnaire.empty_section"))


#########################
# Logic & display
#########################
logic = ut.load_pricing_logic()
for var_name in logic:
    qdata[var_name] = ut.eval_expr(logic[var_name], var_name, qdata)

if os.getenv("MYC_APP_ENV") != "PROD":
    with st.container(horizontal=True, vertical_alignment="center"):
        st.button("", icon=":material/refresh:", key="debug_reload")
        toggle_debug = st.toggle("Debugger", value=True, key="debug_toggle")
    if toggle_debug:
        render_debugger(logic, qdata)

col1, col2, col3 = st.columns([3, 3, 1])
with col1: st.metric(t("ui.C20.title"), qdata.get("C20"), help=t("ui.C20.description"))
with col2: st.metric(t("ui.C21.title"), qdata.get("C21"), help=t("ui.C21.description"))
with col3: st.metric(t("ui.margin_year1.title"), qdata.get("margin_year1"))

for table in ut.load_output_tables():
    st.subheader(t(table["title"]))
    df_table = pd.DataFrame(
        [map(lambda expr: ut.eval_expr(expr, t(table["title"]), qdata), row["data"]) for row in table["rows"] if ut.eval_expr(row.get("required_if", 'True'), table["title"], qdata)],
        columns=t(table["columns"])
    )
    df_table = df_table.map(t_safe)
    df_table = df_table.style.format(precision=2)
    df_table = df_table.apply(lambda row: ["color: black; " + table["rows"][row.name].get("style", "")] * len(row), axis=1)
    st.dataframe(df_table, hide_index=True)
