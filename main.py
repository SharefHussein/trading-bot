import ccxt
import time
import os
import sys
from datetime import datetime

# ============ إعدادات القناص العدواني (تداول سريع جداً) ============
class Config:
    LEVERAGE = 50                     
    MAX_OPEN_POSITIONS = 2            # يسمح بفتح صفقتين لزيادة الفرص
    STOP_LOSS_PERCENT = 0.8          # وقف خسارة مرن
    TAKE_PROFIT_PERCENT = 1.2        # هدف ربح سريع (60% مع الرافعة)
    RSI_BUY_THRESHOLD = 52           # حد دخول مرتفع (فرص كثيرة)
    MIN_VOLUME_USDT = 500000         # مراقبة عملات أكثر سيولة
    CHECK_INTERVAL = 10              # فحص فائق السرعة

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
        log_print("🔥 تم تشغيل القناص العدواني - وضع التداول التلقائي المكثف")
    except Exception as e:
        log_print(f"❌ خطأ اتصال: {e}")
        return

    while True:
        try:
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            
            positions = ex.fetch_positions()
            open_pos_count = len([p for p in positions if float(p['info'].get('positionAmt', 0)) != 0])

            # التحقق من عدد الصفقات المفتوحة
            if open_pos_count >= Config.MAX_OPEN_POSITIONS:
                log_print(f"📦 لدي {open_pos_count} صفقات مفتوحة.. أنتظر إغلاقها")
                time.sleep(20)
                continue

            if avail < 1.0:
                log_print(f"💰 الرصيد المتاح {avail:.2f}$ قليل لفتح صفقة جديدة")
                time.sleep(30)
                continue

            # مسح أفضل 100 عملة نشطة
            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT') and t.get('quoteVolume', 0) > Config.MIN_VOLUME_USDT]
            symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:100]

            for symbol in symbols:
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    closes = [x[4] for x in ohlcv]
                    rsi = calculate_rsi(closes)
                    
                    # شرط الدخول العدواني: RSI تحت الـ 52 (يعني أغلب السوق متاح)
                    if rsi < Config.RSI_BUY_THRESHOLD:
                        price = tickers[symbol]['last']
                        # استخدام 40% من الرصيد المتاح لكل صفقة لتجنب التعليق
                        amount = (avail * 40) / price 
                        
                        log_print(f"⚡ اقتناص سريع: {symbol} | RSI: {rsi:.1f}")
                        
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        sl = price * (1 - Config.STOP_LOSS_PERCENT / 100)
                        
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        
                        log_print(f"✅ تم دخول الصفقة تلقائياً بسعر {price}")
                        break # الخروج من حلقة العملات للانتظار قليلاً
                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            log_print(f"⚠️ تنبيه: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()

