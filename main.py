import ccxt
import time
import os
import sys
from datetime import datetime

# ============ إعدادات التنفيذ الفوري (بدون انتظار) ============
class Config:
    LEVERAGE = 50                     
    MAX_OPEN_POSITIONS = 3            
    STOP_LOSS_PERCENT = 2.0          
    TAKE_PROFIT_PERCENT = 3.0        
    RSI_BUY_THRESHOLD = 80           # رفعنا الحد لـ 80 لضمان الشراء فوراً
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
        log_print("🚀 بدء وضع الاختبار الفوري.. سأفتح صفقة خلال دقائق")
    except Exception as e:
        log_print(f"❌ خطأ اتصال: {e}")
        return

    while True:
        try:
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            positions = ex.fetch_positions()
            open_pos_count = len([p for p in positions if float(p['info'].get('positionAmt', 0)) != 0])

            if open_pos_count >= Config.MAX_OPEN_POSITIONS:
                time.sleep(10)
                continue

            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT')]
            
            for symbol in symbols[:20]: # فحص أسرع لأول 20 عملة
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=15)
                    closes = [x[4] for x in ohlcv]
                    rsi = calculate_rsi(closes)
                    
                    if rsi < Config.RSI_BUY_THRESHOLD:
                        price = tickers[symbol]['last']
                        # قيمة العقد 2.3$ لتجاوز شرط الـ 2.01$ بمان أمان
                        target_value = 2.3 
                        amount = target_value / price 
                        
                        log_print(f"⚡ محاولة دخول فوري في {symbol} | RSI: {rsi:.1f}")
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        sl = price * (1 - Config.STOP_LOSS_PERCENT / 100)
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        
                        log_print(f"✅ تم تنفيذ الصفقة بنجاح!")
                        break
                except: continue
            time.sleep(Config.CHECK_INTERVAL)
        except: time.sleep(10)

if __name__ == "__main__":
    run_bot()

