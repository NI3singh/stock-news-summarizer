import sqlite3
from datetime import datetime
import json
from config import Config

class DatabaseManager:
    def __init__(self, db_path=Config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tickers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker_symbol TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                published_date TEXT,
                content TEXT,
                fetched_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_selected BOOLEAN DEFAULT 0,
                FOREIGN KEY (ticker_symbol) REFERENCES tickers(symbol)
            )
        ''')
        
        # Summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker_symbol TEXT NOT NULL,
                summary_date DATE NOT NULL,
                summary_text TEXT NOT NULL,
                what_changed_today TEXT,
                articles_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker_symbol) REFERENCES tickers(symbol),
                UNIQUE(ticker_symbol, summary_date)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_symbol ON tickers(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_ticker ON articles(ticker_symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_summary_ticker ON summaries(ticker_symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_summary_date ON summaries(summary_date)')
        
        conn.commit()
        conn.close()
    
    # Ticker operations
    def add_ticker(self, symbol):
        """Add a new ticker"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO tickers (symbol) VALUES (?)', (symbol.upper(),))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Ticker already exists, try to reactivate if it was deactivated
            cursor.execute('SELECT is_active FROM tickers WHERE symbol = ?', (symbol.upper(),))
            row = cursor.fetchone()
            if row and row[0] == 0:
                # Reactivate it
                cursor.execute('UPDATE tickers SET is_active = 1 WHERE symbol = ?', (symbol.upper(),))
                conn.commit()
                return True
            return False
        finally:
            conn.close()
    
    def get_all_tickers(self):
        """Get all active tickers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT symbol FROM tickers WHERE is_active = 1 ORDER BY added_date')
        tickers = [row['symbol'] for row in cursor.fetchall()]
        conn.close()
        return tickers
    
    def remove_ticker(self, symbol):
        """Deactivate a ticker"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tickers WHERE symbol = ?', (symbol.upper(),))
        conn.commit()
        conn.close()
    
    def reactivate_ticker(self, symbol):
        """Reactivate a previously deactivated ticker"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tickers SET is_active = 1 WHERE symbol = ?', (symbol.upper(),))
        conn.commit()
        conn.close()
    
    # Article operations
    def save_articles(self, ticker_symbol, articles):
        """Save fetched articles"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for article in articles:
            cursor.execute('''
                INSERT INTO articles (ticker_symbol, source, title, url, published_date, content)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                ticker_symbol.upper(),
                article.get('source'),
                article.get('title'),
                article.get('url'),
                article.get('published_date'),
                article.get('content', '')
            ))
        
        conn.commit()
        conn.close()
    
    def get_articles_for_ticker(self, ticker_symbol, days=1):
        """Get articles for a ticker from last N days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, source, title, url, published_date, content, is_selected
            FROM articles
            WHERE ticker_symbol = ? 
            AND date(fetched_date) >= date('now', '-' || ? || ' days')
            ORDER BY fetched_date DESC
        ''', (ticker_symbol.upper(), days))
        
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return articles
    
    def mark_articles_selected(self, article_ids):
        """Mark articles as selected for summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(article_ids))
        cursor.execute(f'UPDATE articles SET is_selected = 1 WHERE id IN ({placeholders})', article_ids)
        conn.commit()
        conn.close()
    
    # Summary operations
    def save_summary(self, ticker_symbol, summary_text, what_changed, articles_used):
        """Save daily summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT OR REPLACE INTO summaries 
            (ticker_symbol, summary_date, summary_text, what_changed_today, articles_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            ticker_symbol.upper(),
            today,
            summary_text,
            what_changed,
            json.dumps(articles_used)
        ))
        
        conn.commit()
        conn.close()
    
    def get_summaries_for_ticker(self, ticker_symbol, days=7):
        """Get summaries for last N days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT summary_date, summary_text, what_changed_today, articles_used, created_at
            FROM summaries
            WHERE ticker_symbol = ?
            AND date(summary_date) >= date('now', '-' || ? || ' day')
            ORDER BY summary_date DESC
        ''', (ticker_symbol.upper(), days))
        
        summaries = []
        for row in cursor.fetchall():
            summary = dict(row)
            try:
                summary['articles_used'] = json.loads(summary['articles_used']) if summary['articles_used'] else []
            except:
                summary['articles_used'] = []
            summaries.append(summary)
        
        conn.close()
        return summaries
    
    def get_latest_summary(self, ticker_symbol):
        """Get the most recent summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT summary_date, summary_text, what_changed_today, articles_used, created_at
            FROM summaries
            WHERE ticker_symbol = ?
            ORDER BY summary_date DESC
            LIMIT 1
        ''', (ticker_symbol.upper(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            summary = dict(row)
            summary['articles_used'] = json.loads(summary['articles_used'])
            return summary
        return None