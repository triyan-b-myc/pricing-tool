import streamlit as st
import pandas as pd
import re
from functools import cache
import random
from streamlit_agraph import agraph, Node, Edge, Config

agraph_config = Config(from_json="config.json")

def get_dependency_tree(var_name:str, logic:dict):
    @cache
    def _get_dependency_tree(var):
        expr = logic.get(var)
        if not expr:
            return {var: []}
       
        # Get unique dependencies, preserving order
        dependencies = list(dict.fromkeys(re.findall(r"\$([A-Za-z0-9_]+)", expr)))
        if var_name in dependencies:
            return {f"Circular dependency {var_name} and {var}": []} 
        else:
            return {var: [_get_dependency_tree(d) for d in dependencies]}
    return _get_dependency_tree(var_name)


def set_debug_var(var):
    st.session_state.debug_var = var
    st.session_state["debug_grid"]["selection"] = {}

def render_dependency_tree(dependencies, qdata, d=0):
    for dep in dependencies:
        var, child_deps = next(iter(dep.items()))
        val_str = str(qdata.get(var))
        val_str_trunc = val_str[:30] + "..." if len(val_str) >= 30 else val_str

        with st.container(horizontal=True):
            icon = None if len(child_deps) == 0 else \
                    f":material/counter_{len(child_deps)}:" if len(child_deps) < 10 else \
                    ":material/add_circle:"
            with st.expander(f"**{var}** ({val_str_trunc})", expanded=False, icon=icon):
                render_dependency_tree(child_deps, qdata, d+1)
                if len(child_deps) == 0:
                    st.text(val_str)
            st.button(
                ":material/visibility:",
                help="View variable",
                key=f"debug_{var}_{random.randbytes(16)}",
                on_click=set_debug_var, args=[var]
            )


def render_dependency_graph(tree, qdata):
    nodes = {}
    edges = []
    global max_node_name_len
    max_node_name_len = 150
    def get_nodes_and_edges(node, parent_name=None):
        global max_node_name_len
        name, children = next(iter(node.items()))
        if name not in nodes:
            val_str = str(qdata.get(name))
            val_str_trunc = val_str[:30] + "..." if len(val_str) >= 30 else val_str 
            nodes[name] = Node(id=name, title=f"{name} ({val_str_trunc})",  label=name, shape="box", color="#E6007E" if not parent_name else None)
            max_node_name_len = max(max_node_name_len, 8*len(name))
        if parent_name:
            edges.append(Edge(source=parent_name, target=name, color=None))
        for child_node in children:
            get_nodes_and_edges(child_node, name)

    get_nodes_and_edges(tree)
    nodes = list(nodes.values())
    agraph_config.layout["hierarchical"]["nodeSpacing"] = max_node_name_len
    print(max_node_name_len)
    return agraph(nodes, edges, agraph_config)
    

def render_debugger(logic:dict, qdata:dict): 

    df_data_explorer =  pd.DataFrame.from_records(
        [[str(k), str(v), str(logic.get(k))] for k, v in qdata.items()],
        columns=["Variable", "Value", "Expression"],
    )

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        event = st.dataframe(
            df_data_explorer,
            key="debug_grid",
            height=700,
            hide_index=True,
            selection_mode="single-row",
            on_select=lambda: None
        )

    selected = next(iter(event["selection"].get("rows", [])), None)
    var = df_data_explorer.iloc[selected, 0] if selected is not None else st.session_state.get("debug_var")
    st.session_state.debug_var = var

    with col2:
        ct = st.container(border=True, height="stretch")
        ct.subheader("No variable selected" if var is None else var, text_alignment="center", width="stretch")
        if var is None:
            return

        with ct.container(height=600, border=False):
            st.segmented_control("Show dependecies as", ["Tree", "Graph"], default="Graph", key="debug_dep_representation")
            with st.expander("Value", expanded=True):
                val = qdata.get(var)
                st.markdown(f"**Type: {type(val).__name__}**")
                st.markdown(f"{val}")
            with st.expander("Expression", expanded=True):
                st.code(logic.get(var))
            
            dg = get_dependency_tree(var, logic)
            if st.session_state.debug_dep_representation == "Tree":
                with st.expander("Dependency tree", expanded=True):
                    render_dependency_tree(dg[var], qdata)
            else:
                with st.expander("Dependency graph", expanded=True):
                    info_ph = st.empty()
                    selected = render_dependency_graph(dg, qdata)
                    with info_ph.container(horizontal=True, vertical_alignment="center"):
                        st.button(
                            ":material/visibility:",
                            help="View selected variable",
                            key=f"debug_graph_{selected}_{random.randbytes(16)}",
                            disabled=selected is None,
                            on_click=set_debug_var, args=[selected]
                        )
                        if selected is not None and selected in qdata:
                            val = qdata.get(selected)
                            val_str = str(qdata.get(selected))
                            val_str_trunc = val_str[:30] + "..." if len(val_str) >= 30 else val_str
                            st.write(f"**{selected}: {val.__class__.__name__}**")
                            st.write(val_str_trunc)
    