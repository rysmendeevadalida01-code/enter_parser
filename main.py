import csv
import json
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://enter.kg/'
CATEGORY_PATH = 'computers/noutbuki_bishkek'

class_names = {
    'name': 'rows',
    'price': 'price',
    'articul': 'sku'
}

def get_html(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'html.parser')

def extract_simple_specs(text: str) -> dict:
    specs = {'gb': 'None', 'screen': 'None'}
    
    def extract_simple_specs(text: str) -> dict:
        specs = {'gb': 'None', 'screen': 'None'}
        
        words = text.split()
        
        for word in words:
            word_clean = word.strip(',()') # убираем лишние запятые и скобки вокруг слова
            word_lower = word_clean.lower()
            
            if 'gb' in word_lower or 'tb' in word_lower or 'гб' in word_lower:
                specs['gb'] = word_clean
                
            elif '"' in word_clean:
                specs['screen'] = word_clean
                
        return specs

def parse_cards(soup: BeautifulSoup) -> list[dict]:
    result = []
    
    cards = soup.find_all('div', class_='product') or soup.find_all('div', class_='product-container')
    
    if not cards:
        name_elements = soup.find_all('span', class_=class_names['name'])
        cards = [elem.find_parent('div') for elem in name_elements if elem.find_parent('div')]

    for card in cards:
        try:
            name_elem = card.find('span', class_=class_names['name']) or card.find(class_=class_names['name'])
            if not name_elem:
                continue
            name = name_elem.get_text(strip=True)

            articul_elem = card.find('span', class_=class_names['articul']) or card.find(class_=class_names['articul'])
            articul = 'None'
            if articul_elem:
                articul = articul_elem.get_text(strip=True).replace('Артикул:', '').strip()
            
            price_elem = card.find('span', class_=class_names['price']) or card.find(class_=class_names['price'])
            price = 0
            if price_elem:
                price_str = price_elem.get_text(strip=True)
                price_digits = ''.join(filter(str.isdigit, price_str))
                price = int(price_digits) if price_digits else 0
            
            specs = extract_simple_specs(name)
            
            result.append({
                'name': name,
                'articul': articul,
                'price': price,
                'gb': specs['gb'],
                'screen': specs['screen']
            })
        except Exception:
            continue
            
    return result

def save_to_json(data: list[dict], filename: str) -> None:
    with open(f'{filename}.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"-> Успешно сохранен файл: {filename}.json")

def save_to_csv(data: list[dict], filename: str) -> None:
    if not data:
        return
    with open(f'{filename}.csv', 'w', encoding='utf-8', newline='') as file:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f" Успешно сохранен файл: {filename}.csv")

def parse_notebooks(total_pages: int = 3) -> list[dict]:
    all_products = []
    
    for page in range(1, total_pages + 1):
        if page == 1:
            url = f"{BASE_URL}{CATEGORY_PATH}"
        else:
            start_num = (page - 1) * 20 + 1
            end_num = page * 20
            url = f"{BASE_URL}{CATEGORY_PATH}/results,{start_num}-{end_num}"
            
        print(f"Парсим страницу {page}... Ссылка: {url}")
        
        try:
            html = get_html(url)
            soup = get_soup(html)
            products_from_page = parse_cards(soup)
            
            if not products_from_page:
                print(f"На странице {page} товаров не найдено.")
                break
                
            print(f"Найдено {len(products_from_page)} ноутбуков на странице {page}.")
            all_products.extend(products_from_page)
            
        except Exception as e:
            print(f"Ошибка загрузки страницы {page}: {e}")
            break
            
    return all_products

if _name_ == '_main_':
    filename = 'noutbuki_bishkek'
    print(f"Запуск парсинга ноутбуков ({CATEGORY_PATH})...")
    
    notebooks_data = parse_notebooks(total_pages=3)
    
    if notebooks_data:
        save_to_csv(notebooks_data, filename)
        save_to_json(notebooks_data, filename)
        print(f"\nГотово! Всего собрано ноутбуков: {len(notebooks_data)}")
    else:
        print("\nНе удалось собрать данные. Проверь интернет-соединение или структуру сайта.")
