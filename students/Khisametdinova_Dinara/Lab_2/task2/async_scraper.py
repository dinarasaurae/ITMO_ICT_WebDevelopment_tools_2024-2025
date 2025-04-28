import aiohttp
import asyncio
from bs4 import BeautifulSoup
import psycopg2
import time

DB_PARAMS = {
    "dbname": "psychologists_db",
    "user": "postgres",
    "password": "",
    "host": "localhost",
    "port": "5433"
}

async def parse_and_save(session, url, table_name="specializations_async"):
    try:
        async with session.get(url, timeout=10) as response:
            text = await response.text()

            if "#REDIRECT" in text.upper():
                print(f"Skipped redirect {url}")
                return

            soup = BeautifulSoup(text, 'html.parser')
            title_tag = soup.find('h1', id="firstHeading")
            if not title_tag:
                print(f"Skipped {url} (no title)")
                return
            name = title_tag.get_text(strip=True)

            if any(bad in name for bad in ["List of", "Outline of", "Timeline of", "Index of"]):
                print(f"Skipped {url} (bad title: {name})")
                return

            # Находим первый нормальный параграф
            paragraphs = soup.find_all('p')
            description = None
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 50:
                    description = text
                    break

            if not description:
                print(f"Skipped {url} (no good paragraph)")
                return

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

            print(f"Saved {name} from {url}")

    except Exception as e:
        print(f"Error processing {url}: {e}")

async def main():
    with open('specialization_urls.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [parse_and_save(session, url, table_name="specializations_async") for url in urls]
        await asyncio.gather(*tasks)

    end_time = time.time()

    print(f"Async finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(main())
