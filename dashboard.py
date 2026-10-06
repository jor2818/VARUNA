import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="VARUNA Traffic Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for Streamlit adhering to DESIGN.md (Cal.com Design System)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #111111;
    }
    
    .stApp {
        background-color: #ffffff;
    }
    
    .main-header {
        font-family: 'Cal Sans', 'Inter', sans-serif;
        font-size: 2.25rem;
        font-weight: 600;
        color: #111111;
        letter-spacing: -1px;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    
    .db-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        font-size: 0.85rem;
        font-weight: 600;
        color: #111111;
        background-color: #f5f5f5;
        border: 1px solid #e5e7eb;
        border-radius: 9999px;
        margin-bottom: 1rem;
    }
    
    /* Cal.com Card Styling */
    div[data-testid="stMetricValue"] {
        font-family: 'Cal Sans', 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #111111 !important;
        letter-spacing: -1px !important;
    }
    
    .stMetric {
        background-color: #f5f5f5 !important;
        padding: 1.25rem !important;
        border-radius: 12px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: none !important;
    }
    
    /* Primary Action Buttons */
    .stButton > button {
        background-color: #111111 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #111111 !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.15s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #242424 !important;
        border-color: #242424 !important;
        color: #ffffff !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# Database Configurations
DB_MAP = {
    "mb": {
        "name": "Mid-Block Traffic Counts (MB)",
        "file": "MB_traffic_counts_database.db",
        "icon": "🚦",
        "description": "Mid-Block road section traffic counting stations"
    },
    "utc": {
        "name": "U-Turn Traffic Counts (UTC)",
        "file": "UTC_traffic_counts_database.db",
        "icon": "🔄",
        "description": "U-turn intersection traffic counting stations"
    }
}

# 2. Database Selector in Sidebar
st.sidebar.header("🗄️ Database Selector")

# Parse query parameter if provided from Flask UI
url_db = st.query_params.get("db", "mb").lower().strip()
if url_db not in DB_MAP:
    url_db = "mb"

selected_db_key = st.sidebar.radio(
    "Active Database Dataset",
    options=list(DB_MAP.keys()),
    index=0 if url_db == "mb" else 1,
    format_func=lambda k: f"{DB_MAP[k]['icon']} {DB_MAP[k]['name']}",
    help="Select between Mid-Block (MB) and U-Turn (UTC) traffic counting databases"
)

active_db_info = DB_MAP[selected_db_key]
db_path = os.path.join(os.path.dirname(__file__), active_db_info['file'])

# 3. Cached Data Loading Function
@st.cache_data(ttl=600)
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"Database file not found at {file_path}")
        return pd.DataFrame()

    conn = sqlite3.connect(file_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(imports)")
    import_cols = [col[1] for col in cur.fetchall()]

    road_type_expr = "i.road_type" if "road_type" in import_cols else "'N/A' as road_type"

    query = f"""
        SELECT 
            c.id as count_id,
            c.interval_start,
            c.interval_end,
            c.vehicle_type,
            c.count,
            {road_type_expr},
            i.direction,
            i.period,
            s.station_code
        FROM counts c
        JOIN imports i ON c.import_id = i.id
        JOIN stations s ON i.station_id = s.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Parse datetime columns
    df['interval_start'] = pd.to_datetime(df['interval_start'])
    df['interval_end'] = pd.to_datetime(df['interval_end'])
    df['hour'] = df['interval_start'].dt.hour
    df['date'] = df['interval_start'].dt.date

    return df

# Load data into DataFrame
with st.spinner(f"Loading {active_db_info['name']}..."):
    df_raw = load_data(db_path)

if df_raw.empty:
    st.warning(f"No data found in database {active_db_info['file']}.")
    st.stop()

# Header Area
st.markdown(f'<div class="main-header">{active_db_info["icon"]} VARUNA Traffic Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<div class="db-badge">Active Dataset: {active_db_info["name"]} ({active_db_info["file"]})</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{active_db_info["description"]}</div>', unsafe_allow_html=True)

# 4. Sidebar Filters
st.sidebar.markdown("---")
st.sidebar.header("🔍 Data Filters")

# Day Type / Period Filter (WD vs WE)
st.sidebar.subheader("📆 Period / Day Type")
period_options = ["WD", "WE"]
period_labels = {"WD": "Weekday (WD)", "WE": "Weekend (WE)"}

selected_periods = st.sidebar.multiselect(
    "Select Period",
    options=period_options,
    default=period_options,
    format_func=lambda x: period_labels.get(x, x),
    help="Filter counts by Weekday (WD) or Weekend (WE) traffic files"
)

# Vehicle Type Filter
all_vehicle_types = sorted(df_raw['vehicle_type'].unique().tolist())
selected_vehicles = st.sidebar.multiselect(
    "Vehicle Type",
    options=all_vehicle_types,
    default=all_vehicle_types,
    help="Select one or multiple vehicle categories"
)

# Station Code Filter
all_stations = sorted(df_raw['station_code'].unique().tolist())
selected_stations = st.sidebar.multiselect(
    "Station Code",
    options=all_stations,
    default=all_stations,
    help="Select counting stations"
)

# Date/Time Range Filter
min_dt = df_raw['interval_start'].min().to_pydatetime()
max_dt = df_raw['interval_end'].max().to_pydatetime()

st.sidebar.subheader("📅 Date & Time Range")
date_range = st.sidebar.slider(
    "Select Interval Range",
    min_value=min_dt,
    max_value=max_dt,
    value=(min_dt, max_dt),
    format="YYYY-MM-DD HH:mm"
)

# Road Type & Direction Filters
with st.sidebar.expander("Additional Filters (Road & Direction)"):
    all_road_types = sorted(df_raw['road_type'].dropna().unique().tolist())
    selected_road_types = st.multiselect("Road Type", options=all_road_types, default=all_road_types)
    
    all_directions = sorted(df_raw['direction'].dropna().unique().tolist())
    selected_directions = st.multiselect("Direction", options=all_directions, default=all_directions)

# 5. Filter DataFrame according to user selection
filtered_df = df_raw[
    (df_raw['period'].isin(selected_periods)) &
    (df_raw['vehicle_type'].isin(selected_vehicles)) &
    (df_raw['station_code'].isin(selected_stations)) &
    (df_raw['road_type'].isin(selected_road_types)) &
    (df_raw['direction'].isin(selected_directions)) &
    (df_raw['interval_start'] >= date_range[0]) &
    (df_raw['interval_end'] <= date_range[1])
]

# Display Warning if empty
if filtered_df.empty:
    st.warning("No records match your selected filters. Please adjust the sidebar filter options.")
    st.stop()

# 6. Top KPI Metrics Row
col1, col2, col3, col4 = st.columns(4)

total_vehicles = filtered_df['count'].sum()
avg_per_interval = filtered_df['count'].mean()
peak_row = filtered_df.loc[filtered_df['count'].idxmax()] if not filtered_df.empty else None
distinct_stations_count = filtered_df['station_code'].nunique()

with col1:
    st.metric(
        label="Total Vehicles (Filtered)",
        value=f"{total_vehicles:,.0f}"
    )

with col2:
    st.metric(
        label="Active Stations Selected",
        value=f"{distinct_stations_count} / {len(all_stations)}"
    )

with col3:
    st.metric(
        label="Average Count / 15-Min",
        value=f"{avg_per_interval:.1f}"
    )

with col4:
    peak_val = f"{peak_row['count']:,}" if peak_row is not None else "0"
    peak_type = peak_row['vehicle_type'].replace('_', ' ').title() if peak_row is not None else "N/A"
    st.metric(
        label="Peak Single Interval",
        value=peak_val,
        delta=f"Class: {peak_type}"
    )

st.markdown("---")

# 7. Tabbed View for Charts and Raw Data Table
tab_charts, tab_data, tab_summary = st.tabs(["📊 Visual Analytics", "📋 Data Explorer", "ℹ️ Station Insights"])

# Plotly theme matching Cal.com palette (#111111, #374151, #e5e7eb)
PLOTLY_THEME_COLORS = ['#111111', '#374151', '#6b7280', '#9ca3af', '#d1d5db']

with tab_charts:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("1. Vehicle Type Distribution")
        vehicle_summary = filtered_df.groupby('vehicle_type')['count'].sum().reset_index()
        vehicle_summary['vehicle_type_clean'] = vehicle_summary['vehicle_type'].str.replace('_', ' ').str.title()
        vehicle_summary = vehicle_summary.sort_values(by='count', ascending=True)

        fig_bar = px.bar(
            vehicle_summary,
            x='count',
            y='vehicle_type_clean',
            orientation='h',
            labels={'count': 'Total Vehicle Count', 'vehicle_type_clean': 'Vehicle Category'},
            color_discrete_sequence=['#111111'],
            text_auto=',.0f'
        )
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            height=420,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.subheader("2. Traffic Volume Over Time")
        time_summary = filtered_df.groupby('interval_start')['count'].sum().reset_index()

        fig_line = px.line(
            time_summary,
            x='interval_start',
            y='count',
            labels={'interval_start': 'Time Interval', 'count': 'Total Vehicles'},
            line_shape='spline',
            markers=True
        )
        fig_line.update_traces(line_color='#111111', line_width=2.5)
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            height=420,
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # Volume by Station & Period
    st.subheader("3. Traffic Volume by Station & Period")
    station_period = filtered_df.groupby(['station_code', 'period'])['count'].sum().reset_index()
    fig_station = px.bar(
        station_period,
        x='station_code',
        y='count',
        color='period',
        barmode='group',
        labels={'station_code': 'Station Code', 'count': 'Total Count', 'period': 'Period (WD/WE)'},
        color_discrete_sequence=['#111111', '#6b7280']
    )
    fig_station.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=380, 
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_station, use_container_width=True)

with tab_data:
    st.subheader("Interactive Filtered Dataset")
    st.markdown(f"Showing **{len(filtered_df):,}** interval records from **{active_db_info['name']}**.")
    
    display_df = filtered_df[[
        'count_id', 'station_code', 'interval_start', 'interval_end', 
        'vehicle_type', 'count', 'road_type', 'direction', 'period'
    ]].copy()
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=450
    )

    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download Filtered Data as CSV ({selected_db_key.upper()})",
        data=csv_data,
        file_name=f"filtered_traffic_counts_{selected_db_key}.csv",
        mime="text/csv",
    )

with tab_summary:
    st.subheader("Station Summary & Statistics")
    
    st_summary = filtered_df.groupby('station_code').agg(
        total_vehicles=('count', 'sum'),
        avg_vehicles_per_interval=('count', 'mean'),
        max_single_interval=('count', 'max'),
        total_records=('count', 'count')
    ).reset_index()
    
    st_summary['total_vehicles'] = st_summary['total_vehicles'].apply(lambda x: f"{x:,}")
    st_summary['avg_vehicles_per_interval'] = st_summary['avg_vehicles_per_interval'].round(2)
    st_summary['max_single_interval'] = st_summary['max_single_interval'].apply(lambda x: f"{x:,}")
    
    st.table(st_summary)

st.markdown("---")
st.caption(f"VARUNA Traffic Counts System | Active DB: {active_db_info['file']} | Running on Port 8501")
