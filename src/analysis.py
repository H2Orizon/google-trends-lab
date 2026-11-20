import pandas as pd
import plotly.express as px

from database import connect_to_db

def get_trend_statistics(connection):
    query = '''
        SELECT 
            term,
            COUNT(*) FILTER (WHERE trend_status = 'Growth') as growth,
            COUNT(*) FILTER (WHERE trend_status = 'Decline') as decline,
            COUNT(*) FILTER (WHERE trend_status = 'Stable') as stable,
            ROUND(
                COUNT(*) FILTER (WHERE trend_status = 'Growth') * 100.0 /
                COUNT(*) FILTER (WHERE trend_status IN ('Growth', 'Decline', 'Stable')), 2
            ) AS growth_pct,
            ROUND(
                COUNT(*) FILTER (WHERE trend_status = 'Stable') * 100.0 /
                COUNT(*) FILTER (WHERE trend_status IN ('Growth', 'Decline', 'Stable')), 2
            ) AS stable_pct,
            ROUND(
                COUNT(*) FILTER (WHERE trend_status = 'Decline') * 100.0 /
                COUNT(*) FILTER (WHERE trend_status IN ('Growth', 'Decline', 'Stable')), 2
            ) AS decline_pct
        FROM (
            SELECT
                s.term,
                t.date,
                t.interest,
                LAG(t.interest) OVER (
                    PARTITION BY s.term
                    ORDER BY t.date
                ) AS previous_interest,
                t.interest - LAG(t.interest) OVER (
                    PARTITION BY s.term
                    ORDER BY t.date
                ) AS change,
            CASE
                WHEN t.interest - LAG(t.interest) OVER (
                    PARTITION BY s.term
                    ORDER BY t.date
                ) > 0 THEN 'Growth'

                WHEN t.interest - LAG(t.interest) OVER (
                    PARTITION BY s.term
                    ORDER BY t.date
                ) < 0 THEN 'Decline'

                WHEN t.interest - LAG(t.interest) OVER (
                    PARTITION BY s.term
                    ORDER BY t.date
                ) = 0 THEN 'Stable'

                ELSE 'Unknown'
            END AS trend_status
            FROM trend_data t
            JOIN search_terms s
                ON t.search_term_id = s.id
        ) AS trend_analysis
        GROUP BY term;
    '''

    cursor = connection.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
    # print(rows)

    columns = [
        "term",
        "growth",
        "decline",
        "stable",
        "growth_pct",
        "stable_pct",
        "decline_pct"
    ]

    statistics = pd.DataFrame(rows, columns=columns)

    return statistics

def get_trend_history(connection):
    query = '''
        SELECT term, date, interest 
        FROM search_terms
        JOIN trend_data
            ON trend_data.search_term_id = search_terms.id
        ORDER BY term, date
    '''

    cursor = connection.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    columns = [
        "term",
        "date",
        "interest"
    ]

    history = pd.DataFrame(rows, columns=columns)

    history["date"] = pd.to_datetime(history["date"])
    history["interest"] = pd.to_numeric(history["interest"])
    print(history.shape)
    print(history.info())
    print(history["term"].value_counts())

    return history

def create_trend_chart(history):

    fig = px.line(
        data_frame=history,
        x="date",
        y="interest",
        color="term"
    )

    fig.update_layout(
        title="Google Trends: популярність пошукових запитів в Україні",
        xaxis_title="Дата",
        yaxis_title="Інтерес (0–100)",
        hovermode="x unified"  
    )

    return fig

if __name__ == "__main__":
    connection = None

    try:
        connection = connect_to_db()
        result = get_trend_statistics(connection)
        history = get_trend_history(connection)
        print(history.head())

        # create_trend_chart(history)
    except Exception as error:
            print(f"Помилка підключення: {error}")
    finally:
        if connection is not None:
            connection.close()