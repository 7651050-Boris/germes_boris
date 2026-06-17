#!/usr/bin/env python3
"""
Парсер кассовых сборов из ЕАИС (Фонд кино).
Использует JSON-эндпоинт: /ekb/top-films/
Так же парсит премьеры недели/месяца.

Usage:
  python3 eais_top10.py daily      # Top-10 дневные сборы
  python3 eais_top10.py weekend    # Итоги уикенда
  python3 eais_top10.py today      # Премьеры сегодня
  python3 eais_top10.py week       # Премьеры недели
  python3 eais_top10.py month      # Премьеры месяца
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
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def get_daily_top10():
    """Топ-10 за вчерашний день"""
    films = fetch_top_films()
    if not films:
        return {'error': 'Не удалось получить данные ЕАИС'}
    daily_films = [f for f in films if f.get('dsum', 0) > 0]
    daily_films.sort(key=lambda f: f['dsum'], reverse=True)
    date_yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    top10 = []
    for i, film in enumerate(daily_films[:10]):
        top10.append({
            'position': i + 1,
            'title': film.get('title', ''),
            'gross': film.get('dsum', 0),
            'gross_formatted': f"{film.get('dsum', 0):,} ₽".replace(',', ' ') if film.get('dsum', 0) else '—',
            'viewers': film.get('quantity', 0),
            'viewers_formatted': f"{film.get('quantity', 0):,}".replace(',', ' ') if film.get('quantity') else '—',
            'sessions': film.get('sessions', 0),
            'total_gross': film.get('money', 0),
            'total_gross_formatted': f"{film.get('money', 0):,} ₽".replace(',', ' ') if film.get('money') else '—',
        })
    return {'date': date_yesterday, 'total_films': len(daily_films), 'top10': top10}


def get_upcoming_premieres():
    """Предстоящие премьеры"""
    films = fetch_top_films()
    if not films:
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
                        'launch_date': launch_date.strftime('%d.%m.%Y'),
                        'genre': film.get('genre', ''),
                        'country': film.get('country', ''),
                        'age': film.get('ageRestr', '')
                    })
            except ValueError:
                pass
    upcoming.sort(key=lambda f: f['launch_date'])
    return upcoming


def format_daily_top10(data):
    """Форматирование дневного топа"""
    if 'error' in data:
        return f"❌ {data['error']}"
    d = datetime.strptime(data['date'], '%Y-%m-%d')
    lines = [f"🎬 **Кассовые сборы РФ за {d.strftime('%d.%m.%Y')}**\n"]
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


def format_week_premieres(upcoming):
    if isinstance(upcoming, dict) and 'error' in upcoming:
        return f"❌ {upcoming['error']}"
    now = datetime.now()
    week_end = now + timedelta(days=7)
    week_p = [f for f in upcoming if now <= datetime.strptime(f['launch_date'], '%d.%m.%Y') <= week_end]
    lines = ["📅 **Премьеры недели**\n"]
    if not week_p:
        lines.append("На этой неделе нет премьер.")
    else:
        for p in week_p:
            lines.append(f"• **{p['title']}** — {p.get('genre', '')} ({p.get('country', '')})")
            lines.append(f"   📅 {p['launch_date']}")
    return '\n'.join(lines)


def format_month_premieres(upcoming):
    if isinstance(upcoming, dict) and 'error' in upcoming:
        return f"❌ {upcoming['error']}"
    now = datetime.now()
    month_names = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                   5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                   9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}
    month_p = [f for f in upcoming if f['launch_date'].endswith(f'.{now.month:02d}.{now.year}')]
    lines = [f"📋 **Все премьеры {month_names[now.month]} {now.year}**\n"]
    if not month_p:
        lines.append("В этом месяце нет премьер.")
    else:
        for p in month_p:
            lines.append(f"• **{p['title']}** — {p.get('genre', '')} ({p.get('country', '')})")
            lines.append(f"   📅 {p['launch_date']}")
    return '\n'.join(lines)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'daily'
    if cmd == 'daily':
        d = get_daily_top10()
        # Если dsum=0 (нет дневных данных) — сообщаем, что нужен браузер
        if d.get('top10') and all(f['gross'] == 0 for f in d['top10']):
            print("⚠️ Дневные сборы недоступны через JSON. Используй браузер для парсинга страницы статистики.")
        else:
            print(format_daily_top10(d))
    elif cmd == 'today':
        print("🎬 Премьеры сегодня — используй браузер для Кинопоиска.")
    elif cmd == 'week':
        u = get_upcoming_premieres()
        print(format_week_premieres(u))
    elif cmd == 'month':
        u = get_upcoming_premieres()
        print(format_month_premieres(u))
    else:
        print("Usage: python3 eais_top10.py [daily|week|month]")
