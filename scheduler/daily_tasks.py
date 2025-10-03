from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime
from config import Config
from database.models import DatabaseManager
from scrapers import ScraperOrchestrator
from ai.gemini_processor import GeminiProcessor

class DailyTaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = DatabaseManager()
        self.scraper = ScraperOrchestrator()
        self.ai_processor = GeminiProcessor()
        self.timezone = pytz.timezone(Config.TIMEZONE)
    
    def daily_refresh_task(self):
        """Main task that runs daily at scheduled time"""
        print(f"\n{'#'*70}")
        print(f"# DAILY REFRESH STARTED AT {datetime.now(self.timezone)}")
        print(f"{'#'*70}\n")
        
        tickers = self.db.get_all_tickers()
        
        if not tickers:
            print("No tickers found. Nothing to refresh.")
            return
        
        print(f"Processing {len(tickers)} ticker(s): {', '.join(tickers)}\n")
        
        for ticker in tickers:
            try:
                self.process_single_ticker(ticker)
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue
        
        print(f"\n{'#'*70}")
        print(f"# DAILY REFRESH COMPLETED AT {datetime.now(self.timezone)}")
        print(f"{'#'*70}\n")
    
    def process_single_ticker(self, ticker_symbol):
        """Process a single ticker: scrape, analyze, summarize"""
        print(f"\n{'*'*70}")
        print(f"Processing: {ticker_symbol}")
        print(f"{'*'*70}")
        
        # Step 1: Scrape all sources
        all_articles = self.scraper.scrape_all_sources(ticker_symbol)
        
        if not all_articles:
            print(f"No articles found for {ticker_symbol}. Skipping.")
            return
        
        # Step 2: Save articles to database
        self.db.save_articles(ticker_symbol, all_articles)
        print(f"✓ Saved {len(all_articles)} articles to database")
        
        # Step 3: Get historical summaries for context
        historical_summaries = self.db.get_summaries_for_ticker(
            ticker_symbol, 
            days=Config.HISTORY_DAYS
        )
        
        # Step 4: AI Processing
        result = self.ai_processor.process_ticker_news(
            ticker_symbol,
            all_articles,
            historical_summaries
        )
        
        if not result:
            print(f"AI processing failed for {ticker_symbol}")
            return
        
        # Step 5: Mark selected articles
        selected_article_ids = [
            a.get('article_id') for a in result['selected_articles'] 
            if a.get('article_id')
        ]
        if selected_article_ids:
            self.db.mark_articles_selected(selected_article_ids)
        
        # Step 6: Save summary
        articles_used = [
            {
                'title': a['title'],
                'url': a['url'],
                'source': a['source']
            }
            for a in result['selected_articles']
        ]
        
        self.db.save_summary(
            ticker_symbol,
            result['main_summary'],
            result['what_changed_today'],
            articles_used
        )
        
        print(f"✓ Summary saved for {ticker_symbol}")
        print(f"{'*'*70}\n")
    
    def start(self):
        """Start the scheduler"""
        # Parse scheduled time (format: HH:MM)
        hour, minute = map(int, Config.REFRESH_TIME.split(':'))
        
        # Schedule daily task
        self.scheduler.add_job(
            self.daily_refresh_task,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
                timezone=self.timezone
            ),
            id='daily_refresh',
            name='Daily News Refresh',
            replace_existing=True
        )
        
        print(f"\n{'='*70}")
        print(f"Scheduler started!")
        print(f"Daily refresh scheduled at: {Config.REFRESH_TIME} {Config.TIMEZONE}")
        print(f"{'='*70}\n")
        
        self.scheduler.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped.")
    
    def run_now(self):
        """Manually trigger the daily task (for testing)"""
        print("Manual refresh triggered...")
        self.daily_refresh_task()