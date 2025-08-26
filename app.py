import pandas as pd
import streamlit as st
import os

st.set_page_config(page_title="FABU Data Explorer", layout="wide")
st.title("Collection Fabric Availability")

@st.cache_data(show_spinner=False)
def load_csv(path: str, mtime: float):
    return pd.read_csv(path)

CSV_PATH = "Collection Fabric Availability.csv"
df = load_csv(CSV_PATH, os.path.getmtime(CSV_PATH))

# ---------------- Sidebar controls ----------------
st.sidebar.header("Filters")

# Master_Collection
collections = sorted(df.get("Master_Collection", pd.Series(dtype=str)).dropna().astype(str).unique())
sel_collections = st.sidebar.multiselect("Master_Collection", options=collections, default=[])

# Department_Number
depts = sorted(df.get("Department_Number", pd.Series(dtype=str)).dropna().astype(str).unique())
sel_depts = st.sidebar.multiselect("Department_Number", options=depts, default=[])

# Fabric
fabrics = sorted(df.get("Fabric", pd.Series(dtype=str)).dropna().astype(str).unique())
sel_fabrics = st.sidebar.multiselect("Fabric", options=fabrics, default=[])

# Color_Code  (fixed options=colors)
colors = sorted(df.get("Color_Code", pd.Series(dtype=str)).dropna().astype(str).unique())
sel_colors = st.sidebar.multiselect("Color_Code", options=colors, default=[])

# Clear / Reload
if st.sidebar.button("Clear filters"):
    st.cache_data.clear()
    st.rerun()   # <- fixed

if st.sidebar.button("Reload data", type="primary"):
    st.cache_data.clear()
    st.rerun()

# ---------------- Apply filters ----------------
view = df.copy()
if sel_collections:
    view = view[view["Master_Collection"].astype(str).isin(sel_collections)]
if sel_depts:
    view = view[view["Department_Number"].astype(str).isin(sel_depts)]
if sel_fabrics:
    view = view[view["Fabric"].astype(str).isin(sel_fabrics)]
if sel_colors:
    view = view[view["Color_Code"].astype(str).isin(sel_colors)]

# ---------------- Output ----------------
st.write(f"Rows: {len(view):,} | Columns: {len(view.columns)}")
st.dataframe(view, use_container_width=True, height=560)
st.download_button("Download filtered CSV", view.to_csv(index=False).encode("utf-8"),
                   "export.csv", "text/csv")
