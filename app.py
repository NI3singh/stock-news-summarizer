from flask import Flask, render_template, request, jsonify
from config import Config
from database.models import DatabaseManager
from scheduler.daily_tasks import DailyTaskScheduler
import threading

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
db = DatabaseManager()
scheduler = DailyTaskScheduler()

# Start scheduler in background
def start_scheduler():
    scheduler.start()

scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    """Get all active tickers"""
    try:
        tickers = db.get_all_tickers()
        return jsonify({'success': True, 'tickers': tickers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tickers', methods=['POST'])
def add_ticker():
    """Add a new ticker"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').strip().upper()
        
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol is required'}), 400
        
        if len(symbol) > 10:
            return jsonify({'success': False, 'error': 'Invalid symbol'}), 400
        
        success = db.add_ticker(symbol)
        
        if success:
            # Trigger immediate processing for new ticker
            threading.Thread(
                target=scheduler.process_single_ticker, 
                args=(symbol,),
                daemon=True
            ).start()
            
            return jsonify({
                'success': True, 
                'message': f'{symbol} added successfully. Processing...'
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'{symbol} already exists'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tickers/<symbol>', methods=['DELETE'])
def remove_ticker(symbol):
    """Remove a ticker"""
    try:
        db.remove_ticker(symbol)
        return jsonify({'success': True, 'message': f'{symbol} removed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/summary/<symbol>', methods=['GET'])
def get_summary(symbol):
    """Get latest summary and articles for a ticker"""
    try:
        # Get latest summary
        summary = db.get_latest_summary(symbol)
        
        # Get historical summaries
        historical = db.get_summaries_for_ticker(symbol, days=7)
        
        # Get articles used in latest summary
        articles = []
        if summary and summary.get('articles_used'):
            articles = summary['articles_used']
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'latest_summary': summary,
            'historical_summaries': historical,
            'articles': articles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/refresh/<symbol>', methods=['POST'])
def refresh_ticker(symbol):
    """Manually refresh a specific ticker"""
    try:
        # Check if ticker exists
        tickers = db.get_all_tickers()
        if symbol.upper() not in tickers:
            return jsonify({
                'success': False, 
                'error': f'{symbol} not found'
            }), 404
        
        # Trigger refresh in background
        threading.Thread(
            target=scheduler.process_single_ticker,
            args=(symbol.upper(),),
            daemon=True
        ).start()
        
        return jsonify({
            'success': True,
            'message': f'Refresh started for {symbol}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/refresh-all', methods=['POST'])
def refresh_all():
    """Manually trigger refresh for all tickers"""
    try:
        threading.Thread(
            target=scheduler.daily_refresh_task,
            daemon=True
        ).start()
        
        return jsonify({
            'success': True,
            'message': 'Refresh started for all tickers'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'scheduler_running': scheduler.scheduler.running
    })

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)