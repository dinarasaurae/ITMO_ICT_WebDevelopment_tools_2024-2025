import requests
from bs4 import BeautifulSoup
import psycopg2

DB_PARAMS = {
    "dbname": "psychologists_db",
    "user": "postgres",
    "password": "",
    "host": "localhost",
    "port": "5433"
}

def parse_and_save(url, table_name="specializations"):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('h1', id="firstHeading")
        name = title_tag.get_text(strip=True) if title_tag else "No Title"

        first_paragraph = soup.find('p')
        description = first_paragraph.get_text(strip=True) if first_paragraph else "No description."

        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        cursor.execute(
            f'''
            INSERT INTO {table_name} (name, description)
            VALUES (%s, %s)
            ''',
            (name, description)
        )

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Saved {url} to {table_name} with name: {name}")

    except Exception as e:
        print(f"Error processing {url}: {e}")
