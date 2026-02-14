from flask import Flask, request, jsonify
from flask_cors import CORS
from SmartApi import SmartConnect
import pyotp
import os

app = Flask(__name__)
CORS(app)

# Get credentials from environment variables (secure)
ANGEL_API_KEY = os.getenv('ANGEL_API_KEY')
ANGEL_CLIENT_ID = os.getenv('ANGEL_CLIENT_ID')
ANGEL_PASSWORD = os.getenv('ANGEL_PASSWORD')
ANGEL_TOTP_SECRET = os.getenv('ANGEL_TOTP_SECRET')

# Initialize SmartConnect
smart_api = None
auth_token = None

def get_totp():
    """Generate TOTP for login"""
    totp = pyotp.TOTP(ANGEL_TOTP_SECRET)
    return totp.now()

def login():
    """Login to Angel SmartAPI"""
    global smart_api, auth_token
    try:
        smart_api = SmartConnect(api_key=ANGEL_API_KEY)
        totp = get_totp()
        data = smart_api.generateSession(ANGEL_CLIENT_ID, ANGEL_PASSWORD, totp)
        
        if data['status']:
            auth_token = data['data']['jwtToken']
            return True
        return False
    except Exception as e:
        print(f"Login error: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'Angel SmartAPI Proxy'})

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    """Get quotes for multiple symbols"""
    global smart_api, auth_token
    
    # Login if not authenticated
    if not auth_token:
        if not login():
            return jsonify({'error': 'Authentication failed'}), 401
    
    try:
        symbols = request.args.get('symbols', '').split(',')
        quotes_data = []
        
        for symbol in symbols:
            try:
                # Get quote (simplified - you'd need symbol tokens)
                # For demo, return mock data structure
                quotes_data.append({
                    'symbol': symbol,
                    'ltp': 0,
                    'change': 0,
                    'pChange': 0
                })
            except:
                continue
        
        return jsonify({'success': True, 'data': quotes_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
