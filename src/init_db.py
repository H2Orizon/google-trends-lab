import psycopg


def create_tables(connection):
    with connection.cursor() as cursor:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_terms (
                id SERIAL PRIMARY KEY,
                term VARCHAR(100) NOT NULL UNIQUE,
                category VARCHAR(50) NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trend_data (
                id SERIAL PRIMARY KEY,
                search_term_id INTEGER NOT NULL,
                date DATE NOT NULL,
                interest NUMERIC(5,2) NOT NULL,
                FOREIGN KEY (search_term_id)
                    REFERENCES search_terms(id),
                UNIQUE (search_term_id, date)
            );
        """)

    connection.commit()