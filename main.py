import ccxt
import time
import os
import sys

# التأكد من الطباعة الفورية في سجلات GitHub
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# سحب مفاتيح BingX
BK = os.getenv("BINGX_APIKEY")
BS = os.getenv("BINGX_SECRETKEY")

try:
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {'defaultType': 'swap'}
    })
    log_print("✅ تم الاتصال بـ BingX بنجاح (الوضع المجاني)")
except Exception as e:
    log_print(f"❌ خطأ في الاتصال: {e}")

symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "NEAR/USDT"]

def get_signal(symbol):
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='15m', limit=50)
        closes = [x[4] for x in ohlcv]
        last_price = closes[-1]
        avg_price = sum(closes) / len(closes)
        
        if last_price < avg_price * 0.99: return "LONG"
        elif last_price > avg_price * 1.01: return "SHORT"
        return "WAIT"
    except:
        return "WAIT"

def run_bot():
    log_print("🚀 انطلاق البوت... جاري فحص الفرص")
    
    while True:
        for symbol in symbols:
            try:
                decision = get_signal(symbol)
                
                if decision in ["LONG", "SHORT"]:
                    log_print(f"📊 إشارة لـ {symbol}: {decision}")
                    
                    # --- التعديل هنا لحل مشكلة setLeverage ---
                    try:
                        ex.set_leverage(20, symbol, {'side': 'BOTH'}) 
                    except:
                        pass # إذا كانت مضبوطة مسبقاً سيتخطى الخطأ
                    
                    ticker = ex.fetch_ticker(symbol)
                    price = ticker['last']
                    amount = 2.0 / price # حجم صفقة بـ 2 دولار
                    
                    side = 'buy' if decision == "LONG" else 'sell'
                    order = ex.create_market_order(symbol, side, amount)
                    log_print(f"✅ تم تنفيذ صفقة {decision} على {symbol}")
                
                time.sleep(30) # فحص سريع كل 30 ثانية
            except Exception as e:
                log_print(f"⚠️ تنبيه في {symbol}: {e}")
                time.sleep(10)
        time.sleep(300)

if __name__ == "__main__":
    run_bot()

