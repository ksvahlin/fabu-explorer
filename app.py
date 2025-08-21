import pandas as pd
import streamlit as st

st.set_page_config(page_title="FABU Data Explorer", layout="wide")
st.title("Collection Fabric Availability")

CSV_PATH = "Collection Fabric Availability.csv"

@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

df = load_csv(CSV_PATH)

# ---------------- Sidebar controls ----------------
st.sidebar.header("Filters")

# Multi-select like Excel filter for Master_Collection
if "Master_Collection" in df.columns:
    collections = sorted(df["Master_Collection"].dropna().astype(str).unique())
    sel_collections = st.sidebar.multiselect(
        "Master_Collection",
        options=collections,
        default=[],
        help="Pick one or more collections to include"
    )
else:
    sel_collections = []

# Multi-select like Excel filter for Department_Number
if "Department_Number" in df.columns:
    depts = sorted(df["Department_Number"].dropna().astype(str).unique())
    sel_depts = st.sidebar.multiselect(
        "Department_Number",
        options=depts,
        default=[],
        help="Pick one or more Departments to include"
    )
else:
    sel_depts = []

# Multi-select like Excel filter for Fabric
if "Fabric" in df.columns:
    fabrics = sorted(df["Fabric"].dropna().astype(str).unique())
    sel_fabrics = st.sidebar.multiselect(
        "Fabric",
        options=fabrics,
        default=[],
        help="Pick one or more Fabrics to include"
    )
else:
    sel_fabrics = []

# Global quick search (across visible columns)
q_global = st.sidebar.text_input("Quick contains (all visible columns)", "")

# Column chooser
show_cols = st.sidebar.multiselect(
    "Columns to show",
    options=list(df.columns),
    default=list(df.columns),
)

# Clear button
if st.sidebar.button("Clear filters"):
    sel_collections = []
    q_global = ""
    show_cols = list(df.columns)
    st.experimental_rerun()

# ---------------- Apply filters ----------------
view = df.copy()

if sel_collections:
    view = view[view["Master_Collection"].astype(str).isin(sel_collections)]

if q_global:
    sub = view[show_cols] if show_cols else view
    mask = sub.astype(str).apply(lambda s: s.str.contains(q_global, case=False, na=False))
    view = view[mask.any(axis=1)]

if show_cols:
    view = view[show_cols]

# ---------------- Output ----------------
st.write(f"Rows: {len(view):,} | Columns: {len(view.columns)}")
st.dataframe(view, use_container_width=True, height=560)

st.download_button(
    "Download filtered CSV",
    view.to_csv(index=False).encode("utf-8"),
    "export.csv",
    "text/csv"
)
