import psycopg
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DATA_LONG = "data/google-trends-long.csv"

categories = {
    "ChatGPT": "AI" ,
    "Machine Learning": "AI",
    "Python":"Programming",
    "Docker":"DevOps",
    "Data Science":"Analytics"
}

def connect_to_db():
    is_docker = os.getenv("DOCKER_ENV") == "true"

    connection = psycopg.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="db" if is_docker else "localhost",
        port=5432
    )

    return connection

def insert_search_terms(connection):
    curr = connection.cursor()
    for term, category in categories.items():
        curr.execute(
            '''
                INSERT INTO search_terms (term, category) 
                VALUES (%s, %s)
                ON CONFLICT (term) DO NOTHING;
            ''',
            (term, category)
        )

    connection.commit()

    curr.close()


def insert_trend_data(connection):
    data = pd.read_csv(DATA_LONG)
    # print(data.head())

    curr = connection.cursor()
    curr.execute(
        '''
            SELECT id, term FROM search_terms;
        '''
    )
    rows = curr.fetchall()
    # print(rows)

    term_ids = {term: term_id for term_id, term in rows}
    # print(term_ids)

    for row in data.itertuples(index=False):
        curr.execute(
            '''
                INSERT INTO trend_data (search_term_id, date, interest)
                VALUES (%s, %s, %s)
                ON CONFLICT (search_term_id, date) DO NOTHING;
            ''',
            (
                term_ids[row.search_term], 
                row.date, 
                row.interest
            )
        )

    connection.commit()
    curr.close()


if __name__ == "__main__":
    try:
        connection = connect_to_db()
        print("Успішне підключення до PostgreSQL!")

        insert_search_terms(connection)
        insert_trend_data(connection)

        connection.close()
        print("Підключення закрито.")
    except Exception as error:
        print(f"Помилка підключення: {error}")


