import ccxt
from openai import OpenAI
import time
import os

# سحب المفاتيح من GitHub Secrets بناءً على الأسماء في صورتك
OK = os.getenv("OPENAI")
BK = os.getenv("BINGX_APIKEY")
BS = os.getenv("BINGX_SECRETKEY")

client = OpenAI(api_key=OK)
ex = ccxt.bingx({'apiKey': BK, 'secret': BS, 'options': {'defaultType': 'swap'}})

symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "NEAR/USDT", "LINK/USDT"]

def run_bot():
    print("🚀 انطلاق الوكيل الذكي (نسخة Secrets الآمنة)...")
    
    if not OK or not BK or not BS:
        print("❌ خطأ: لم يتم العثور على المفاتيح. تأكد من مطابقة الأسماء في Secrets.")
        return

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
                    ex.set_leverage(20, symbol)
                    side = 'buy' if "LONG" in decision else 'sell'
                    ex.create_market_order(symbol, side, 0.5)
                    print(f"✅ تم فتح صفقة {decision} على {symbol} بسعر {price}")
                
                time.sleep(300) 
            except Exception as e:
                print(f"⚠️ تنبيه: {e}")
                time.sleep(30)
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
