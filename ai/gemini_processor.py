import google.generativeai as genai
from config import Config
import json
import time

class GeminiProcessor:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        else:
            raise ValueError("Gemini API key not configured")
    
    def select_top_articles(self, articles, ticker_symbol):
        """
        First AI prompt: Select top 5-7 most relevant articles
        """
        if not articles:
            return []
        
        # Prepare articles list for AI
        articles_text = ""
        for idx, article in enumerate(articles, 1):
            articles_text += f"\n{idx}. Title: {article['title']}\n"
            articles_text += f"   Source: {article['source']}\n"
            articles_text += f"   Date: {article.get('published_date', 'N/A')}\n"
            articles_text += f"   Content: {article.get('content', 'N/A')[:200]}...\n"
            articles_text += f"   URL: {article['url']}\n"
        
        prompt = f"""You are a financial analyst helping traders make informed decisions about {ticker_symbol}.

Below are news articles collected from multiple sources. Your task is to select the TOP 5-7 most relevant and credible articles that would be most valuable for understanding recent developments about {ticker_symbol}.

Selection Criteria:
1. Credibility: Prioritize articles from reputable financial sources
2. Relevance: Focus on articles directly about {ticker_symbol}'s business, financials, or market performance
3. Recency: Prefer more recent articles
4. Impact: Select articles that discuss significant events, earnings, leadership changes, or market-moving news
5. Avoid: Generic market commentary, duplicate information, or tangentially related news

Articles:
{articles_text}

Return your selection as a JSON array of article numbers only. Example format:
[1, 3, 5, 8, 12]

Select between 5-7 articles. Return ONLY the JSON array, no other text."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            if '[' in response_text and ']' in response_text:
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                json_str = response_text[start:end]
                selected_indices = json.loads(json_str)
                
                # Get selected articles
                selected_articles = []
                for idx in selected_indices:
                    if 1 <= idx <= len(articles):
                        article = articles[idx - 1].copy()
                        article['article_id'] = idx
                        selected_articles.append(article)
                
                print(f"Selected {len(selected_articles)} articles for {ticker_symbol}")
                return selected_articles
            else:
                print("Could not parse AI response for article selection")
                # Fallback: return first 7 articles
                return articles[:7]
                
        except Exception as e:
            print(f"Error in article selection: {e}")
            # Fallback: return first 7 articles
            return articles[:7]
    
    def generate_summary(self, selected_articles, ticker_symbol, historical_summaries=None):
        """
        Second AI prompt: Generate comprehensive summary with "What Changed Today" section
        """
        if not selected_articles:
            return None, None
        
        # Prepare selected articles for summarization
        articles_text = ""
        for article in selected_articles:
            articles_text += f"\nTitle: {article['title']}\n"
            articles_text += f"Source: {article['source']}\n"
            articles_text += f"Date: {article.get('published_date', 'N/A')}\n"
            articles_text += f"Content: {article.get('content', article['title'])}\n"
            articles_text += f"URL: {article['url']}\n"
            articles_text += "-" * 80 + "\n"
        
        # Add historical context if available
        historical_context = ""
        if historical_summaries and len(historical_summaries) > 0:
            historical_context = "\n\nHistorical Context (Last 7 Days):\n"
            for summary in historical_summaries[:5]:  # Last 5 days
                date = summary.get('summary_date', 'Unknown')
                what_changed = summary.get('what_changed_today', 'No data')
                historical_context += f"- {date}: {what_changed[:200]}...\n"
        
        prompt = f"""You are a financial analyst creating a daily summary for traders and investors tracking {ticker_symbol}.

Using the selected news articles below, create a comprehensive but concise summary that helps traders understand the current situation and recent developments.

Selected Articles:
{articles_text}
{historical_context}

Please provide:

1. **MAIN SUMMARY** (Maximum 400 words):
   - Synthesize the key information from all selected articles
   - Focus on factual, actionable insights
   - Highlight significant events, announcements, or developments
   - Include relevant financial metrics, if mentioned
   - Maintain an objective, professional tone

2. **WHAT CHANGED TODAY** (Maximum 100 words):
   - Specifically highlight NEW developments compared to previous days
   - Focus on changes, announcements, or shifts in sentiment
   - If this is a continuation of previous news, mention that context
   - Be specific about what's different or noteworthy today

Format your response EXACTLY as:
MAIN SUMMARY:
[Your summary here]

WHAT CHANGED TODAY:
[What's new today]

Keep the total response under {Config.SUMMARY_MAX_WORDS} words. Be concise but informative."""

        try:
            response = self.model.generate_content(prompt)
            summary_text = response.text.strip()
            
            # Parse the response
            main_summary = ""
            what_changed = ""
            
            if "MAIN SUMMARY:" in summary_text and "WHAT CHANGED TODAY:" in summary_text:
                parts = summary_text.split("WHAT CHANGED TODAY:")
                main_summary = parts[0].replace("MAIN SUMMARY:", "").strip()
                what_changed = parts[1].strip()
            else:
                # Fallback parsing
                main_summary = summary_text
                what_changed = "No specific changes identified."
            
            print(f"Generated summary for {ticker_symbol}")
            return main_summary, what_changed
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None, None
    
    def process_ticker_news(self, ticker_symbol, all_articles, historical_summaries=None):
        """
        Complete AI processing pipeline:
        1. Select top articles
        2. Generate summary
        """
        print(f"\n{'='*60}")
        print(f"Processing AI analysis for {ticker_symbol}")
        print(f"Total articles collected: {len(all_articles)}")
        
        if not all_articles:
            print(f"No articles found for {ticker_symbol}")
            return None
        
        # Step 1: Select best articles
        time.sleep(1)  # Rate limiting
        selected_articles = self.select_top_articles(all_articles, ticker_symbol)
        
        if not selected_articles:
            print(f"No articles selected for {ticker_symbol}")
            return None
        
        # Step 2: Generate summary
        time.sleep(1)  # Rate limiting
        main_summary, what_changed = self.generate_summary(
            selected_articles, 
            ticker_symbol,
            historical_summaries
        )
        
        if not main_summary:
            print(f"Failed to generate summary for {ticker_symbol}")
            return None
        
        result = {
            'ticker_symbol': ticker_symbol,
            'selected_articles': selected_articles,
            'main_summary': main_summary,
            'what_changed_today': what_changed,
            'total_articles_analyzed': len(all_articles),
            'articles_selected': len(selected_articles)
        }
        
        print(f"✓ AI processing complete for {ticker_symbol}")
        print(f"  - Articles selected: {len(selected_articles)}")
        print(f"  - Summary length: {len(main_summary.split())} words")
        print(f"{'='*60}\n")
        
        return result