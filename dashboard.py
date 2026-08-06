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


asset_id_col = st.sidebar.selectbox(
"Asset ID Column",
df.columns
)


pof_value_col = st.sidebar.selectbox(
    "POF Value Column",
    df.columns
)


risk_col = st.sidebar.selectbox(
    "Risk Bucket Column",
    df.columns,
    index=get_default_index(
        ["risk", "risk_bucket"]
    )
)

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


age_col = st.sidebar.selectbox(
    "Failure Indicator Column",
    df.columns
)


failure_type_col = st.sidebar.selectbox(
    "Failure Type Column",
    df.columns
)



date_col = st.sidebar.selectbox(
    "Date Column",
    df.columns,
    index=get_default_index(
        ["date", "failure_date", "event_date"]
    )
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

working_df[failure_type_col] = (
    working_df[failure_type_col]
    .astype(str)
    .str.strip()
    .str.upper()
    .str.replace("IN-SERVICE FAILURE", "FAILURE")
)

working_df[failure_type_col] = (
    working_df[failure_type_col]
    .replace(["NAN", "NONE"], pd.NA)
)

working_df[pof_value_col] = pd.to_numeric(
    working_df[pof_value_col].astype(float),
    errors="coerce",
    downcast ="float"
)

# ==========================================================
# CREATE POF / COF
# ==========================================================

working_df["POF"] = pd.to_numeric(
    working_df[risk_col].str[0],
    errors="coerce"
)

# ==========================================================
# POF RANGE BUCKETS
# ==========================================================
working_df[pof_value_col] = pd.to_numeric(
working_df[pof_value_col].astype(float),
errors="coerce",
    downcast ="float"
)

# Create quantiles and capture bins
_, bins = pd.qcut(
working_df[pof_value_col],
q=3,
retbins=True,
duplicates="drop"
)
# Build labels from actual bin edges
range_labels = [
f"{bins[i]:.3f} - {bins[i+1]:.3f}"
for i in range(len(bins) - 1)
]
# Create ordered categorical ranges
working_df["POF_Range"] = pd.qcut(
working_df[pof_value_col],
q=len(range_labels),
labels=range_labels,
duplicates="drop"
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

def create_risk_distribution(data):

    summary = (
        data[[asset_id_col, "POF"]]
        .drop_duplicates()
        .groupby("POF")
        .size()
        .reset_index(name="Asset Count")
    )

    summary = summary.set_index("POF")

    summary = summary.reindex(
        range(1, 6),
        fill_value=0
    )

    summary = summary.reset_index()

    summary["Percent"] = (
        summary["Asset Count"]
        /
        summary["Asset Count"].sum()
        * 100
    ).round(2)

    return summary

def create_risk_bucket_summary(data):

    summary = (
        data[[asset_id_col, "POF"]]
        .drop_duplicates()
        .groupby("POF")
        .size()
        .reset_index(name="Asset Count")
    )

    summary = summary.set_index("POF").reindex(
        range(1, 6),
        fill_value=0
    )

    return summary.reset_index()

def create_failure_matrix(data):

    matrix = pd.crosstab(
        data["POF"],
        data[failure_type_col]
    )

    matrix = matrix.reindex(
        index=range(1, 6),
        fill_value=0
    )

    return matrix


def plot_failure_heatmap(matrix, title):

    total = matrix.values.sum()

    labels = matrix.copy().astype(str)

    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):

            count = matrix.iloc[r, c]

            pct = (
                count / total * 100
                if total > 0 else 0
            )

            labels.iloc[r, c] = (
                f"{count}<br>{pct:.1f}%"
            )

    fig = px.imshow(
        matrix,
        color_continuous_scale="Reds",
        aspect="auto"
    )

    fig.update_traces(
        text=labels.values,
        texttemplate="%{text}"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Failure Type",
        yaxis_title="Risk Bucket"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


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


def create_quantile_heatmap_data(data):
    temp = (
    data[
    [
    asset_id_col,
    "POF",
    "POF_Range"
    ]
    ]
    .dropna(subset=["POF_Range"])
    )
    matrix = pd.crosstab(
    temp["POF"],
    temp["POF_Range"]
    )
    # Force risk buckets 1-5
    matrix = matrix.reindex(
    index=[1, 2, 3, 4, 5],
    fill_value=0
    )
    # Force column order to match actual POF ranges
    matrix = matrix.reindex(
    columns=range_labels,
    fill_value=0
    )
    return matrix

def plot_quantile_heatmap(matrix, title):

    total = matrix.values.sum()

    labels = matrix.copy().astype(str)

    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):

            cnt = matrix.iloc[r, c]

            pct = (
                cnt / total * 100
                if total > 0
                else 0
            )

            labels.iloc[r, c] = (
                f"{cnt}<br>{pct:.1f}%"
            )

    fig = px.imshow(
        matrix,
        color_continuous_scale="Blues",
        aspect="auto"
    )

    fig.update_traces(
        text=labels.values,
        texttemplate="%{text}"
    )

    fig.update_layout(
        title=title,
        xaxis_title="POF Quartile",
        yaxis_title="Risk Bucket"
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

        brkr_summary = create_risk_distribution(
            brkr_df
        )

        fig = px.bar(
            brkr_summary,
            x="POF",
            y="Asset Count",
            text="Asset Count",
            title="BRKR Risk Bucket Distribution"
        )

        st.markdown("### Risk Bucket vs POF Quartile")

        brkr_heatmap = create_quantile_heatmap_data(
            brkr_df
        )

        plot_quantile_heatmap(
            brkr_heatmap,
            "BRKR Risk Bucket vs POF Quartile"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            brkr_summary,
            use_container_width=True
        )


        st.dataframe(
            brkr_heatmap,
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

        txfr_summary = create_risk_distribution(
            txfr_df
        )

        fig = px.bar(
            txfr_summary,
            x="POF",
            y="Asset Count",
            text="Asset Count",
            title="TXFR Risk Bucket Distribution"
        )

        st.markdown("### Risk Bucket vs POF Quartile")

        txfr_heatmap = create_quantile_heatmap_data(
            txfr_df
        )

        plot_quantile_heatmap(
            txfr_heatmap,
            "TXFR Risk Bucket vs POF Quartile"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            txfr_summary,
            use_container_width=True
        )



        st.dataframe(
            txfr_heatmap,
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

        failure_matrix = pd.crosstab(
            failure_df["POF"],
            failure_df[failure_type_col]
        )

        failure_matrix = failure_matrix.reindex(
            index=[1, 2, 3, 4, 5],
            fill_value=0
        )

        total_failures = failure_matrix.values.sum()

        labels = failure_matrix.copy().astype(str)

        for i in range(failure_matrix.shape[0]):
            for j in range(failure_matrix.shape[1]):

                cnt = failure_matrix.iloc[i, j]

                pct = (
                    cnt / total_failures * 100
                    if total_failures > 0
                    else 0
                )

                labels.iloc[i, j] = (
                    f'Count: {cnt}<br>Percentage: {pct:.1f}%'
                )

        fig = px.imshow(
            failure_matrix,
            color_continuous_scale="Reds",
            aspect="auto"
        )

        fig.update_traces(
            text=labels.values,
            texttemplate="%{text}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown("### Failure Risk Bucket vs POF Quartile")

        failure_heatmap = create_quantile_heatmap_data(
                    failure_df
                )

        plot_quantile_heatmap(
                    failure_heatmap,
                    "Failure Risk Bucket vs POF Quartile"
                )


        # ===========================================
        # FAILURE RATE BY POF BUCKET
        # ===========================================

        # Total assets in each bucket
        asset_bucket_counts = (
            filtered_df[[asset_id_col, "POF"]]
            .drop_duplicates()
            .groupby("POF")
            .size()
            .reset_index(name="Asset Count")
        )

        # Total failures in each bucket
        failure_bucket_counts = (
            failure_df
            .groupby("POF")
            .size()
            .reset_index(name="Failure Count")
        )

        # Merge together
        failure_rate_table = pd.merge(
            asset_bucket_counts,
            failure_bucket_counts,
            on="POF",
            how="left"
        )

        failure_rate_table["Failure Count"] = (
            failure_rate_table["Failure Count"]
            .fillna(0)
            .astype(int)
        )

        # Calculate failure rate
        failure_rate_table["Failure Rate (%)"] = (
            failure_rate_table["Failure Count"]
            /
            failure_rate_table["Asset Count"]
            * 100
        ).round(2)

        # Ensure all buckets 1-5 appear
        failure_rate_table = (
            failure_rate_table
            .set_index("POF")
            .reindex(range(1, 6), fill_value=0)
            .reset_index()
        )

        st.markdown("### Failure Rate by Risk Bucket")

        st.dataframe(
            failure_rate_table,
            use_container_width=True
        )


        failure_summary = (
            failure_df
            .groupby(
                ["POF", failure_type_col]
            )
            .size()
            .reset_index(name="Count")
        )

        failure_summary["Percent"] = (
            failure_summary["Count"]
            /
            failure_summary["Count"].sum()
            * 100
        ).round(2)

        st.dataframe(
            failure_summary,
            use_container_width=True
        )


        st.dataframe(
            failure_heatmap,
            use_container_width=True)