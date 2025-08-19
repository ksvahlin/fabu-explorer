import pandas as pd
import streamlit as st

st.set_page_config(page_title="FABU Data Explorer", layout="wide")
st.title("FABU Data Explorer")

# Load the CSV that lives in the repo
df = pd.read_csv("ks_fabu.csv")

# Basic interactivity
with st.expander("Filters", expanded=True):
    cols = st.multiselect("Columns to show", df.columns.tolist(), default=list(df.columns))
    q = st.text_input("Quick contains filter")
view = df[cols]
if q:
    mask = view.astype(str).apply(lambda s: s.str.contains(q, case=False, na=False))
    view = view[mask.any(axis=1)]

st.write(f"Rows: {len(view):,}  |  Columns: {len(view.columns)}")
st.dataframe(view, use_container_width=True, height=520)
st.download_button("Download filtered CSV", view.to_csv(index=False).encode(), "export.csv", "text/csv")
