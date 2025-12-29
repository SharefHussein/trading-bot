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
    # إعداد صارم للتعامل مع العقود الآجلة فقط
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {'defaultType': 'swap'} 
    })
    log_print("✅ متصل بـ BingX - وضع العقود الآجلة")
except Exception as e:
    log_print(f"❌ خطأ اتصال: {e}")

symbols = ["RIVER/USDT", "PIPPIN/USDT", "SQD/USDT", "BEAT/USDT"]

def get_signal(symbol):
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='15m', limit=50)
        closes = [x[4] for x in ohlcv]
        last_price = closes[-1]
        avg_price = sum(closes) / len(closes)
        if last_price < avg_price * 0.995: return "LONG"
        elif last_price > avg_price * 1.005: return "SHORT"
        return "WAIT"
    except: return "WAIT"

def run_bot():
    log_print("🚀 تشغيل البوت بمبلغ 1$ من محفظة العقود...")
    
    while True:
        for symbol in symbols:
            try:
                decision = get_signal(symbol)
                if decision in ["LONG", "SHORT"]:
                    # التأكد من ضبط الرافعة
                    try: ex.set_leverage(25, symbol)
                    except: pass
                    
                    ticker = ex.fetch_ticker(symbol)
                    price = ticker['last']
                    
                    # تنفيذ الصفقة بمبلغ 1 دولار (سيستخدم رصيد العقود الآجلة)
                    amount = 1.0 / price 
                    side = 'buy' if decision == "LONG" else 'sell'
                    
                    # تحديد params لضمان استخدام محفظة العقود
                    order = ex.create_market_order(symbol, side, amount)
                    log_print(f"✅ نجاح! فتح صفقة {decision} على {symbol}")
                
                time.sleep(20)
            except Exception as e:
                # إذا ظهر خطأ الرصيد، سيطبع لنا التفاصيل بدقة
                log_print(f"⚠️ {symbol}: {e}")
                time.sleep(10)
        time.sleep(300)

if __name__ == "__main__":
    run_bot()

