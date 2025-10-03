# 📈 Financial News Aggregator - AI-Powered Stock Market Summaries

A comprehensive, cost-effective solution that automatically aggregates financial news from multiple sources and generates intelligent AI summaries using Google's Gemini Pro. Designed for traders and investors who need quick, actionable insights.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%20Pro-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### Data Collection
- **Multi-Source Aggregation**: Collects news from 3 major sources
  - TradingView news pages
  - Finviz quote pages
  - Polygon API news endpoint
- **Smart Deduplication**: Removes duplicate articles automatically
- **Rate Limiting**: Respects API quotas and implements delays

### AI Processing
- **Intelligent Article Selection**: AI selects top 5-7 most relevant articles
- **Quality Summarization**: Generates <500 word summaries
- **"What Changed Today"**: Highlights new developments with 7-day context
- **Historical Analysis**: Compares current news with past week's data

### User Interface
- **Clean, Professional Design**: Modern, responsive interface
- **Ticker Management**: Easy add/remove functionality
- **Source Transparency**: Shows all URLs and headlines used
- **Historical View**: Access 7 days of summary history
- **Real-time Updates**: Manual refresh for any ticker

### Automation
- **Scheduled Updates**: Daily refresh at 8 AM IST
- **Background Processing**: Non-blocking operations
- **Persistent Storage**: SQLite database for history
- **Error Handling**: Graceful failure recovery

## 💰 Cost Breakdown

**Total Monthly Cost: $0** ✅

| Service | Plan | Cost | Usage |
|---------|------|------|-------|
| Gemini Pro API | Free Tier | $0 | 60 requests/minute |
| Polygon API | Free Tier | $0 | 5 calls/minute |
| Render.com | Free Tier | $0 | 750 hours/month |
| **TOTAL** | | **$0/month** | **$0 *currrently** |

### Cost Optimization Strategies
1. Uses free tier APIs with generous limits
2. Implements aggressive caching
3. Rate limiting prevents quota exhaustion
4. SQLite eliminates database costs
5. Static files served directly (no CDN needed)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Gemini API Key (free from Google AI Studio)
- Polygon API Key (free tier)

### Local Installation

1. **Clone Repository**
```bash
git clone https://github.com/NI3singh/stock-news-summarizer.git
cd stock-news-summarizer
```

2. **Create Virtual Environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment Variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
GEMINI_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
FLASK_SECRET_KEY=your_secret_key
```

5. **Run Application**
```bash
python app.py
```

Visit `http://localhost:5000`

## 📦 Project Structure

```
financial-news-aggregator/
│
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── Procfile                        # Deployment config
├── runtime.txt                     # Python version
├── .env.example                    # Environment template
│
├── scrapers/                       # Web scraping modules
│   ├── __init__.py                # Orchestrator
│   ├── tradingview_scraper.py     # TradingView scraper
│   ├── finviz_scraper.py          # Finviz scraper
│   └── polygon_scraper.py         # Polygon API client
│
├── ai/                            # AI processing
│   ├── __init__.py
│   └── gemini_processor.py        # Gemini AI integration
│
├── database/                      # Database layer
│   ├── __init__.py
│   └── models.py                  # SQLite models & queries
│
├── scheduler/                     # Task scheduling
│   ├── __init__.py
│   └── daily_tasks.py            # Daily refresh jobs
│
├── static/                        # Frontend assets
│   ├── css/
│   └── js/
│       └── main.js               # Frontend JavaScript
│
└── templates/                     # HTML templates
    └── index.html                # Main UI
```

## 🔧 API Endpoints

### Tickers
- `GET /api/tickers` - List all tickers
- `POST /api/tickers` - Add new ticker
  ```json
  {"symbol": "AAPL"}
  ```
- `DELETE /api/tickers/<symbol>` - Remove ticker

### Summaries
- `GET /api/summary/<symbol>` - Get summary and history
- `POST /api/refresh/<symbol>` - Refresh specific ticker
- `POST /api/refresh-all` - Refresh all tickers

### Health
- `GET /health` - Health check endpoint

## 🎯 Usage Guide

### Adding Your First Ticker

1. Enter ticker symbol (e.g., "AAPL") in the input box
2. Click the **+** button
3. Wait 10-30 seconds for initial processing
4. View the generated summary

### Understanding the Summary

**Main Summary**: Comprehensive overview of recent news
- Key developments and announcements
- Financial metrics and performance
- Market sentiment and analyst views

**What Changed Today**: Specific new developments
- Compares to previous 7 days
- Highlights breaking news
- Identifies trend changes

**Source Articles**: All articles used in summary
- Clickable links to original sources
- Multiple sources for verification
- Transparent data sourcing

### Manual Refresh

- **Single Ticker**: Click refresh icon next to ticker
- **All Tickers**: Click "Refresh All" button in header
- Processing takes 10-30 seconds per ticker

## 🚀 Deployment

### Deployed on Render.com (FREE)

## 📊 Performance Metrics

### Typical Processing Times
- Article scraping (3 sources): 5-10 seconds
- AI article selection: 2-3 seconds
- AI summary generation: 3-5 seconds
- **Total per ticker**: 10-18 seconds

### Resource Usage
- Memory: ~100-150 MB
- CPU: Minimal (scraping + API calls)
- Storage: ~1-2 MB per ticker per month
- Bandwidth: ~5-10 MB per ticker daily

## 📈 Future Enhancements

### Planned Features
- [ ] Email notifications for daily summaries
- [ ] Custom refresh schedules per ticker
- [ ] Sentiment analysis scores
- [ ] Price chart integration
- [ ] Export summaries to PDF
- [ ] Multi-user support with authentication

### Contribution Ideas
- Add more data sources (Yahoo Finance, Bloomberg)
- Improve AI prompt engineering
- Add technical indicators
- Implement webhooks for real-time updates

## 📝 License

MIT License - feel free to use for personal or commercial projects

## 🙏 Acknowledgments

- Google Gemini for powerful free AI API
- Polygon.io for comprehensive financial data
- TradingView & Finviz for news aggregation
- Flask community for excellent documentation

## 📧 Contact & Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue]
- Documentation: This README
- API Status: Check individual provider status pages

---

<div align="center">

**Built with ❤️ for traders and investors**

**Star ⭐ this repo if you find it useful!**

</div>