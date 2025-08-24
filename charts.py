from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px


def plot_kpis(kpis: pd.DataFrame) -> None:
    """Display KPI metrics using Streamlit metric widgets.

    Parameters
    ----------
    kpis : DataFrame
        Expected to contain columns ``total_sessions``, ``total_conversions``,
        and ``overall_conversion_rate`` with at least one row. If empty,
        zeros are displayed instead.
    """
    total_sessions = int(kpis.iloc[0]['total_sessions']) if not kpis.empty else 0
    total_conversions = int(kpis.iloc[0]['total_conversions']) if not kpis.empty else 0
    conv_rate = kpis.iloc[0]['overall_conversion_rate'] if not kpis.empty else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sessions", f"{total_sessions:,}")
    c2.metric("Total Conversions", f"{total_conversions:,}")
    c3.metric("Overall Conversion Rate", f"{conv_rate or 0:.2f}%")


def plot_weekday_vs_weekend(df: pd.DataFrame) -> None:
    """Plot Weekday vs Weekend conversion rates."""
    if df.empty:
        st.info("No data for Weekday vs Weekend chart.")
        return
    df = df.replace({"weekend": {True: "Weekend", False: "Weekday"}})
    fig = px.bar(
        df,
        x="weekend",
        y="conversion_rate",
        text="conversion_rate",
        labels={"conversion_rate": "Conversion Rate (%)", "weekend": ""},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


def plot_monthwise_conversion_rate(df: pd.DataFrame) -> None:
    """Plot monthly conversion rates as a line chart."""
    if df.empty:
        st.info("No data for Monthwise Conversion Rate chart.")
        return
    fig = px.line(
        df,
        x="month",
        y="conversion_rate",
        markers=True,
        labels={"conversion_rate": "Conversion Rate (%)", "month": "Month"},
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_browser_share(df: pd.DataFrame) -> None:
    """Plot browser share by sessions as a pie chart."""
    if df.empty:
        st.info("No data for Browser Share chart.")
        return
    fig = px.pie(
        df,
        names="name",
        values="total_sessions",
        hole=0.45,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_browser_conversion_rate(df: pd.DataFrame) -> None:
    """Plot browser conversion rates as a bar chart."""
    if df.empty:
        st.info("No data for Browser Conversion Rate chart.")
        return
    fig = px.bar(
        df,
        x="name",
        y="conversion_rate",
        text="conversion_rate",
        labels={"name": "Browser", "conversion_rate": "Conversion Rate (%)"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


def plot_traffic_type_performance(df: pd.DataFrame) -> None:
    """Plot traffic type conversion rates as a horizontal bar chart."""
    if df.empty:
        st.info("No data for Traffic Type – Conversion Rate chart.")
        return
    fig = px.bar(
        df,
        y="name",
        x="conversion_rate",
        orientation="h",
        text="conversion_rate",
        labels={"name": "Traffic Type", "conversion_rate": "Conversion Rate (%)"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


def plot_region_performance(df: pd.DataFrame) -> None:
    """Plot region conversion rates as a bar chart."""
    if df.empty:
        st.info("No data for Region – Conversion Rate chart.")
        return
    fig = px.bar(
        df.head(15),
        x="name",
        y="conversion_rate",
        text="conversion_rate",
        labels={"name": "Region", "conversion_rate": "Conversion Rate (%)"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


def plot_os_performance(df: pd.DataFrame) -> None:
    """Plot operating system conversion rates as a bar chart."""
    if df.empty:
        st.info("No data for OS Performance chart.")
        return
    fig = px.bar(
        df,
        x="name",
        y="conversion_rate",
        text="conversion_rate",
        labels={"name": "Operating System", "conversion_rate": "Conversion Rate (%)"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


def plot_page_type_performance(df: pd.DataFrame) -> None:
    """Plot page type conversion rates as a bar chart."""
    if df.empty:
        st.info("No data for Page Type Performance chart.")
        return
    fig = px.bar(
        df,
        x="page_type",
        y="conversion_rate",
        text="conversion_rate",
        labels={"page_type": "Page Type", "conversion_rate": "Conversion Rate (%)"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


def plot_engagement_metrics_impact(df: pd.DataFrame) -> None:
    """Plot engagement metrics impact as a grouped bar chart."""
    if df.empty:
        st.info("No data for Engagement Metrics Impact chart.")
        return
    # Melt the DataFrame to long form for easier plotting
    df_melted = df.melt(id_vars='revenue', var_name='metric', value_name='average_value')
    df_melted['revenue'] = df_melted['revenue'].map({True: 'Converted', False: 'Did Not Convert'})
    # Format values differently depending on metric type
    def format_eng_value(row):
        if row['metric'] in ['avg_bounce_rate', 'avg_exit_rate']:
            return f"{pd.to_numeric(row['average_value'], errors='coerce'):.2%}"
        else:
            return f"${pd.to_numeric(row['average_value'], errors='coerce'):.2f}"
    df_melted['text_value'] = df_melted.apply(format_eng_value, axis=1)
    fig = px.bar(
        df_melted,
        x="metric",
        y="average_value",
        color="revenue",
        barmode="group",
        text='text_value',
        labels={"metric": "Engagement Metric", "average_value": "Average Value", "revenue": "Session Outcome"},
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)


def plot_special_day_effect(df: pd.DataFrame) -> None:
    """Plot special day effect as a bar chart."""
    if df.empty:
        st.info("No data for Special Day Effect chart.")
        return
    fig = px.bar(
        df,
        x="specialday",
        y="conversion_rate",
        text="conversion_rate",
        labels={"specialday": "Special Day Score", "conversion_rate": "Conversion Rate (%)"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)


# --- Cohort and cohort-like visualisations ---

def plot_monthly_new_vs_returning(df: pd.DataFrame) -> None:
    """Plot monthly new vs returning visitor conversion rates.

    This expects columns ``month``, ``visitortype`` (with values
    like ``New_Visitor``/``Returning_Visitor``) and ``conversion_rate``.
    It renders a line chart with a separate trace per visitor type.
    """
    if df.empty:
        st.info("No data for Monthly New vs Returning Visitors chart.")
        return
    fig = px.line(
        df,
        x="month",
        y="conversion_rate",
        color="visitortype",
        markers=True,
        labels={"conversion_rate": "Conversion Rate (%)", "month": "Month", "visitortype": "Visitor Type"},
    )
    # Use an explicit key to avoid StreamlitDuplicateElementId errors when
    # this chart is rendered multiple times within the same app session.
    st.plotly_chart(fig, use_container_width=True, key="monthly_new_vs_returning_chart")


def plot_weekday_conversion_by_traffic(df: pd.DataFrame) -> None:
    """Plot conversion rate by traffic type for weekday/weekend.

    Expects columns ``weekend_label`` (e.g. ``Weekday``/``Weekend``),
    ``traffic_name`` and ``conversion_rate``. Displays a grouped bar chart.
    """
    if df.empty:
        st.info("No data for Weekday Conversion by Traffic chart.")
        return
    fig = px.bar(
        df,
        x="traffic_name",
        y="conversion_rate",
        color="weekend_label",
        barmode="group",
        text="conversion_rate",
        labels={"traffic_name": "Traffic Type", "conversion_rate": "Conversion Rate (%)", "weekend_label": "Weekend"},
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    # Provide a unique key to prevent duplicate element IDs.
    st.plotly_chart(fig, use_container_width=True, key="weekday_conversion_by_traffic_chart")


def plot_browser_os_matrix(df: pd.DataFrame) -> None:
    """Plot a heatmap of conversion rate by browser and operating system.

    Expects columns ``browser_name``, ``os_name`` and ``conversion_rate``.
    A heatmap conveys the conversion rate for each browser/OS pair.
    """
    if df.empty:
        st.info("No data for Browser × OS Conversion Matrix chart.")
        return
    # Pivot the DataFrame into a matrix form for heatmap
    pivot = df.pivot(index="os_name", columns="browser_name", values="conversion_rate")
    fig = px.imshow(
        pivot,
        labels=dict(x="Browser", y="Operating System", color="Conversion Rate (%)"),
        aspect="auto",
    )
    # Provide a unique key to prevent duplicate element IDs.
    st.plotly_chart(fig, use_container_width=True, key="browser_os_matrix_chart")

# -------------------------------------------------------------------
# Cohort analysis
# -------------------------------------------------------------------

def plot_cohort(df: pd.DataFrame) -> None:
    """Plot cohort analysis for monthly new vs returning visitors.

    This function expects a DataFrame with columns ``month``, ``visitortype`` and
    ``conversion_rate``. It will draw a line chart comparing conversion
    rates for new and returning visitors across months.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame returned from the ``clickstream.monthly_new_vs_returning`` view.
    """
    if df.empty:
        st.info("No data for Cohort Analysis chart.")
        return
    # Ensure the month column is sorted chronologically if not already
    try:
        df_sorted = df.sort_values("month")
    except Exception:
        df_sorted = df
    fig = px.line(
        df_sorted,
        x="month",
        y="conversion_rate",
        color="visitortype",
        markers=True,
        labels={
            "month": "Month",
            "conversion_rate": "Conversion Rate (%)",
            "visitortype": "Visitor Type",
        },
    )
    st.plotly_chart(fig, use_container_width=True)