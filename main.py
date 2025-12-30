import ccxt
import time
import os
import sys

def log_print(msg):
    print(msg)
    sys.stdout.flush()

BK = os.getenv("BINGX_APIKEY")
BS = os.getenv("BINGX_SECRETKEY")

try:
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {'defaultType': 'swap', 'accountsByType': {'swap': 'future'}}
    })
    log_print("⚡ وضع القناص الجريء: فحص أفضل 100 عملة")
except Exception as e:
    log_print(f"❌ خطأ اتصال: {e}")

def get_active_symbols():
    try:
        markets = ex.fetch_tickers()
        sorted_symbols = sorted(markets.items(), key=lambda x: x[1]['quoteVolume'] if x[1]['quoteVolume'] else 0, reverse=True)
        return [symbol for symbol, data in sorted_symbols[:100] if '/USDT' in symbol]
    except:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT"]

def get_rsi(symbol, timeframe, period=14):
    try:
        bars = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=period + 5)
        closes = [x[4] for x in bars]
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except: return 50

def run_bot():
    symbols = get_active_symbols()
    log_print(f"📡 بدأ مراقبة {len(symbols)} عملة برصيد {1.3}$...")
    
    while True:
        try:
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            positions = ex.fetch_positions()
            has_position = any(float(p['info'].get('positionAmt', 0)) != 0 for p in positions)
        except: continue

        if not has_position and avail >= 1.2:
            for symbol in symbols:
                try:
                    rsi_1m = get_rsi(symbol, '1m')
                    rsi_5m = get_rsi(symbol, '5m')
                    
                    if rsi_1m < 42 and rsi_5m < 48:
                        ticker = ex.fetch_ticker(symbol)
                        price = ticker['last']
                        
                        # استخدام رافعة عالية لتناسب الرصيد الصغير
                        amount = (avail * 45) / price 
                        
                        ex.create_market_order(symbol, 'buy', amount)
                        log_print(f"🚀 هجوم على {symbol} | RSI(1m): {rsi_1m:.1f}")
                        
                        tp = price * 1.006 
                        sl = price * 0.995 
                        
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        break 
                    time.sleep(0.2)
                except: continue
        time.sleep(10)

if __name__ == "__main__":
    run_bot()
 

