import requests
import time
from datetime import datetime, timedelta
from config import Config

class PolygonScraper:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.POLYGON_API_KEY
        self.base_url = 'https://api.polygon.io/v2'
        
    def scrape_news(self, ticker_symbol):
        """Fetch news from Polygon API"""
        articles = []
        
        if not self.api_key:
            print("Polygon API key not configured")
            return articles
        
        # Get news from last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f'{self.base_url}/reference/news'
        params = {
            'ticker': ticker_symbol.upper(),
            'published_utc.gte': start_date.strftime('%Y-%m-%d'),
            'published_utc.lte': end_date.strftime('%Y-%m-%d'),
            'order': 'desc',
            'limit': 20,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and 'results' in data:
                    for item in data['results']:
                        articles.append({
                            'source': f"Polygon ({item.get('publisher', {}).get('name', 'Unknown')})",
                            'title': item.get('title', ''),
                            'url': item.get('article_url', ''),
                            'published_date': item.get('published_utc', ''),
                            'content': item.get('description', '')
                        })
            elif response.status_code == 429:
                print("Polygon API rate limit reached")
            else:
                print(f"Polygon API error: {response.status_code}")
            
            time.sleep(Config.RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"Error fetching from Polygon API for {ticker_symbol}: {e}")
        
        print(f"Polygon: Found {len(articles)} articles for {ticker_symbol}")
        return articles