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
    # تعديل الإعدادات للوصول للمحفظة التي تظهر عندك (بهامش USD)
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {
            'defaultType': 'swap',
            'accountsByType': {'swap': 'future'} # محاولة الوصول للحساب الموحد
        }
    })
    log_print("✅ تم الربط بالمحفظة المتاحة (بهامش USD)")
except Exception as e:
    log_print(f"❌ خطأ: {e}")

symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT"]

def run_bot():
    log_print("🚀 فحص الرصيد والبدء...")
    
    while True:
        for symbol in symbols:
            try:
                # محاولة جلب الرصيد من المحفظة التي بها 2.15$
                balance = ex.fetch_balance()
                # طباعة الرصيد المتاح لنتأكد مما يراه البوت فعلياً
                log_print(f"💰 الرصيد المتاح حالياً: {balance['free'].get('USDT', 0)}")
                
                ticker = ex.fetch_ticker(symbol)
                price = ticker['last']
                
                # تنفيذ الصفقة بمبلغ 1.2$ لضمان تجاوز الحد الأدنى
                amount = 1.2 / price 
                
                # استراتيجية سريعة (شراء عند الانخفاض)
                ohlcv = ex.fetch_ohlcv(symbol, timeframe='5m', limit=2)
                if ohlcv[-1][4] < ohlcv[-2][4]:
                    order = ex.create_market_order(symbol, 'buy', amount)
                    log_print(f"✅ تمت العملية بنجاح على {symbol}")
                
                time.sleep(30)
            except Exception as e:
                log_print(f"⚠️ تنبيه: {e}")
                time.sleep(10)
        time.sleep(300)

if __name__ == "__main__":
    run_bot()

