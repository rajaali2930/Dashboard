import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import json

# ---------------------------
# Configuration / constants
# ---------------------------
DEFAULT_FILE = "trial_balance.xlsx"
DEFAULT_SHEET = "trial_balance"

# Premium Dark Grey Color Scheme
COLORS = {
    "background": "#121212",
    "surface": "#1E1E1E", 
    "primary_text": "#E0E0E0",
    "secondary_text": "#B0B0B0",
    "accent": "#1E88E5",
    "expense": "#4CAF50",
    "pd": "#FF9800", 
    "ch": "#03A9F4",
    "positive": "#00E676",
    "negative": "#F44336",
    "neutral": "#9E9E9E",
    "border": "#2C2C2C",
    "card_bg": "#1A1A1A"
}

LOGO_PATH = "iqra-university-seeklogo.png"

# ---------------------------
# Utility functions
# ---------------------------
def adjust_hex_color(hex_color, factor=1.2):
    """Lighten or darken a hex color by a factor."""
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    rgb_adjusted = tuple(min(255, max(0, int(c * factor))) for c in rgb)
    return f"#{rgb_adjusted[0]:02x}{rgb_adjusted[1]:02x}{rgb_adjusted[2]:02x}"

def fmt_money(x, decimals=2):
    """Format number as currency with proper formatting."""
    try:
        if abs(x) >= 1e9:
            return f"${x/1e9:,.{decimals}f}B"
        elif abs(x) >= 1e6:
            return f"${x/1e6:,.{decimals}f}M"
        elif abs(x) >= 1e3:
            return f"${x/1e3:,.{decimals}f}K"
        else:
            return f"${x:,.{decimals}f}"
    except:
        return str(x)

def safe_pct(cy, ly):
    """Calculate safe percentage change."""
    if ly is None or np.isclose(ly, 0.0):
        return None
    try:
        return (cy - ly) / abs(ly)
    except:
        return None

def make_yoy_str(cy, ly):
    """Create year-over-year percentage string with proper formatting."""
    p = safe_pct(cy, ly)
    if p is None:
        return "—"
    sign = "+" if p >= 0 else ""
    return f"{sign}{p*100:.1f}%"

def get_trend_icon(cy, ly):
    """Get trend icon based on comparison."""
    p = safe_pct(cy, ly)
    if p is None:
        return "➖"
    elif p > 0:
        return "📈"
    elif p < 0:
        return "📉"
    else:
        return "➖"

def get_category_icon(category):
    """Get appropriate icon for each category."""
    icons = {
        "EXPENSE": "💰",
        "PD": "📦", 
        "CH": "🏢",
        "LIABILITY": "📋",
        "ASSET": "💎",
        "EQUITY": "📊",
        "INCOME": "💵"
    }
    return icons.get(category, "📊")

@st.cache_data
def load_df(path: str, sheet: str):
    """Load and process Excel data with caching."""
    import openpyxl
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", dtype={"Account ID": str})
    df.columns = [c.strip() for c in df.columns]
    
    required = {"Account ID", "Account Description", "Debit Amt", "Credit Amt", "Last FYE Bal", "Type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Required columns missing: {missing}")
    
    # Clean and convert numeric columns
    for col in ["Debit Amt", "Credit Amt", "Last FYE Bal"]:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False).str.strip()
        df[col] = pd.to_numeric(df[col].replace({"": "0", "nan": "0", "None": "0"}), errors="coerce").fillna(0.0)
    
    df["Type"] = df["Type"].astype(str).str.strip().str.upper()
    df["CY_Amount"] = df["Debit Amt"] - df["Credit Amt"]
    df["LY_Amount"] = df["Last FYE Bal"].astype(float)
    
    # Add calculated fields
    df["YoY_Change"] = df["CY_Amount"] - df["LY_Amount"]
    df["YoY_Pct"] = df.apply(lambda x: safe_pct(x["CY_Amount"], x["LY_Amount"]), axis=1)
    
    return df

def top_n_with_other(df: pd.DataFrame, n=10):
    """Get top N items with 'Other' category for remaining items."""
    df_sorted = df.sort_values("CY_Amount", ascending=False).copy()
    top = df_sorted.head(n).copy()
    rest = df_sorted.iloc[n:].copy()
    
    top["Label"] = top["Account Description"].astype(str)
    
    if len(rest) > 0:
        other = {
            "Label": f"Other ({len(rest)} accts)",
            "CY_Amount": rest["CY_Amount"].sum(),
            "LY_Amount": rest["LY_Amount"].sum(),
            "YoY_Change": rest["YoY_Change"].sum(),
            "YoY_Pct": safe_pct(rest["CY_Amount"].sum(), rest["LY_Amount"].sum())
        }
        top_out = pd.concat([top[["Label","CY_Amount","LY_Amount","YoY_Change","YoY_Pct"]], 
                           pd.DataFrame([other])], ignore_index=True)
    else:
        top_out = top[["Label","CY_Amount","LY_Amount","YoY_Change","YoY_Pct"]]
    
    # Add ranking
    top_out = top_out.reset_index(drop=True)
    top_out.insert(0, "Rank", range(1, len(top_out) + 1))
    
    return top_out

def create_kpi_card(title, value, delta, icon, color):
    """Create a styled KPI card with custom HTML."""
    trend_color = COLORS["positive"] if delta and delta != "—" and not delta.startswith("-") else COLORS["negative"]
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['card_bg']}, {adjust_hex_color(COLORS['card_bg'], 1.05)});
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 24px; margin-right: 10px;">{icon}</span>
            <span style="color: {COLORS['secondary_text']}; font-size: 14px; font-weight: 500;">{title}</span>
        </div>
        <div style="font-size: 28px; font-weight: bold; color: {COLORS['primary_text']}; margin-bottom: 5px;">
            {value}
        </div>
        <div style="color: {trend_color}; font-size: 14px; font-weight: 500;">
            {delta}
        </div>
    </div>
    """

def create_advanced_chart(df, chart_type="bar", title="", height=400):
    """Create advanced charts with consistent styling."""
    if chart_type == "treemap":
        fig = px.treemap(
            df, 
            path=['Type', 'Account Description'], 
            values='CY_Amount',
            title=title,
            color='CY_Amount',
            color_continuous_scale=[COLORS['expense'], COLORS['pd'], COLORS['ch']]
        )
    elif chart_type == "sunburst":
        fig = px.sunburst(
            df,
            path=['Type', 'Account Description'],
            values='CY_Amount',
            title=title,
            color='CY_Amount',
            color_continuous_scale=[COLORS['expense'], COLORS['pd'], COLORS['ch']]
        )
    else:  # bar chart
        fig = px.bar(
            df,
            x='Account Description',
            y='CY_Amount',
            title=title,
            color='CY_Amount',
            color_continuous_scale=[COLORS['expense'], COLORS['pd']]
        )
    
    # Apply consistent styling
    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font_color=COLORS['primary_text'],
        font_family="Arial, sans-serif",
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(
            gridcolor=COLORS['border'],
            showgrid=True,
            tickangle=-45
        ),
        yaxis=dict(
            gridcolor=COLORS['border'],
            showgrid=True
        ),
        title=dict(
            x=0.5,
            xanchor='center',
            font=dict(size=16, color=COLORS['primary_text'])
        )
    )
    
    return fig

# ---------------------------
# Streamlit Page Config
# ---------------------------
st.set_page_config(
    page_title="Enterprise Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# Custom CSS for Premium Styling
# ---------------------------
st.markdown(
    f"""
    <style>
        /* Main app styling */
        .stApp {{
            background: linear-gradient(135deg, {COLORS['background']}, {adjust_hex_color(COLORS['background'], 1.02)});
            color: {COLORS['primary_text']};
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background-color: {COLORS['surface']};
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS['primary_text']};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 600;
        }}
        
        /* Metric cards */
        .stMetric {{
            background: linear-gradient(135deg, {COLORS['card_bg']}, {adjust_hex_color(COLORS['card_bg'], 1.05)});
            border-radius: 12px;
            padding: 15px;
            border: 1px solid {COLORS['border']};
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        
        .stMetric .value {{
            color: {COLORS['primary_text']};
            font-size: 1.8em;
            font-weight: bold;
        }}
        
        .stMetric .label {{
            color: {COLORS['secondary_text']};
            font-size: 0.9em;
        }}
        
        .stMetric .delta {{
            color: {COLORS['positive']};
            font-weight: 500;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {COLORS['accent']}, {adjust_hex_color(COLORS['accent'], 0.9)});
            color: {COLORS['primary_text']};
            border-radius: 8px;
            padding: 10px 20px;
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .stButton > button:hover {{
            background: linear-gradient(135deg, {adjust_hex_color(COLORS['accent'], 1.1)}, {COLORS['accent']});
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        
        /* Dataframes */
        [data-testid="stDataFrameResizable"], .stDataFrame, .stTable {{
            background-color: {COLORS['surface']} !important;
            border-radius: 12px;
            border: 1px solid {COLORS['border']} !important;
            overflow: hidden;
        }}
        
        [data-testid="stDataFrameResizable"] table, .stDataFrame table, .stTable table {{
            background-color: {COLORS['surface']} !important;
            color: {COLORS['primary_text']} !important;
        }}
        
        [data-testid="stDataFrameResizable"] th, [data-testid="stDataFrameResizable"] td,
        .stDataFrame th, .stDataFrame td, .stTable th, .stTable td {{
            background-color: {COLORS['surface']} !important;
            color: {COLORS['primary_text']} !important;
            border: 1px solid {COLORS['border']} !important;
            padding: 12px 8px;
        }}
        
        [data-testid="stDataFrameResizable"] thead tr th,
        .stDataFrame thead tr th, .stTable thead tr th {{
            background-color: {adjust_hex_color(COLORS['surface'], 1.1)} !important;
            color: {COLORS['primary_text']} !important;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        /* Input fields */
        .stTextInput > div > input, .stNumberInput > div > input,
        .stSelectbox > div > select, .stMultiselect > div > div {{
            background-color: {COLORS['surface']} !important;
            color: {COLORS['primary_text']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 8px;
            padding: 8px 12px;
        }}
        
        /* Expanders */
        .streamlit-expanderHeader {{
            background-color: {COLORS['surface']} !important;
            color: {COLORS['primary_text']} !important;
            border-radius: 8px;
            border: 1px solid {COLORS['border']} !important;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: {COLORS['surface']};
            border-radius: 8px 8px 0px 0px;
            color: {COLORS['secondary_text']};
            border: 1px solid {COLORS['border']};
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {COLORS['accent']};
            color: {COLORS['primary_text']};
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {COLORS['surface']};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {COLORS['border']};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['accent']};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Sidebar Configuration
# ---------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: {COLORS['primary_text']}; margin: 0;">📊 Dashboard</h2>
            <p style="color: {COLORS['secondary_text']}; margin: 5px 0;">Enterprise Management</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Data Configuration
    st.subheader("📁 Data Configuration")
    file_path = st.text_input("Excel File Path", value=DEFAULT_FILE, help="Path to your trial balance Excel file")
    sheet_name = st.text_input("Worksheet Name", value=DEFAULT_SHEET, help="Name of the worksheet containing data")
    
    # Filters
    st.subheader("🔍 Filters & Controls")
    top_n = st.slider("Top N Expense Lines", min_value=5, max_value=25, value=10, step=1)
    
    type_options = ["EXPENSE", "PD", "CH", "LIABILITY", "ASSET", "EQUITY", "INCOME"]
    type_filter = st.multiselect(
        "Account Types",
        options=type_options,
        default=["EXPENSE", "PD", "CH"],
        help="Select account types to include in analysis"
    )
    
    # View Options
    st.subheader("📈 View Options")
    show_ly = st.checkbox("Show Last Year Comparisons", value=True)
    show_percentages = st.checkbox("Show as % of Total", value=False)
    show_trends = st.checkbox("Show Trend Indicators", value=True)
    
    # Export Options
    st.subheader("💾 Export Options")
    download_name = st.text_input("Export Filename", value="management_report.csv")
    
    # Performance Settings
    st.subheader("⚡ Performance")
    cache_data = st.checkbox("Cache Data", value=True, help="Improve performance by caching data")
    max_rows = st.number_input("Max Rows to Display", min_value=100, max_value=10000, value=1000, step=100)

# ---------------------------
# Header Section
# ---------------------------
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    try:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=80)
        else:
            st.markdown(f"<div style='text-align: center; font-size: 48px;'>🏢</div>", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"<div style='text-align: center; font-size: 48px;'>🏢</div>", unsafe_allow_html=True)

with col2:
    st.markdown(
        f"""
        <div style="text-align: center;">
            <h1 style="color: {COLORS['primary_text']}; margin: 0; font-size: 2.5em; font-weight: 700;">
                Enterprise Management Dashboard
            </h1>
            <p style="color: {COLORS['secondary_text']}; margin: 5px 0; font-size: 1.1em;">
                Financial Overview & Strategic Analysis
            </p>
            <p style="color: {COLORS['secondary_text']}; margin: 0; font-size: 0.9em;">
                Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 20px;">
            <div style="background: {COLORS['accent']}; color: {COLORS['primary_text']}; 
                        padding: 8px 16px; border-radius: 20px; display: inline-block; font-weight: 500;">
                LIVE
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ---------------------------
# Data Loading
# ---------------------------
try:
    with st.spinner("Loading financial data..."):
        df = load_df(file_path, sheet_name)
    st.success(f"✅ Data loaded successfully! {len(df):,} records processed.")
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.info("Please check your file path and worksheet name in the sidebar.")
    st.stop()

# Apply filters
df_filtered = df[df["Type"].isin([t.upper() for t in type_filter])].copy()

# Split by type
df_exp = df_filtered[df_filtered["Type"] == "EXPENSE"].copy()
df_pd = df_filtered[df_filtered["Type"] == "PD"].copy()
df_ch = df_filtered[df_filtered["Type"] == "CH"].copy()

# Calculate totals
totals = {
    "expense": {
        "cy": float(df_exp["CY_Amount"].sum()),
        "ly": float(df_exp["LY_Amount"].sum()),
        "icon": get_category_icon("EXPENSE")
    },
    "pd": {
        "cy": float(df_pd["CY_Amount"].sum()),
        "ly": float(df_pd["LY_Amount"].sum()),
        "icon": get_category_icon("PD")
    },
    "ch": {
        "cy": float(df_ch["CY_Amount"].sum()),
        "ly": float(df_ch["LY_Amount"].sum()),
        "icon": get_category_icon("CH")
    }
}

totals["grand"] = {
    "cy": totals["expense"]["cy"] + totals["pd"]["cy"] + totals["ch"]["cy"],
    "ly": totals["expense"]["ly"] + totals["pd"]["ly"] + totals["ch"]["ly"],
    "icon": "📊"
}

# ---------------------------
# KPI Cards Section
# ---------------------------
st.markdown(
    f"""
    <div style="margin: 30px 0;">
        <h2 style="color: {COLORS['primary_text']}; text-align: center; margin-bottom: 20px;">
            🎯 Key Performance Indicators
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

# Create KPI cards using custom HTML
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        create_kpi_card(
            "Total Expenses",
            fmt_money(totals["expense"]["cy"]),
            make_yoy_str(totals["expense"]["cy"], totals["expense"]["ly"]),
            totals["expense"]["icon"],
            COLORS["expense"]
        ),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        create_kpi_card(
            "PD Amount",
            fmt_money(totals["pd"]["cy"]),
            make_yoy_str(totals["pd"]["cy"], totals["pd"]["ly"]),
            totals["pd"]["icon"],
            COLORS["pd"]
        ),
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        create_kpi_card(
            "CH Amount",
            fmt_money(totals["ch"]["cy"]),
            make_yoy_str(totals["ch"]["cy"], totals["ch"]["ly"]),
            totals["ch"]["icon"],
            COLORS["ch"]
        ),
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        create_kpi_card(
            "Grand Total",
            fmt_money(totals["grand"]["cy"]),
            make_yoy_str(totals["grand"]["cy"], totals["grand"]["ly"]),
            totals["grand"]["icon"],
            COLORS["accent"]
        ),
        unsafe_allow_html=True
    )

# ---------------------------
# Main Analysis Section
# ---------------------------
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Expense Analysis", "📈 Trends & Comparisons", "🌳 Hierarchical View", "📋 Detailed Data"])

with tab1:
    st.subheader("📊 Top Expense Analysis")
    
    if df_exp.empty:
        st.info("No expense data found with current filters.")
    else:
        # Get top expenses
        top_df = top_n_with_other(df_exp, n=top_n)
        
        # Create comparison chart
        if show_ly:
            fig_comparison = go.Figure()
            
            # Current year bars
            fig_comparison.add_trace(go.Bar(
                name="Current Year",
                x=top_df["Label"],
                y=top_df["CY_Amount"],
                marker_color=COLORS["expense"],
                text=[fmt_money(x) for x in top_df["CY_Amount"]],
                textposition='outside'
            ))
            
            # Last year bars
            fig_comparison.add_trace(go.Bar(
                name="Last Year",
                x=top_df["Label"],
                y=top_df["LY_Amount"],
                marker_color=COLORS["pd"],
                text=[fmt_money(x) for x in top_df["LY_Amount"]],
                textposition='outside'
            ))
            
            fig_comparison.update_layout(
                title="Top Expense Lines - Current vs Last Year",
                barmode='group',
                plot_bgcolor=COLORS['background'],
                paper_bgcolor=COLORS['background'],
                font_color=COLORS['primary_text'],
                height=500,
                xaxis_tickangle=-45,
                xaxis=dict(gridcolor=COLORS['border'], showgrid=True),
                yaxis=dict(gridcolor=COLORS['border'], showgrid=True)
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Summary table
        st.subheader("📋 Expense Summary Table")
        
        summary_table = top_df.copy()
        summary_table["YoY %"] = summary_table.apply(
            lambda r: make_yoy_str(r["CY_Amount"], r["LY_Amount"]), axis=1
        )
        summary_table["Trend"] = summary_table.apply(
            lambda r: get_trend_icon(r["CY_Amount"], r["LY_Amount"]), axis=1
        )
        
        # Format for display
        display_table = summary_table[["Rank", "Label", "CY_Amount", "LY_Amount", "YoY %", "Trend"]].copy()
        display_table.columns = ["Rank", "Description", "Current Year", "Last Year", "YoY %", "Trend"]
        
        st.dataframe(
            display_table.style.format({
                "Current Year": lambda x: fmt_money(x),
                "Last Year": lambda x: fmt_money(x)
            }),
            use_container_width=True,
            height=400
        )
        
        # JavaScript to ensure table styling
        st.components.v1.html(
            f"""
            <script>
                document.querySelectorAll('[data-testid="stDataFrameResizable"] table').forEach(table => {{
                    table.style.backgroundColor = '{COLORS["surface"]}';
                    table.querySelectorAll('th, td').forEach(cell => {{
                        cell.style.backgroundColor = '{COLORS["surface"]}';
                        cell.style.color = '{COLORS["primary_text"]}';
                        cell.style.border = '1px solid {COLORS["border"]}';
                    }});
                    table.querySelectorAll('thead tr th').forEach(header => {{
                        header.style.backgroundColor = '{adjust_hex_color(COLORS["surface"], 1.1)}';
                        header.style.color = '{COLORS["primary_text"]}';
                    }});
                }});
            </script>
            """,
            height=0
        )
        
        # Export button
        csv_data = summary_table.to_csv(index=False)
        st.download_button(
            label="📥 Download Expense Summary",
            data=csv_data,
            file_name=f"expense_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with tab2:
    st.subheader("📈 Trend Analysis & Comparisons")
    
    # Create trend analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # YoY comparison chart
        categories = ["Expenses", "PD", "CH", "Total"]
        cy_values = [totals["expense"]["cy"], totals["pd"]["cy"], totals["ch"]["cy"], totals["grand"]["cy"]]
        ly_values = [totals["expense"]["ly"], totals["pd"]["ly"], totals["ch"]["ly"], totals["grand"]["ly"]]
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            name="Current Year",
            x=categories,
            y=cy_values,
            marker_color=[COLORS["expense"], COLORS["pd"], COLORS["ch"], COLORS["accent"]]
        ))
        fig_trend.add_trace(go.Bar(
            name="Last Year",
            x=categories,
            y=ly_values,
            marker_color=[adjust_hex_color(COLORS["expense"], 0.7), 
                         adjust_hex_color(COLORS["pd"], 0.7), 
                         adjust_hex_color(COLORS["ch"], 0.7), 
                         adjust_hex_color(COLORS["accent"], 0.7)]
        ))
        
        fig_trend.update_layout(
            title="Year-over-Year Comparison",
            barmode='group',
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            font_color=COLORS['primary_text'],
            height=400,
            xaxis=dict(gridcolor=COLORS['border'], showgrid=True),
            yaxis=dict(gridcolor=COLORS['border'], showgrid=True)
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        # Growth rate chart
        growth_rates = []
        for i, cat in enumerate(categories[:-1]):  # Exclude total
            pct = safe_pct(cy_values[i], ly_values[i])
            growth_rates.append(pct * 100 if pct is not None else 0)
        
        fig_growth = go.Figure(go.Bar(
            x=["Expenses", "PD", "CH"],
            y=growth_rates,
            marker_color=[COLORS["positive"] if x >= 0 else COLORS["negative"] for x in growth_rates],
            text=[f"{x:+.1f}%" for x in growth_rates],
            textposition='outside'
        ))
        
        fig_growth.update_layout(
            title="Growth Rates (YoY %)",
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            font_color=COLORS['primary_text'],
            height=400,
            yaxis_title="Growth Rate (%)",
            xaxis=dict(gridcolor=COLORS['border'], showgrid=True),
            yaxis=dict(gridcolor=COLORS['border'], showgrid=True)
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)

with tab3:
    st.subheader("🌳 Hierarchical Data Visualization")
    
    # Treemap visualization
    if not df_filtered.empty:
        fig_treemap = px.treemap(
            df_filtered,
            path=['Type', 'Account Description'],
            values='CY_Amount',
            title="Expense Distribution by Category",
            color='CY_Amount',
            color_continuous_scale=[COLORS['expense'], COLORS['pd'], COLORS['ch']]
        )
        
        fig_treemap.update_layout(
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            font_color=COLORS['primary_text'],
            height=600
        )
        
        st.plotly_chart(fig_treemap, use_container_width=True)
        
        # Sunburst chart
        st.subheader("🌞 Sunburst Chart")
        fig_sunburst = px.sunburst(
            df_filtered,
            path=['Type', 'Account Description'],
            values='CY_Amount',
            title="Hierarchical Expense Structure",
            color='CY_Amount',
            color_continuous_scale=[COLORS['expense'], COLORS['pd'], COLORS['ch']]
        )
        
        fig_sunburst.update_layout(
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            font_color=COLORS['primary_text'],
            height=600
        )
        
        st.plotly_chart(fig_sunburst, use_container_width=True)

with tab4:
    st.subheader("📋 Detailed Data View")
    
    # Search functionality
    search_term = st.text_input("🔍 Search accounts:", placeholder="Enter account description...")
    
    if search_term:
        filtered_data = df_filtered[
            df_filtered["Account Description"].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_data = df_filtered
    
    # Display filtered data
    if not filtered_data.empty:
        display_data = filtered_data.head(max_rows).copy()
        display_data["YoY %"] = display_data.apply(
            lambda r: make_yoy_str(r["CY_Amount"], r["LY_Amount"]), axis=1
        )
        
        st.dataframe(
            display_data[["Account ID", "Account Description", "Type", "CY_Amount", "LY_Amount", "YoY %"]].style.format({
                "CY_Amount": lambda x: fmt_money(x),
                "LY_Amount": lambda x: fmt_money(x)
            }),
            use_container_width=True,
            height=500
        )
        
        st.info(f"Showing {len(display_data)} of {len(filtered_data)} records. Use search to filter results.")
    else:
        st.warning("No data found matching your search criteria.")

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; padding: 20px 0; color: {COLORS['secondary_text']};">
        <p style="margin: 0; font-size: 0.9em;">
            🏢 <strong>Enterprise Management Dashboard</strong> | 
            Powered by Iqra University | 
            Version 2.0 | 
            Data as of {datetime.now().strftime('%B %Y')}
        </p>
        <p style="margin: 5px 0 0 0; font-size: 0.8em; opacity: 0.7;">
            Built with Streamlit & Plotly | 
            Real-time Financial Analytics | 
            Executive Decision Support
        </p>
    </div>
    """,
    unsafe_allow_html=True
)