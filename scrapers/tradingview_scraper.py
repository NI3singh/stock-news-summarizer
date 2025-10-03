import requests
from bs4 import BeautifulSoup
import time
from config import Config
from fake_useragent import UserAgent

class TradingViewScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def scrape_news(self, ticker_symbol):
        """Scrape news from TradingView"""
        articles = []
        
        # TradingView uses different exchanges, try common ones
        exchanges = ['NASDAQ', 'NYSE', 'NSE']
        
        for exchange in exchanges:
            url = f'https://www.tradingview.com/symbols/{exchange}-{ticker_symbol}/news/'
            
            try:
                response = self.session.get(
                    url, 
                    headers=self.get_headers(),
                    timeout=Config.REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Try multiple selectors as TradingView structure changes
                    news_items = []
                    
                    # Method 1: Look for article tags
                    news_items = soup.find_all('article')
                    
                    # Method 2: Look for news-specific divs
                    if not news_items:
                        news_items = soup.find_all('div', class_=lambda x: x and 'news' in x.lower())
                    
                    # Method 3: Look for links with news-related patterns
                    if not news_items:
                        news_items = soup.find_all('a', href=lambda x: x and '/news/' in x)
                    
                    for item in news_items[:15]:  # Get top 15 articles
                        try:
                            # Extract title
                            title_elem = item.find(['h3', 'h2', 'h4', 'span', 'a'])
                            
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                
                                # Skip if title is too short or generic
                                if len(title) < 10:
                                    continue
                                
                                # Get link
                                link_elem = item.find('a', href=True)
                                if link_elem:
                                    link = link_elem.get('href', '')
                                else:
                                    link = item.get('href', '') if item.name == 'a' else ''
                                
                                if link and not link.startswith('http'):
                                    link = 'https://www.tradingview.com' + link
                                
                                # Skip if no valid link
                                if not link or len(link) < 10:
                                    continue
                                
                                # Extract date if available
                                date_elem = item.find('time')
                                pub_date = date_elem.get('datetime', '') if date_elem else ''
                                
                                # Extract snippet/content
                                content_elem = item.find('p')
                                content = content_elem.get_text(strip=True) if content_elem else title
                                
                                articles.append({
                                    'source': 'TradingView',
                                    'title': title,
                                    'url': link,
                                    'published_date': pub_date,
                                    'content': content
                                })
                        except Exception as e:
                            continue
                    
                    if articles:
                        break  # Found articles, no need to try other exchanges
                
                time.sleep(Config.RATE_LIMIT_DELAY)
                
            except Exception as e:
                print(f"Error scraping TradingView for {exchange}-{ticker_symbol}: {e}")
                continue
        
        # If TradingView fails, it's not critical - we have other sources
        print(f"TradingView: Found {len(articles)} articles for {ticker_symbol}")
        return articles