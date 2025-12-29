import ccxt
from openai import OpenAI
import time
import os
import sys

# التأكد من الطباعة الفورية في السجلات
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# سحب المفاتيح
OPENAI_KEY = os.getenv("OPENAI")
BINGX_API = os.getenv("BINGX_APIKEY")
BINGX_SECRET = os.getenv("BINGX_SECRETKEY")

try:
    client = OpenAI(api_key=OPENAI_KEY)
    ex = ccxt.bingx({'apiKey': BINGX_API, 'secret': BINGX_SECRET, 'options': {'defaultType': 'swap'}})
    log_print("✅ تم الاتصال بـ BingX و OpenAI بنجاح")
except Exception as e:
    log_print(f"❌ خطأ في الإعدادات: {e}")

symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT"]

def run_bot():
    log_print("🚀 انطلاق الوكيل الذكي... جاري فحص السوق")
    
    while True:
        for symbol in symbols:
            try:
                ticker = ex.fetch_ticker(symbol)
                price = ticker['last']
                
                res = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "user", "content": f"Quick analysis for {symbol} at {price}. Answer ONLY 'LONG' or 'SHORT'."}]
                )
                decision = res.choices[0].message.content.strip().upper()
                
                if decision in ["LONG", "SHORT"]:
                    log_print(f"📊 قرار الذكاء الاصطناعي لـ {symbol}: {decision}")
                    ex.set_leverage(20, symbol)
                    
                    # فتح صفقة بقيمة 2 دولار تقريباً (آمن للرصيد الصغير)
                    amount = 2.0 / price 
                    side = 'buy' if "LONG" in decision else 'sell'
                    
                    order = ex.create_market_order(symbol, side, amount)
                    log_print(f"✅ تم تنفيذ صفقة {decision} بنجاح!")
                
                time.sleep(60) # فحص كل دقيقة
            except Exception as e:
                log_print(f"⚠️ تنبيه في {symbol}: {e}")
                time.sleep(10)

if __name__ == "__main__":
    run_bot()

