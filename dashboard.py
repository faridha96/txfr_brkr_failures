import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Asset Risk & Failure Dashboard",
    layout="wide"
)

st.title("Asset Risk & Failure Dashboard")

# ==========================================================
# FILE UPLOAD
# ==========================================================

uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is None:
    st.info("Upload a CSV or Excel file to begin.")
    st.stop()


@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


df = load_data(uploaded_file)

# ==========================================================
# COLUMN MAPPING
# ==========================================================

st.sidebar.header("Column Mapping")

def get_default_index(possible_names):
    lower_cols = [c.lower() for c in df.columns]

    for name in possible_names:
        if name.lower() in lower_cols:
            return lower_cols.index(name.lower())

    return 0


asset_col = st.sidebar.selectbox(
    "Asset Type Column",
    df.columns,
    index=get_default_index(
        ["asset", "asset_type", "equipment_type"]
    )
)

line_col = st.sidebar.selectbox(
    "Line Column",
    df.columns,
    index=get_default_index(
        ["line", "line_type"]
    )
)

risk_col = st.sidebar.selectbox(
    "Risk Bucket Column",
    df.columns,
    index=get_default_index(
        ["risk", "risk_bucket"]
    )
)

age_col = st.sidebar.selectbox(
    "Failure Indicator Column",
    df.columns
)

date_col = st.sidebar.selectbox(
    "Date Column",
    df.columns,
    index=get_default_index(
        ["date", "failure_date", "event_date"]
    )
)

asset_id_col = st.sidebar.selectbox(
"Asset ID Column",
df.columns
)

# ==========================================================
# DATA CLEANING
# ==========================================================

working_df = df.copy()

working_df[asset_col] = (
    working_df[asset_col]
    .astype(str)
    .str.upper()
    .str.strip()
)

working_df[line_col] = (
    working_df[line_col]
    .astype(str)
    .str.upper()
    .str.strip()
)

working_df[risk_col] = (
    working_df[risk_col]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
    .str.zfill(2)
)

working_df[age_col] = pd.to_numeric(
    working_df[age_col],
    errors="coerce"
)

working_df[date_col] = pd.to_datetime(
    working_df[date_col],
    errors="coerce"
)


# ==========================================================
# CREATE POF / COF
# ==========================================================

working_df["POF"] = pd.to_numeric(
    working_df[risk_col].str[0],
    errors="coerce"
)

working_df["COF"] = pd.to_numeric(
    working_df[risk_col].str[1],
    errors="coerce"
)

working_df = working_df[
    working_df["POF"].between(1, 5)
    &
    working_df["COF"].between(1, 5)
]

if working_df.empty:
    st.error(
        "No valid risk buckets found. "
        "Risk values must be between 11 and 55."
    )
    st.stop()

# ==========================================================
# FILTERS
# ==========================================================

st.sidebar.header("Dashboard Filters")

# --------------------------
# DATE RANGE
# --------------------------

working_df["Failure_Year"] = pd.to_datetime(
    working_df[date_col],
    errors="coerce"
).dt.year

available_years = sorted(
    working_df["Failure_Year"]
    .dropna()
    .unique()
)

selected_years = st.sidebar.multiselect(
    "Failure Years",
    available_years,
    default=available_years
)

# --------------------------
# ASSET FILTER
# --------------------------

available_assets = sorted(
    working_df[asset_col]
    .dropna()
    .unique()
    .tolist()
)

selected_assets = st.sidebar.multiselect(
    "Asset Type",
    options=available_assets,
    default=available_assets
)

# --------------------------
# LINE FILTER
# --------------------------

available_lines = sorted(
    working_df[line_col]
    .dropna()
    .unique()
    .tolist()
)

selected_lines = st.sidebar.multiselect(
    "Line Type",
    options=available_lines,
    default=available_lines
)

# ==========================================================
# APPLY FILTERS
# ==========================================================

filtered_df = working_df[
    working_df[asset_col].isin(
        selected_assets
    )
]

filtered_df = filtered_df[
    filtered_df[line_col].isin(
        selected_lines
    )
]

if filtered_df.empty:
    st.warning(
        "No records found after applying filters."
    )
    st.stop()

# ==========================================================
# DATASETS
# ==========================================================

brkr_df = filtered_df[
    filtered_df[asset_col] == "BRKR"
]

txfr_df = filtered_df[
    filtered_df[asset_col] == "TXFR"
]

# ==========================================================
# KPI BAR
# ==========================================================

if selected_years:
    st.caption(
        f"Selected Failure Years: "
        f"{min(selected_years)} - {max(selected_years)}"
    )
else:
    st.caption("No Failure Years Selected")

filtered_asset_count = (
    filtered_df[asset_id_col]
    .nunique()
)

brkr_count = (
    brkr_df[asset_id_col]
    .nunique()
)

txfr_count = (
    txfr_df[asset_id_col]
    .nunique()
)

failure_records = filtered_df[
    filtered_df[age_col].notna()
]

failure_records = failure_records[
    failure_records["Failure_Year"]
    .isin(selected_years)
]

total_failures = len(failure_records)

failure_rate = (
    total_failures / filtered_asset_count * 100
    if filtered_asset_count > 0
    else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Filtered Assets",
    f"{filtered_asset_count:,}"
)

k2.metric(
    "BRKR Assets",
    f"{brkr_count:,}"
)

k3.metric(
    "TXFR Assets",
    f"{txfr_count:,}"
)

k4.metric(
    "Total Failures",
    f"{int(total_failures):,}"
)

k5.metric(
    "Failures per Asset",
    f"{failure_rate:.2f}%"
)

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def create_asset_matrix(data):

    unique_assets = (
        data[
            [
                asset_id_col,
                "POF",
                "COF"
            ]
        ]
        .drop_duplicates()
    )

    matrix = pd.crosstab(
        unique_assets["POF"],
        unique_assets["COF"]
    )

    matrix = matrix.reindex(
        index=range(1, 6),
        columns=range(1, 6),
        fill_value=0
    )

    return matrix

def create_failure_matrix(data):

    matrix = pd.crosstab(
        data["POF"],
        data["COF"]
    )

    matrix = matrix.reindex(
        index=range(1, 6),
        columns=range(1, 6),
        fill_value=0
    )

    return matrix


def plot_heatmap(
    matrix,
    title,
    colorscale
):

    fig = px.imshow(
        matrix,
        text_auto=True,
        color_continuous_scale=colorscale,
        aspect="auto",
        labels={
            "x": "COF Bucket",
            "y": "POF Bucket",
            "color": "Count"
        }
    )

    fig.update_layout(
        title=title,
        height=550
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================================
# TABS
# ==========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "BRKR",
        "TXFR",
        "Failure Analysis"
    ]
)

# ==========================================================
# BRKR TAB
# ==========================================================

with tab1:

    st.subheader(
        "Circuit Breakers (BRKR)"
    )

    if brkr_df.empty:

        st.warning(
            "No BRKR assets found."
        )

    else:

        brkr_matrix = create_asset_matrix(
            brkr_df
        )

        plot_heatmap(
            brkr_matrix,
            "BRKR Count by POF / COF Bucket",
            "Blues"
        )

        st.markdown(
            "#### Asset Count Matrix"
        )

        st.dataframe(
            brkr_matrix,
            use_container_width=True
        )

        st.markdown(
            "#### Filtered BRKR Assets"
        )

        st.dataframe(
            brkr_df.drop_duplicates(
                subset=[asset_id_col]
            ),
            use_container_width=True
        )

# ==========================================================
# TXFR TAB
# ==========================================================

with tab2:

    st.subheader(
        "Transformers (TXFR)"
    )

    if txfr_df.empty:

        st.warning(
            "No TXFR assets found."
        )

    else:

        txfr_matrix = create_asset_matrix(
            txfr_df
        )

        plot_heatmap(
            txfr_matrix,
            "TXFR Count by POF / COF Bucket",
            "Greens"
        )

        st.markdown(
            "#### Asset Count Matrix"
        )

        st.dataframe(
            txfr_matrix,
            use_container_width=True
        )

        st.markdown(
            "#### Filtered TXFR Assets"
        )

        st.dataframe(
            txfr_df.drop_duplicates(
                subset=[asset_id_col]
            ),
            use_container_width=True
        )

# ==========================================================
# FAILURE TAB
# ==========================================================

with tab3:

    st.subheader(
        "Failure Analysis"
    )

    failure_df = filtered_df[
        filtered_df[age_col].notna()
    ].copy()

    failure_df = failure_df[
        failure_df["Failure_Year"]
        .isin(selected_years)
    ]


    if failure_df.empty:

        st.warning(
            "No failure records found."
        )

    else:

        failure_matrix = (
            create_failure_matrix(
                failure_df
            )
        )

        plot_heatmap(
            failure_matrix,
            "Failure Count by POF / COF Bucket",
            "Reds"
        )

        st.markdown(
            "#### Failure Count Matrix"
        )

        st.dataframe(
            failure_matrix,
            use_container_width=True
        )

        bucket_summary = (
    failure_df
    .groupby(risk_col)
    .size()
    .reset_index(name="Failure Count")
)       

        total_bucket_failures = (
            bucket_summary["Failure Count"]
            .sum()
        )

        bucket_summary["Failure %"] = (
            bucket_summary["Failure Count"]
            / total_bucket_failures
            * 100
        ).round(2)

        bucket_summary = (
            bucket_summary
            .sort_values(
                "Failure Count",
                ascending=False
            )
        )

        st.markdown(
            "#### Failure Distribution by Bucket"
        )

        st.dataframe(
            bucket_summary,
            use_container_width=True
        )

        st.markdown(
            "#### Failure Records"
        )

        st.dataframe(
            failure_df,
            use_container_width=True
        )