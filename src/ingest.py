
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def extract_data():
    csv_path = PROJECT_ROOT / "data" / "IOT-temp.csv"

    df = pd.read_csv(csv_path)

    print(f"Registros lidos: {len(df)}")
    return df


def transform_data(df):

    df = df.drop_duplicates().copy()

    df["noted_date"] = pd.to_datetime(
        df["noted_date"],
        format="%d-%m-%Y %H:%M",
        errors="raise",
    )

    df = df.rename(
        columns={
            "room_id/id": "room_id",
            "noted_date": "reading_time",
            "temp": "temperature",
            "out/in": "location_type",
        }
    )

    if df["id"].duplicated().any():
        raise ValueError("Ainda existem IDs duplicados após a limpeza.")

    print(f"Registros após a transformação: {len(df)}")
    return df


def load_data(df):

    required_vars = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_PORT",
    ]

    missing_vars = [
        name for name in required_vars if not os.getenv(name)
    ]

    if missing_vars:
        raise RuntimeError(
            f"Variáveis ausentes no .env: {', '.join(missing_vars)}"
        )

    connection = psycopg2.connect(
        host="localhost",
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                insert_sql = """
                    INSERT INTO temperature_readings
                    (id, room_id, reading_time, temperature, location_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """

                rows = [
                    (
                        row.id,
                        row.room_id,
                        row.reading_time.to_pydatetime(),
                        int(row.temperature),
                        row.location_type,
                    )
                    for row in df.itertuples(index=False)
                ]

                execute_batch(
                    cursor,
                    insert_sql,
                    rows,
                    page_size=1000,
                )

                print(
                    f"Registros processados para carga: {len(rows)}"
                )

    finally:
        connection.close()


def main():
    df = extract_data()
    transformed_df = transform_data(df)
    load_data(transformed_df)
    print("Pipeline concluído!")


if __name__ == "__main__":
    main()
