import pandas as pd
import numpy as np
import streamlit as st
import re
from datetime import datetime, date

st.set_page_config(page_title="FABU Data Explorer", layout="wide")
st.title("Collection Fabric Availability")

CSV_PATH = "Collection Fabric Availability.csv"

# ---------- Data ----------
@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # try to infer datetimes (non-destructive: only converts columns that look like dates)
    for c in df.columns:
        if df[c].dtype == object:
            try_dt = pd.to_datetime(df[c], errors="coerce", utc=False, infer_datetime_format=True)
            # convert only if there are enough valid datetimes (avoid false positives)
            if try_dt.notna().sum() >= max(5, int(0.5 * len(df))):
                df[c] = try_dt.dt.tz_localize(None)  # ensure naive timestamps
    return df

df = load_csv(CSV_PATH)

# ---------- Helpers ----------
def is_datetime(s: pd.Series) -> bool:
    return np.issubdtype(s.dtype, np.datetime64)

def build_text_filter(col_name: str, series: pd.Series):
    st.write(f"**{col_name}**  _(text)_")
    col1, col2 = st.columns([2,1])
    with col1:
        q = st.text_input(f"Contains (case-insensitive) — {col_name}", key=f"txt_{col_name}", label_visibility="collapsed")
    with col2:
        regex = st.checkbox("Regex", key=f"rgx_{col_name}")
    return ("text", q, regex)

def build_categorical_filter(col_name: str, series: pd.Series, max_multiselect=200):
    st.write(f"**{col_name}**  _(category)_")
    vals = series.dropna().astype(str).unique()
    vals.sort()
    if len(vals) <= max_multiselect:
        chosen = st.multiselect(f"Values — {col_name}", options=vals, default=[], key=f"cat_{col_name}", label_visibility="collapsed")
        return ("cat", chosen)
    else:
        # fallback to text contains if too many uniques
        q = st.text_input(f"Contains — {col_name}", key=f"cat_txt_{col_name}", label_visibility="collapsed")
        return ("cat_txt", q)

def build_numeric_filter(col_name: str, series: pd.Series):
    st.write(f"**{col_name}**  _(number)_")
    s = pd.to_numeric(series, errors="coerce")
    s_non_na = s.dropna()
    if s_non_na.empty:
        st.caption("No numeric values found.")
        return ("num_none", None)
    min_v, max_v = float(s_non_na.min()), float(s_non_na.max())
    step = (max_v - min_v) / 100.0 if max_v > min_v else 1.0
    lo, hi = st.slider(f"Range — {col_name}", min_value=min_v, max_value=max_v, value=(min_v, max_v),
                       step=step, key=f"num_{col_name}", label_visibility="collapsed")
    include_na = st.checkbox("Include blanks/NaN", value=True, key=f"num_na_{col_name}")
    return ("num", (lo, hi, include_na))

def build_date_filter(col_name: str, series: pd.Series):
    st.write(f"**{col_name}**  _(date)_")
    s = pd.to_datetime(series, errors="coerce")
    s_non_na = s.dropna()
    if s_non_na.empty:
        st.caption("No valid dates found.")
        return ("dt_none", None)
    min_d, max_d = s_non_na.min().date(), s_non_na.max().date()
    start, end = st.date_input(f"Between — {col_name}", (min_d, max_d), min_value=min_d, max_value=max_d,
                               key=f"dt_{col_name}", label_visibility="collapsed")
    include_na = st.checkbox("Include blanks/NaT", value=True, key=f"dt_na_{col_name}")
    # Ensure tuple
    if isinstance(start, date) and isinstance(end, date):
        return ("dt", (start, end, include_na))
    else:
        # If user clears selection, fallback to full range
        return ("dt", (min_d, max_d, include_na))

def apply_filters(df_in: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df_in.copy()
    for col, spec in filters.items():
        kind = spec[0]
        if kind == "text":
            q, regex = spec[1], spec[2]
            if q:
                try:
                    out = out[out[col].astype(str).str.contains(q, case=False, na=False, regex=regex)]
                except re.error:
                    # If regex invalid, fall back to literal contains
                    out = out[out[col].astype(str).str.contains(q, case=False, na=False, regex=False)]
        elif kind == "cat":
            chosen = spec[1]
            if chosen:
                out = out[out[col].astype(str).isin(chosen)]
        elif kind == "cat_txt":
            q = spec[1]
            if q:
                out = out[out[col].astype(str).str.contains(q, case=False, na=False)]
        elif kind == "num":
            lo, hi, include_na = spec[1]
            s = pd.to_numeric(out[col], errors="coerce")
            mask = s.between(lo, hi)
            if include_na:
                mask = mask | s.isna()
            out = out[mask]
        elif kind == "dt":
            start, end, include_na = spec[1]
            s = pd.to_datetime(out[col], errors="coerce")
            mask = (s.dt.date >= start) & (s.dt.date <= end)
            if include_na:
                mask = mask | s.isna()
            out = out[mask]
        # *_none kinds apply nothing
    return out

# ---------- UI ----------
with st.expander("Filters", expanded=True):
    left, right = st.columns([2, 1])

    with left:
        # Per-column filters inside a form (apply at once)
        with st.form("col_filters", clear_on_submit=False):
            st.subheader("Per-column filters", divider="gray")
            filters = {}
            for col in df.columns:
                with st.container(border=True):
                    s = df[col]
                    if is_datetime(s):
                        filters[col] = build_date_filter(col, s)
                    elif pd.api.types.is_numeric_dtype(s):
                        filters[col] = build_numeric_filter(col, s)
                    else:
                        # Decide between categorical and free text
                        nun = s.nunique(dropna=True)
                        if nun <= 50:
                            filters[col] = build_categorical_filter(col, s, max_multiselect=200)
                        else:
                            filters[col] = build_text_filter(col, s)
            col_f_applied = st.form_submit_button("Apply filters")

    with right:
        st.subheader("Global tools", divider="gray")
        # Column chooser
        default_cols = list(df.columns)
        show_cols = st.multiselect("Columns to show", df.columns.tolist(), default=default_cols)
        # Quick search across *visible* columns
        q_global = st.text_input("Quick contains (all visible columns)")

        if st.button("Clear all filters"):
            st.cache_data.clear()  # not required, but keeps things tidy
            st.experimental_rerun()

# ---------- Filtering logic ----------
view = df.copy()

# apply per-column filters when the form is submitted; on first load, apply with defaults
view = apply_filters(view, filters if 'filters' in locals() else {})

# apply global quick filter on the columns chosen to display (done after per-column filters)
if q_global:
    sub = view[show_cols] if show_cols else view
    mask = sub.astype(str).apply(lambda s: s.str.contains(q_global, case=False, na=False))
    view = view[mask.any(axis=1)]

# choose visible columns
if show_cols:
    view = view[show_cols]

# ---------- Output ----------
st.write(f"Rows: {len(view):,}  |  Columns: {len(view.columns)}")
st.dataframe(view, use_container_width=True, height=560)

st.download_button(
    "Download filtered CSV",
    view.to_csv(index=False).encode("utf-8"),
    "export.csv",
    "text/csv"
)

