import os
from flask import Flask, render_template, jsonify
import yfinance as yf

app = Flask(
    __name__,
    static_folder='../static',
    template_folder='templates'
)

@app.route('/')
def index():
    return render_template('stockhub.html')

@app.route('/api/analyze/<symbol>')
def analyze_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")
        
        if hist.empty:
            return jsonify({"error": "Symbol not found"}), 404

        info = ticker.info
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        pct_change = ((current_price - prev_close) / prev_close) * 100
        volatility = hist['Close'].pct_change().std() * 100
        
        return jsonify({
            "name": info.get('longName', symbol),
            "price": round(current_price, 2),
            "change": round(pct_change, 2),
            "volatility": round(volatility, 2),
            "dates": hist.index.strftime('%b %d').tolist(),
            "close": hist['Close'].tolist(),
            "volume_data": hist['Volume'].tolist(),
            "description": info.get('longBusinessSummary', 'No description available.')[:200] + '...'
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5007)),
        debug=False
    )