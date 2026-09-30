from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg://demo:demo@localhost:5432/olist"


def get_engine():
    return create_engine(DB_URL)


if __name__ == "__main__":
    with get_engine().connect() as conn:
        print("connected to:", conn.execute(text("SELECT current_database()")).scalar())
        