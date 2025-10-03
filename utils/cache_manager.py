from cachetools import TTLCache
import time

# Simple cache for articles (1 hour TTL)
article_cache = TTLCache(maxsize=100, ttl=3600)

def get_cached_articles(ticker):
    """Get cached articles for a ticker"""
    cache_key = f"{ticker}_{time.strftime('%Y-%m-%d')}"
    return article_cache.get(cache_key)

def set_cached_articles(ticker, articles):
    """Cache articles for a ticker"""
    cache_key = f"{ticker}_{time.strftime('%Y-%m-%d')}"
    article_cache[cache_key] = articles

def clear_cache():
    """Clear all cached articles"""
    article_cache.clear()