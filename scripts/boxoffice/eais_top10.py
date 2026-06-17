#!/usr/bin/env python3
"""
Парсер кассовых сборов из ЕАИС (Фонд кино).
Использует JSON-эндпоинт: /ekb/top-films/
Так же парсит премьеры недели/месяца.
"""

import urllib.request
import json
import sys
from datetime import datetime, timedelta

EAIS_URL = 'https://ekinobilet.fond-kino.ru'
TOP_FILMS_URL = f'{EAIS_URL}/ekb/top-films/'


def fetch_top_films():
    """Загружает JSON со всеми фильмами из ЕАИС"""
    req = urllib.request.Request(
        TOP_FILMS_URL,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{EAIS_URL}/statistics/',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return None


def get_daily_top10():
    """
    Собирает топ-10 за вчерашний день из данных ЕАИС.
    Сортирует по сборам (поле dsum = daily sum).
    """
    films = fetch_top_films()
    if films is None:
        return {'error': 'Не удалось получить данные ЕАИС'}
    
    # Фильтруем: те, у кого есть ежедневные сборы (dsum > 0)
    daily_films = [f for f in films if f.get('dsum', 0) > 0]
    
    # Сортируем по дневным сборам (dsum)
    daily_films.sort(key=lambda f: f['dsum'], reverse=True)
    
    date_yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    top10 = []
    for i, film in enumerate(daily_films[:10]):
        top10.append({
            'position': i + 1,
            'title': film.get('title', ''),
            'title_en': film.get('title_en', ''),
            'gross': film.get('dsum', 0),
            'gross_formatted': f"{film.get('dsum', 0):,} ₽".replace(',', ' ') if film.get('dsum', 0) else '—',
            'viewers': film.get('quantity', 0),
            'viewers_formatted': f"{film.get('quantity', 0):,}".replace(',', ' ') if film.get('quantity', 0) else '—',
            'sessions': film.get('sessions', 0),
            'total_gross': film.get('money', 0),
            'total_gross_formatted': f"{film.get('money', 0):,} ₽".replace(',', ' ') if film.get('money', 0) else '—',
            'genre': film.get('genre', ''),
            'distributor': film.get('distributor', ''),
            'age': film.get('ageRestr', ''),
            'country': film.get('country', '')
        })
    
    return {
        'date': date_yesterday,
        'total_films': len(daily_films),
        'top10': top10
    }


def get_alltime_top10():
    """Топ-10 за всё время (общие сборы)"""
    films = fetch_top_films()
    if films is None:
        return {'error': 'Не удалось получить данные'}
    
    films.sort(key=lambda f: f.get('money', 0) or 0, reverse=True)
    
    top10 = []
    for i, film in enumerate(films[:10]):
        top10.append({
            'position': i + 1,
            'title': film.get('title', ''),
            'total_gross': film.get('money', 0),
            'total_gross_formatted': f"{film.get('money', 0):,} ₽".replace(',', ' ') if film.get('money', 0) else '—',
            'viewers': film.get('tickets', 0),
            'year': film.get('year', ''),
            'country': film.get('country', ''),
            'genre': film.get('genre', ''),
            'distributor': film.get('distributor', '')
        })
    
    return top10


def get_upcoming_premieres():
    """
    Собирает предстоящие премьеры из ЕАИС.
    Фильмы с датой старта в будущем, сортировка по дате.
    """
    films = fetch_top_films()
    if films is None:
        return {'error': 'Не удалось получить данные'}
    
    today = datetime.now()
    upcoming = []
    
    for film in films:
        launch_str = film.get('launch_date', '')
        if launch_str:
            try:
                launch_date = datetime.strptime(launch_str.split('T')[0], '%Y.%m.%d')
                if launch_date > today:
                    upcoming.append({
                        'title': film.get('title', ''),
                        'title_en': film.get('title_en', ''),
                        'launch_date': launch_date.strftime('%d.%m.%Y'),
                        'genre': film.get('genre', ''),
                        'country': film.get('country', ''),
                        'distributor': film.get('distributor', ''),
                        'age': film.get('ageRestr', '')
                    })
            except ValueError:
                pass
    
    upcoming.sort(key=lambda f: f['launch_date'])
    return upcoming


def format_daily_top10(data):
    """Форматирует дневной топ-10 для Telegram"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    d = datetime.strptime(data['date'], '%Y-%m-%d')
    date_ru = d.strftime('%d.%m.%Y')
    
    lines = [f"🎬 **Кассовые сборы РФ за {date_ru}**\n"]
    
    total_gross = 0
    total_viewers = 0
    
    for film in data['top10']:
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(film['position'], f"{film['position']}.")
        lines.append(f"{medal} **{film['title']}**")
        lines.append(f"   💰 {film['gross_formatted']} | 👥 {film['viewers_formatted']}")
        total_gross += film['gross']
        total_viewers += film['viewers']
    
    lines.append(f"\n💰 **Сумма топ-10:** {total_gross:,} ₽".replace(',', ' '))
    lines.append(f"👥 **Всего зрителей топ-10:** {total_viewers:,}".replace(',', ' '))
    lines.append(f"📊 ЕАИС (Фонд кино)")
    
    return '\n'.join(lines)


def format_weekend_summary(data):
    """Итоги уикенда с анализом (пн-вс)"""
    if 'error' in data:
        return f"❌ {data['error']}"
    
    lines = ["📊 **Итоги уикенда**\n"]
    
    for film in data['top10'][:5]:
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(film['position'], f"{film['position']}.")
        lines.append(f"{medal} **{film['title']}**")
        lines.append(f"   💰 {film['gross_formatted']} | 👥 {film['viewers_formatted']}")
        if film.get('total_gross'):
            lines.append(f"   📈 Всего: {film['total_gross_formatted']}")
    
    total_gross = sum(f['gross'] for f in data['top10'])
    total_viewers = sum(f['viewers'] for f in data['top10'])
    lines.append(f"\n💰 **Общие сборы топ-10:** {total_gross:,} ₽".replace(',', ' '))
    lines.append(f"👥 **Всего зрителей:** {total_viewers:,}".replace(',', ' '))
    lines.append(f"📊 ЕАИС (Фонд кино)")
    
    return '\n'.join(lines)


def format_today_premieres(upcoming):
    """Форматирует премьеры сегодня"""
    if isinstance(upcoming, dict) and 'error' in upcoming:
        return f"❌ {upcoming['error']}"
    
    today_str = datetime.now().strftime('%d.%m.%Y')
    today_premieres = [f for f in upcoming if f.get('launch_date') == today_str]
    
    lines = [f"🎬 **Премьеры сегодня ({today_str})**\n"]
    
    if not today_premieres:
        lines.append("Сегодня нет премьер.")
    else:
        for p in today_premieres[:15]:
            genre_str = f" — {p['genre']}" if p.get('genre') else ""
            country_str = f" ({p['country']})" if p.get('country') else ""
            age_str = f" [{p['age']}+]" if p.get('age') else ""
            lines.append(f"• **{p['title']}**{genre_str}{country_str}{age_str}")
    
    return '\n'.join(lines)


def format_week_premieres(upcoming):
    """Форматирует премьеры недели"""
    if isinstance(upcoming, dict) and 'error' in upcoming:
        return f"❌ {upcoming['error']}"
    
    now = datetime.now()
    week_end = now + timedelta(days=7)
    
    week_premieres = []
    for f in upcoming:
        try:
            fd = datetime.strptime(f['launch_date'], '%d.%m.%Y')
            if now <= fd <= week_end:
                week_premieres.append(f)
        except:
            pass
    
    lines = ["📅 **Премьеры недели**\n"]
    
    if not week_premieres:
        lines.append("На этой неделе нет премьер.")
    else:
        for p in week_premieres:
            genre_str = f" — {p['genre']}" if p.get('genre') else ""
            country_str = f" ({p['country']})" if p.get('country') else ""
            age_str = f" [{p['age']}+]" if p.get('age') else ""
            lines.append(f"• **{p['title']}**{genre_str}{country_str}")
            lines.append(f"   📅 {p['launch_date']}{age_str}")
    
    return '\n'.join(lines)


def format_all_month_premieres(upcoming):
    """Форматирует все премьеры месяца"""
    if isinstance(upcoming, dict) and 'error' in upcoming:
        return f"❌ {upcoming['error']}"
    
    now = datetime.now()
    month = now.month
    year = now.year
    
    month_premieres = [f for f in upcoming if f['launch_date'].endswith(f'.{month:02d}.{year}') or 
                       f['launch_date'].endswith(f'.{month:02d}')]
    
    month_names = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                   5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                   9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}
    
    lines = [f"📋 **Все премьеры {month_names[month]} {year}**\n"]
    
    if not month_premieres:
        lines.append("В этом месяце нет премьер.")
    else:
        for p in month_premieres:
            genre_str = f" — {p['genre']}" if p.get('genre') else ""
            country_str = f" ({p['country']})" if p.get('country') else ""
            lines.append(f"• **{p['title']}**{genre_str}{country_str}")
            lines.append(f"   📅 {p['launch_date']}")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = 'daily'
    
    if cmd == 'daily':
        data = get_daily_top10()
        print(format_daily_top10(data))
    elif cmd == 'weekend':
        data = get_daily_top10()
        print(format_weekend_summary(data))
    elif cmd == 'today':
        upcoming = get_upcoming_premieres()
        print(format_today_premieres(upcoming))
    elif cmd == 'week':
        upcoming = get_upcoming_premieres()
        print(format_week_premieres(upcoming))
    elif cmd == 'month':
        upcoming = get_upcoming_premieres()
        print(format_all_month_premieres(upcoming))
    else:
        print(f"Неизвестная команда: {cmd}")
        print("Использование: python3 eais_top10.py [daily|weekend|today|week|month]")
