import ccxt
import time
import os
import sys

# التأكد من الطباعة الفورية في سجلات GitHub
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# سحب مفاتيح BingX فقط (لا نحتاج OpenAI الآن)
BK = os.getenv("BINGX_APIKEY")
BS = os.getenv("BINGX_SECRETKEY")

try:
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {'defaultType': 'swap'}
    })
    log_print("✅ تم الاتصال بـ BingX بنجاح (الوضع المجاني المؤتمت)")
except Exception as e:
    log_print(f"❌ خطأ في الاتصال بـ BingX: {e}")

symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "NEAR/USDT"]

def get_signal(symbol):
    try:
        # جلب الشموع (إطار 15 دقيقة) لتحليل الاتجاه
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='15m', limit=50)
        closes = [x[4] for x in ohlcv]
        
        # حساب مؤشر بسيط (RSI البدائي)
        last_price = closes[-1]
        prev_price = closes[-2]
        
        # استراتيجية بسيطة: إذا انخفض السعر كثيراً نشتري، وإذا ارتفع كثيراً نبيع
        if last_price < sum(closes)/len(closes) * 0.98: 
            return "LONG"
        elif last_price > sum(closes)/len(closes) * 1.02:
            return "SHORT"
        return "WAIT"
    except:
        return "WAIT"

def run_bot():
    log_print("🚀 انطلاق البوت المجاني 24/7 (بدون تكاليف OpenAI)")
    
    while True:
        for symbol in symbols:
            try:
                ticker = ex.fetch_ticker(symbol)
                price = ticker['last']
                
                # الحصول على إشارة فنية بدلاً من ذكاء اصطناعي
                decision = get_signal(symbol)
                
                if decision in ["LONG", "SHORT"]:
                    log_print(f"📊 إشارة فنية لـ {symbol}: {decision}")
                    ex.set_leverage(20, symbol)
                    
                    # حجم الصفقة (حوالي 2 دولار)
                    amount = 2.0 / price 
                    side = 'buy' if decision == "LONG" else 'sell'
                    
                    order = ex.create_market_order(symbol, side, amount)
                    log_print(f"✅ تم تنفيذ صفقة {decision} بنجاح على {symbol}")
                
                time.sleep(60) 
            except Exception as e:
                log_print(f"⚠️ تنبيه في {symbol}: {e}")
                time.sleep(10)
        time.sleep(300)

if __name__ == "__main__":
    run_bot()

