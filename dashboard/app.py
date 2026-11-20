import streamlit as st
import sys
import pandas as pd
import plotly.express as px
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from database import (
    connect_to_db,
    insert_search_terms,
    insert_trend_data
)
from init_db import create_tables
from analysis import (
    get_trend_history,
    create_trend_chart,
    get_trend_statistics
)

st.set_page_config(
    page_title="Google Trends Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

connection = connect_to_db()

create_tables(connection)
insert_search_terms(connection)
insert_trend_data(connection)

st.title("Google Trends Dashboard")
st.write("Аналіз популярності пошукових запитів в Україні")

if connection:
    st.success("Успішне підключення до PostgreSQL!")

history = get_trend_history(connection)
statistics = get_trend_statistics(connection)

with st.sidebar:
    st.title("⚙️ Фільтри")

    st.subheader("Пошукові запити")

    terms = history["term"].unique()

    selected_terms = st.multiselect(
        "Оберіть запити:",
        options=terms,
        default=terms
    )

    st.subheader("Період аналізу")

    date_range = st.date_input(
        "Оберіть дати:",
        value=(history["date"].min(), history["date"].max()),
        min_value=history["date"].min(),
        max_value=history["date"].max()
    )

filtered_history = history[
    history["term"].isin(selected_terms)
]

filtered_history = filtered_history.sort_values(
    by=["term", "date"]
).copy()

if len(date_range) == 2:
    start_date, end_date = date_range

    filtered_history = filtered_history[
        (filtered_history["date"] >= pd.Timestamp(start_date)) &
        (filtered_history["date"] <= pd.Timestamp(end_date))
    ]

filtered_history["change"] = (
    filtered_history.groupby("term")["interest"].diff()
)

filtered_history["trend_status"] = "Unknown"

filtered_history.loc[
    filtered_history["change"] > 0, "trend_status"
] = "Growth"

filtered_history.loc[
    filtered_history["change"] < 0, "trend_status"
] = "Decline"

filtered_history.loc[
    filtered_history["change"] == 0, "trend_status"
] = "Stable"

if filtered_history.empty:
    st.warning("За вибраними фільтрами даних немає.")
    st.stop()

st.subheader("📊 Основні показники")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Кількість запитів",
    filtered_history["term"].nunique()
)

col2.metric(
    "Кількість спостережень",
    len(filtered_history)
)

col3.metric(
    "Середній інтерес",
    round(filtered_history["interest"].mean(), 2)
)

st.dataframe(filtered_history)

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Огляд",
    "🏆 Рейтинг",
    "📊 Динаміка",
    "📋 Дані"
])

ranking = (
    filtered_history.groupby("term")["interest"]
    .mean()
    .reset_index()
    .sort_values(by="interest", ascending=False)
)

with tab1:
    st.subheader("Динаміка популярності пошукових запитів")
    fig = create_trend_chart(filtered_history)
    st.plotly_chart(fig, width="stretch")

with tab2:
    ranking_fig = px.bar(
        ranking.sort_values("interest"),
        x="interest",
        y="term",
        orientation="h",
        title="Рейтинг популярності пошукових запитів",
        color="interest",
        text_auto=".2f",
        color_continuous_scale="Blues"
    )
    st.subheader("Рейтинг популярності")
    st.dataframe(ranking)
    st.plotly_chart(ranking_fig, width="stretch")

with tab3:
    statistics_filtered = (
        filtered_history[
            filtered_history["trend_status"] != "Unknown"
        ]
        .groupby(["term", "trend_status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for column in ["Growth", "Decline", "Stable"]:
        if column not in statistics_filtered.columns:
            statistics_filtered[column] = 0

    statistics_filtered["Total"] = (
        statistics_filtered[["Growth", "Decline", "Stable"]].sum(axis=1)
    )

    for column in ["Growth", "Decline", "Stable"]:
        statistics_filtered[f"{column}_pct"] = (
            statistics_filtered[column] /
            statistics_filtered["Total"].replace(0, pd.NA) * 100
        )

    statistics_long = statistics_filtered.melt(
        id_vars=["term"],
        value_vars=["Growth_pct", "Decline_pct", "Stable_pct"],
        var_name="trend_type",
        value_name="percentage"
    )

    st.dataframe(statistics_filtered)

    trend_pct_fig = px.bar(
        statistics_long,
        x="term",
        y="percentage",
        color="trend_type",
        title="Відсотковий розподіл динаміки трендів",
        barmode="group",
        labels={
            "term": "Пошуковий запит",
            "percentage": "Відсоток (%)",
            "trend_type": "Тип динаміки"
        },
        text_auto=".2f"
    )

    trend_fig = px.bar(
        statistics_filtered,
        x="term",
        y=["Growth", "Decline", "Stable"],
        title="Динаміка пошукових трендів",
        barmode="group",
        labels={
            "term": "Пошуковий запит",
            "value": "Кількість періодів",
            "variable": "Тип динаміки"
        }
    )

    st.subheader("Зростання, падіння та стабільність")
    st.plotly_chart(trend_fig, width="stretch")

    st.subheader("Відсотковий аналіз трендів")
    st.plotly_chart(trend_pct_fig, width="stretch")

with tab4:
    st.subheader("Історія пошукових трендів")
    st.dataframe(filtered_history, width="stretch")

    st.subheader("Статистика")
    st.dataframe(statistics_filtered, width="stretch")

st.divider()

st.caption(
    "Джерело: Google Trends | Географія: Україна | "
    "Інтерес нормалізований у діапазоні 0–100"
)