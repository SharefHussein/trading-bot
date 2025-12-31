import ccxt
import time
import os
import sys
from datetime import datetime

# ============ إعدادات البيع والشراء (الرافعة 20) ============
class Config:
    LEVERAGE = 20                     
    MAX_OPEN_POSITIONS = 1            
    TAKE_PROFIT_PERCENT = 1.5        
    MAX_LOSS_USD = 0.05              # أقصى خسارة 5 سنتات
    RSI_BUY_THRESHOLD = 30           # شراء (Long) عند التشبع البيعي
    RSI_SELL_THRESHOLD = 70          # بيع (Short) عند التشبع الشرائي
    CHECK_INTERVAL = 5               

def log_print(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def run_bot():
    BK = os.getenv("BINGX_APIKEY")
    BS = os.getenv("BINGX_SECRETKEY")
    try:
        ex = ccxt.bingx({'apiKey': BK, 'secret': BS, 'options': {'defaultType': 'swap'}})
        log_print(f"🔄 نظام البيع والشراء نشط.. الرافعة: 20 | حماية: 0.05$")
    except Exception as e:
        log_print(f"❌ خطأ: {e}")
        return

    while True:
        try:
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            positions = ex.fetch_positions()
            open_pos = [p for p in positions if float(p['info'].get('positionAmt', 0)) != 0]

            if len(open_pos) >= Config.MAX_OPEN_POSITIONS:
                time.sleep(30)
                continue

            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT')]
            
            for symbol in symbols[:50]: 
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                    closes = [x[4] for x in ohlcv]
                    rsi = calculate_rsi(closes)
                    
                    # مراقبة القيم القريبة من الدخول
                    if rsi < 35 or rsi > 65:
                        log_print(f"🔍 {symbol} | RSI: {rsi:.2f}")

                    price = tickers[symbol]['last']
                    margin_to_use = 3.8
                    amount = (margin_to_use * Config.LEVERAGE) / price
                    
                    # حالة 1: الشراء (Long) - السعر في القاع
                    if rsi < Config.RSI_BUY_THRESHOLD:
                        sl = price - (Config.MAX_LOSS_USD / amount)
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        
                        log_print(f"🚀 دخول شراء (Long) في {symbol} | RSI: {rsi:.2f}")
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        log_print(f"✅ تم تنفيذ الشراء.")
                        break

                    # حالة 2: البيع المكشوف (Short) - السعر في القمة
                    elif rsi > Config.RSI_SELL_THRESHOLD:
                        sl = price + (Config.MAX_LOSS_USD / amount)
                        tp = price * (1 - Config.TAKE_PROFIT_PERCENT / 100)
                        
                        log_print(f"🔻 دخول بيع (Short) في {symbol} | RSI: {rsi:.2f}")
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'sell', amount)
                        ex.create_order(symbol, 'limit', 'buy', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'buy', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        log_print(f"✅ تم تنفيذ البيع.")
                        break 

                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)
        except: time.sleep(10)

if __name__ == "__main__":
    run_bot()

