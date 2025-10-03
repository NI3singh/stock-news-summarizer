import requests
from bs4 import BeautifulSoup
import time
from config import Config
from fake_useragent import UserAgent

class FinvizScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def scrape_news(self, ticker_symbol):
        """Scrape news from Finviz"""
        articles = []
        url = f'https://finviz.com/quote.ashx?t={ticker_symbol}'
        
        try:
            response = self.session.get(
                url,
                headers=self.get_headers(),
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Find news table
                news_table = soup.find('table', {'id': 'news-table'})
                
                if news_table:
                    rows = news_table.find_all('tr')
                    
                    current_date = None
                    for row in rows[:20]:  # Get top 20 articles
                        try:
                            cols = row.find_all('td')
                            
                            if len(cols) >= 2:
                                # First column contains date/time
                                date_cell = cols[0].get_text(strip=True)
                                
                                # Check if it's a new date or just time
                                if len(date_cell.split()) > 1:
                                    current_date = date_cell
                                else:
                                    date_cell = f"{current_date.split()[0]} {date_cell}"
                                
                                # Second column contains link and title
                                link_elem = cols[1].find('a')
                                if link_elem:
                                    title = link_elem.get_text(strip=True)
                                    link = link_elem.get('href', '')
                                    
                                    # Get source
                                    source_elem = cols[1].find('span')
                                    source = source_elem.get_text(strip=True) if source_elem else 'Finviz'
                                    
                                    articles.append({
                                        'source': f'Finviz ({source})',
                                        'title': title,
                                        'url': link,
                                        'published_date': date_cell,
                                        'content': title  # Finviz doesn't provide snippets
                                    })
                        except Exception as e:
                            print(f"Error parsing Finviz row: {e}")
                            continue
            
            time.sleep(Config.RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"Error scraping Finviz for {ticker_symbol}: {e}")
        
        print(f"Finviz: Found {len(articles)} articles for {ticker_symbol}")
        return articles