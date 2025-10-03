from scrapers.tradingview_scraper import TradingViewScraper
from scrapers.finviz_scraper import FinvizScraper
from scrapers.polygon_scraper import PolygonScraper
import time

class ScraperOrchestrator:
    """Orchestrates all scrapers to collect news from multiple sources"""
    
    def __init__(self):
        self.tradingview = TradingViewScraper()
        self.finviz = FinvizScraper()
        self.polygon = PolygonScraper()
    
    def scrape_all_sources(self, ticker_symbol):
        """
        Scrape news from all three sources for a given ticker
        Returns combined list of articles
        """
        print(f"\n{'='*60}")
        print(f"Starting news collection for {ticker_symbol}")
        print(f"{'='*60}")
        
        all_articles = []
        
        # Scrape TradingView
        print("\n[1/3] Scraping TradingView...")
        try:
            tv_articles = self.tradingview.scrape_news(ticker_symbol)
            all_articles.extend(tv_articles)
            print(f"✓ TradingView: {len(tv_articles)} articles")
        except Exception as e:
            print(f"✗ TradingView failed: {e}")
        
        time.sleep(2)  # Rate limiting between sources
        
        # Scrape Finviz
        print("\n[2/3] Scraping Finviz...")
        try:
            fv_articles = self.finviz.scrape_news(ticker_symbol)
            all_articles.extend(fv_articles)
            print(f"✓ Finviz: {len(fv_articles)} articles")
        except Exception as e:
            print(f"✗ Finviz failed: {e}")
        
        time.sleep(2)  # Rate limiting between sources
        
        # Scrape Polygon
        print("\n[3/3] Fetching from Polygon API...")
        try:
            pg_articles = self.polygon.scrape_news(ticker_symbol)
            all_articles.extend(pg_articles)
            print(f"✓ Polygon: {len(pg_articles)} articles")
        except Exception as e:
            print(f"✗ Polygon failed: {e}")
        
        # Remove duplicates based on title similarity
        all_articles = self._remove_duplicates(all_articles)
        
        print(f"\n{'='*60}")
        print(f"Collection complete for {ticker_symbol}")
        print(f"Total unique articles: {len(all_articles)}")
        print(f"{'='*60}\n")
        
        return all_articles
    
    def _remove_duplicates(self, articles):
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title_lower = article['title'].lower().strip()
            # Simple duplicate detection - can be enhanced
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_articles.append(article)
        
        return unique_articles