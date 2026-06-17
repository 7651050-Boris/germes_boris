#!/usr/bin/env python3
"""
Парсер премьер недели/месяца с Кинопоиска и ЕАИС.
"""

import urllib.request
import re
import json
from datetime import datetime, timedelta

# ========= Кинопоиск =========

def fetch_kinopoisk_premieres(week=True):
    """
    Парсит страницу «Скоро в кино» на Кинопоиске.
    Можно получить премьеры недели или месяца.
    """
    url = 'https://www.kinopoisk.ru/premiere/'
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        return {"error": f"Кинопоиск недоступен: {e}"}
    
    premieres = []
    
    # Ищем блоки премьер
    # Паттерн: название фильма, дата, жанр
    film_blocks = re.findall(
        r'<div[^>]*class="[^"]*premiereItem[^"]*"[^>]*>.*?'
        r'<div[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</div>.*?'
        r'<div[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</div>.*?'
        r'<div[^>]*class="[^"]*genre[^"]*"[^>]*>(.*?)</div>',
        html, re.DOTALL
    )
    
    # Если не сработало — другой паттерн
    if not film_blocks:
        film_blocks = re.findall(
            r'<a[^>]*class="[^"]*filmName[^"]*"[^>]*>(.*?)</a>.*?'
            r'<span[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</span>',
            html, re.DOTALL
        )
    
    if not film_blocks:
        # Ещё один вариант — ищем названия фильмов и даты
        items = re.findall(
            r'<a[^>]*href="/film/\d+/"[^>]*>(.*?)</a>',
            html
        )
        dates = re.findall(r'(\d+\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})', html)
        
        for i, item in enumerate(items):
            name = re.sub(r'<[^>]+>', '', item).strip()
            if name and len(name) > 2:
                date = dates[i] if i < len(dates) else ''
                premieres.append({
                    'title': name,
                    'date': date,
                    'genre': ''
                })
    else:
        for block in film_blocks:
            name = re.sub(r'<[^>]+>', '', block[0]).strip()
            date = re.sub(r'<[^>]+>', '', block[1]).strip()
            genre = re.sub(r'<[^>]+>', '', block[2]).strip() if len(block) > 2 else ''
            
            if name:
                premieres.append({
                    'title': name,
                    'date': date,
                    'genre': genre
                })
    
    return {
        'source': 'kinopoisk.ru',
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total': len(premieres),
        'premieres': premieres
    }


# ========= ЕАИС - Каталог фильмов =========

def fetch_eais_catalog(page=1, per_page=20):
    """Парсит каталог фильмов ЕАИС"""
    url = f'https://ekinobilet.fond-kino.ru/catalog/films/?page={page}&per-page={per_page}'
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        return {"error": f"Каталог ЕАИС недоступен: {e}"}
    
    films = []
    
    # Ищем блоки карточек фильмов
    cards = re.findall(
        r'<div[^>]*class="[^"]*film-card[^"]*"[^>]*>.*?'
        r'<a[^>]*href="/catalog/film/\d+"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    
    # Пробуем другой паттерн
    if not cards:
        # Вытаскиваем все названия со страницы каталога
        titles = re.findall(
            r'<a[^>]*href="/catalog/film/\d+"[^>]*>(.*?)</a>',
            html
        )
        for title in titles:
            clean = re.sub(r'<[^>]+>', '', title).strip()
            if clean:
                films.append({'title': clean})
    
    return {
        'source': 'eais.fond-kino.ru',
        'page': page,
        'total': len(films),
        'films': films
    }


# ========= Форматирование =========

def format_today_premieres(data):
    """Форматирует премьеры дня"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    today = datetime.now().strftime('%d %B')
    lines = [f"🎬 **Премьеры сегодня ({today})**\n"]
    
    for p in data['premieres'][:15]:
        date_str = f" ({p['date']})" if p['date'] else ""
        genre_str = f" — {p['genre']}" if p['genre'] else ""
        lines.append(f"• **{p['title']}**{genre_str}{date_str}")
    
    if not data['premieres']:
        lines.append("Нет данных о премьерах.")
    
    return '\n'.join(lines)


def format_week_premieres(data):
    """Форматирует премьеры недели"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    lines = ["📅 **Премьеры недели**\n"]
    
    for p in data['premieres'][:20]:
        genre_str = f" — {p['genre']}" if p['genre'] else ""
        date_str = f" ({p['date']})" if p['date'] else ""
        lines.append(f"• **{p['title']}**{genre_str}{date_str}")
    
    if not data['premieres']:
        lines.append("Нет данных.")
    
    return '\n'.join(lines)


def format_month_premieres(data):
    """Форматирует все премьеры месяца"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    month_name = {
        1: 'январь', 2: 'февраль', 3: 'март', 4: 'апрель',
        5: 'май', 6: 'июнь', 7: 'июль', 8: 'август',
        9: 'сентябрь', 10: 'октябрь', 11: 'ноябрь', 12: 'декабрь'
    }
    month = month_name.get(datetime.now().month, '')
    
    lines = [f"📋 **Все премьеры {month}**\n"]
    
    for p in data['premieres']:
        genre_str = f" — {p['genre']}" if p['genre'] else ""
        date_str = f" ({p['date']})" if p['date'] else ""
        lines.append(f"• **{p['title']}**{genre_str}{date_str}")
    
    if not data['premieres']:
        lines.append("Нет данных.")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'today':
        data = fetch_kinopoisk_premieres(week=False)
        print(format_today_premieres(data))
    elif len(sys.argv) > 1 and sys.argv[1] == 'month':
        data = fetch_kinopoisk_premieres(week=False)
        print(format_month_premieres(data))
    else:
        data = fetch_kinopoisk_premieres(week=True)
        print(format_week_premieres(data))
        print('\n' + '='*40)
        print('\nJSON:')
        print(json.dumps(data, ensure_ascii=False, indent=2))
