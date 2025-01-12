import asyncio
import aiohttp
import json
import re
import nest_asyncio
import os

# Zorg ervoor dat er een event loop is voordat je nest_asyncio toepast
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
nest_asyncio.apply()

# Functie om URLs te lezen uit het bestand urls.txt
def read_urls(file_path='urls.txt'):
    urls = []
    with open(file_path, 'r', encoding='latin-1') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 3:
                name, url, category = parts
                urls.append((name, url, category))
    return urls

# Asynchrone functie om de inhoud van een URL op te halen
async def fetch_content(session, url, semaphore):
    async with semaphore:
        async with session.get(url) as response:
            return await response.text()

# Functie om de inhoud van de wetgeving op te slaan in een JSON-bestand
def save_cache_to_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Hoofdfunctie om URLs te verwerken en de inhoud in een cache op te slaan
async def create_legislation_cache(urls, max_concurrent_requests=4):
    # Initialiseer de caches
    cache_omgevingsplannen_1 = {}
    cache_omgevingsplannen_2 = {}
    cache_other = {}
    
    omgevingsplan_counter = 0

    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        tasks = []

        for name, url, category in urls:
            # Asynchrone taak maken voor elke URL
            task = asyncio.create_task(fetch_content(session, url, semaphore))
            tasks.append((task, name, url, category))

        # Wacht tot alle taken zijn voltooid en verwerk de resultaten
        for task, name, url, category in tasks:
            content = await task
            # Verdeel de omgevingsplannen over twee cache-bestanden
            if "omgevingsplan" in category.lower():
                if omgevingsplan_counter % 2 == 0:
                    cache_omgevingsplannen_1[url] = {
                        'name': name,
                        'category': category,
                        'content': content
                    }
                else:
                    cache_omgevingsplannen_2[url] = {
                        'name': name,
                        'category': category,
                        'content': content
                    }
                omgevingsplan_counter += 1
            else:
                # Overige wetgeving in aparte bestanden
                cache_other[url] = {
                    'name': name,
                    'category': category,
                    'content': content
                }

    # Sla de caches op in aparte JSON-bestanden
    save_cache_to_file(cache_omgevingsplannen_1, 'omgevingsplannen_1.json')
    save_cache_to_file(cache_omgevingsplannen_2, 'omgevingsplannen_2.json')
    print("Omgevingsplannen verdeeld en opgeslagen in omgevingsplannen_1.json en omgevingsplannen_2.json")

    # Sla overige wetgeving op in aparte JSON-bestanden
    for url, data in cache_other.items():
        filename = re.sub(r'\W+', '_', data['name'].lower()) + '.json'  # Bestandnaam op basis van naam
        save_cache_to_file({url: data}, filename)
        print(f"Overige wetgeving opgeslagen in {filename}")

# Uitvoeren van de cache-creatie met URLs uit urls.txt
def main():
    urls = read_urls('urls.txt')  # Lees de URLs uit het bestand
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_legislation_cache(urls))

if __name__ == "__main__":
    main()
