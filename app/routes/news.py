from datetime import datetime

import requests
from flask import Blueprint, current_app, jsonify, render_template, request

from app.models import News

bp = Blueprint('news', __name__)


@bp.route('/news')
def news():
    articles = []
    error = None
    search_query = request.args.get('q', '').strip()

    try:
        api_key = current_app.config.get('NEWS_API_KEY', '')
        if api_key:
            articles = _fetch_external_news(api_key, query=search_query)
        else:
            query = News.query
            if search_query:
                query = query.filter(News.title.ilike(f'%{search_query}%') | News.content.ilike(f'%{search_query}%'))
            articles = [
                item.to_dict() for item in (
                    query.order_by(News.published_date.desc()).limit(20)
                )
            ]
    except Exception as exc:
        error = str(exc)

    if not articles and not search_query:
        articles = _fallback_news()

    # Place flood-related news at the very top
    articles.sort(key=lambda x: not bool(x.get('is_flood_related', False)))

    return render_template('news.html', articles=articles, error=error, search_query=search_query)


@bp.route('/api/news')
def api_news():
    api_key = current_app.config.get('NEWS_API_KEY', '')
    search_query = request.args.get('q', '').strip()
    try:
        if api_key:
            articles = _fetch_external_news(api_key, query=search_query)
        else:
            query = News.query
            if search_query:
                query = query.filter(News.title.ilike(f'%{search_query}%') | News.content.ilike(f'%{search_query}%'))
            articles = [
                item.to_dict() for item in (
                    query.order_by(News.published_date.desc()).limit(20)
                )
            ]

        if not articles and not search_query:
            articles = _fallback_news()

        articles.sort(key=lambda x: not bool(x.get('is_flood_related', False)))

        return jsonify({
            'status': 'ok',
            'articles': articles,
            'requires_api_key': not bool(api_key)
        })
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 503


def _fetch_external_news(api_key, query=None):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    q = query if query else 'Guntur OR "Andhra Pradesh" OR flood OR rainfall OR municipal OR weather'

    raw_articles = []
    seen_titles = set()

    # 1. Fetch Top Headlines (country=in) as requested
    try:
        top_resp = requests.get(
            'https://newsapi.org/v2/top-headlines',
            headers=headers,
            params={
                'country': 'in',
                'pageSize': 20,
                'apiKey': api_key,
            },
            timeout=8,
        )
        if top_resp.status_code == 200:
            top_data = top_resp.json().get('articles') or []
            for art in top_data:
                title = (art.get('title') or '').strip().lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    raw_articles.append(art)
    except Exception:
        pass

    # Fallback/Additional top headlines search if country=in returned empty
    if not raw_articles:
        try:
            top_gen = requests.get(
                'https://newsapi.org/v2/top-headlines',
                headers=headers,
                params={
                    'category': 'general',
                    'pageSize': 15,
                    'apiKey': api_key,
                },
                timeout=8,
            )
            if top_gen.status_code == 200:
                gen_data = top_gen.json().get('articles') or []
                for art in gen_data:
                    title = (art.get('title') or '').strip().lower()
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        raw_articles.append(art)
        except Exception:
            pass

    # 2. Fetch Everything endpoint news for targeted query
    try:
        every_resp = requests.get(
            'https://newsapi.org/v2/everything',
            headers=headers,
            params={
                'q': q,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 25,
                'apiKey': api_key,
            },
            timeout=8,
        )
        if every_resp.status_code == 200:
            every_data = every_resp.json().get('articles') or []
            for art in every_data:
                title = (art.get('title') or '').strip().lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    raw_articles.append(art)
    except Exception:
        pass

    formatted_articles = []
    for article in raw_articles:
        raw_date = article.get('publishedAt')
        formatted_date = raw_date
        if raw_date:
            try:
                dt = datetime.strptime(raw_date.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                formatted_date = dt.strftime('%d %b %Y, %I:%M %p')
            except Exception:
                formatted_date = raw_date[:10] if len(raw_date) >= 10 else raw_date

        formatted_articles.append({
            'title': article.get('title') or 'Untitled News',
            'content': (
                article.get('description')
                or article.get('content')
                or 'No content preview available.'
            ),
            'category': 'external',
            'source': (
                (article.get('source') or {}).get('name')
                or 'NewsAPI'
            ),
            'is_flood_related': _is_flood_related(article),
            'published_date': formatted_date,
            'image_url': article.get('urlToImage'),
            'external_url': article.get('url'),
        })
    return formatted_articles


def _is_flood_related(article):
    text = ' '.join([
        article.get('title') or '',
        article.get('description') or '',
        article.get('content') or '',
    ]).lower()
    keywords = [
        'flood', 'rain', 'rainfall', 'storm', 'waterlogging', 'monsoon',
        'inundat', 'cyclone', 'deluge', 'landslide', 'overflow', 'waterlog', 'drainage'
    ]
    return any(keyword in text for keyword in keywords)


def _fallback_news():
    now = f"{datetime.utcnow().isoformat()}Z"
    return [
        {
            'title': 'Municipal flood safety & urban drainage advisory',
            'content': (
                'Guntur Municipal Corporation asks citizens to stay safe during heavy monsoon rains '
                'and report waterlogging issues on the Jal Suraksha portal.'
            ),
            'category': 'general',
            'source': 'Guntur Municipal Corporation',
            'is_flood_related': True,
            'published_date': now,
            'image_url': None,
            'external_url': None,
        }
    ]
