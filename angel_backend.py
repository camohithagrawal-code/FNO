# Angel SmartAPI Backend Proxy
# This simple backend handles CORS and authentication for the F&O Scanner app

from flask import Flask, request, jsonify
from flask_cors import CORS
from SmartApi import SmartConnect
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for browser access

# Store active sessions (in production, use Redis or database)
sessions = {}

@app.route('/api/login', methods=['POST'])
def login():
    """Login to Angel SmartAPI"""
    try:
        data = request.json
        api_key = data.get('apiKey')
        client_id = data.get('clientId')
        password = data.get('password')
        totp = data.get('totp')
        
        # Initialize SmartConnect
        smart_api = SmartConnect(api_key=api_key)
        
        # Generate session
        session_data = smart_api.generateSession(client_id, password, totp)
        
        if session_data['status']:
            # Store session
            auth_token = session_data['data']['jwtToken']
            sessions[client_id] = {
                'smart_api': smart_api,
                'auth_token': auth_token,
                'feed_token': session_data['data']['feedToken']
            }
            
            return jsonify({
                'success': True,
                'authToken': auth_token,
                'feedToken': session_data['data']['feedToken']
            })
        else:
            return jsonify({'success': False, 'error': 'Login failed'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """Get real-time quotes for multiple symbols"""
    try:
        client_id = request.args.get('clientId')
        symbols = request.args.get('symbols', '').split(',')
        
        if client_id not in sessions:
            return jsonify({'error': 'Not authenticated'}), 401
        
        smart_api = sessions[client_id]['smart_api']
        
        # Fetch quotes for all symbols
        quotes_data = []
        for symbol in symbols:
            try:
                # Get LTP (Last Traded Price)
                ltp_data = smart_api.ltpData('NSE', symbol, get_token(symbol))
                
                # Get quote with more details
                quote = smart_api.getMarketData('FULL', [{'exchange': 'NSE', 'symboltoken': get_token(symbol)}])
                
                quotes_data.append({
                    'symbol': symbol,
                    'ltp': ltp_data['data']['ltp'],
                    'change': ltp_data['data']['change'],
                    'pChange': ltp_data['data']['pChange'],
                    'open': quote['data']['fetched'][0]['open'],
                    'high': quote['data']['fetched'][0]['high'],
                    'low': quote['data']['fetched'][0]['low'],
                    'close': quote['data']['fetched'][0]['close']
                })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'data': quotes_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/option-chain', methods=['GET'])
def get_option_chain():
    """Get option chain data for a symbol"""
    try:
        client_id = request.args.get('clientId')
        symbol = request.args.get('symbol')
        
        if client_id not in sessions:
            return jsonify({'error': 'Not authenticated'}), 401
        
        smart_api = sessions[client_id]['smart_api']
        
        # Note: Angel API doesn't provide direct option chain
        # You'd need to construct it from individual option symbols
        # This is a simplified version
        
        return jsonify({
            'success': True,
            'message': 'Option chain endpoint - to be implemented'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_token(symbol):
    """Get symbol token for Angel API (you need a token mapping file)"""
    # In production, load from a JSON file or database
    # For now, return a placeholder
    token_map = {
        'RELIANCE': '2885',
        'TCS': '11536',
        'HDFCBANK': '1333',
        'INFY': '1594',
        # Add more mappings...
    }
    return token_map.get(symbol, '0')

if __name__ == '__main__':
    # For development
    app.run(debug=True, host='0.0.0.0', port=5000)
    
# DEPLOYMENT INSTRUCTIONS:
# 
# 1. Install dependencies:
#    pip install flask flask-cors SmartApi-Python
#
# 2. Deploy to Render.com (FREE):
#    - Create account on render.com
#    - New Web Service
#    - Connect this code
#    - Deploy
#    - Get URL: https://your-app.onrender.com
#
# 3. Update your HTML app:
#    - Set PROXY_ENDPOINT to your Render URL
#    - Enable USE_PROXY = true
#
# 4. That's it! Real-time Angel data working!
