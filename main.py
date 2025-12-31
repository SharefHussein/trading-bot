import ccxt
import time
import os
import sys
from datetime import datetime

# ============ إعدادات الرافعة المالية 20 والحماية الصارمة ============
class Config:
    LEVERAGE = 20                     # تم الضبط على 20 حسب طلبك
    MAX_OPEN_POSITIONS = 1            # صفقة واحدة فقط في كل مرة
    TAKE_PROFIT_PERCENT = 1.5        
    MAX_LOSS_USD = 0.05              # أقصى خسارة 5 سنتات فقط
    RSI_BUY_THRESHOLD = 60           
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
        log_print(f"🛡️ نظام الرافعة 20 يعمل.. حماية الخسارة: {Config.MAX_LOSS_USD}$")
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
                    
                    if rsi < Config.RSI_BUY_THRESHOLD:
                        price = tickers[symbol]['last']
                        margin_to_use = 1.0 
                        amount = (margin_to_use * Config.LEVERAGE) / price 
                        
                        # حساب سعر وقف الخسارة (SL) وسعر جني الربح (TP)
                        sl_price = price - (Config.MAX_LOSS_USD / amount)
                        tp_price = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        
                        log_print(f"🎯 دخول {symbol} | رافعة: 20 | الوقف عند خسارة {Config.MAX_LOSS_USD}$")
                        
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        
                        # وضع الأوامر الحمائية
                        ex.create_order(symbol, 'limit', 'sell', amount, tp_price, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl_price, 'reduceOnly': True})
                        
                        log_print(f"✅ تم التنفيذ. في انتظار النتائج..")
                        break 
                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)
        except: time.sleep(10)

if __name__ == "__main__":
    run_bot()

