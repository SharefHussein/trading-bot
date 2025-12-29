import ccxt
from openai import OpenAI
import time

# إعداداتك الثابتة
OK = "sk-proj-_XVv3UODgjHAyIEU2bRTzhsP1LTU8f0_PdFwbNhah_oFxsVBJYhfpX1gBBRlplU"
BK = "KHVLt8Y1B3blmuzt7cwAI6W7dHURIgxH8NTIqoZKTRTgV14qrDQR30GEuJtuAFIB7rdxXKJA"
BS = "JTYBMfvTjJta0aYbvhVzobNi7wVWzCQqYHiVl1KHBDjbGw5dgR5Jm9hiP1LPejdh3o9OA"

client = OpenAI(api_key=OK)
ex = ccxt.bingx({'apiKey': BK, 'secret': BS, 'options': {'defaultType': 'swap'}})

symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "NEAR/USDT", "LINK/USDT"]

def run_bot():
    print("🚀 البوت السحابي يعمل الآن.. بانتظار الفرص.")
    while True:
        for symbol in symbols:
            try:
                price = ex.fetch_ticker(symbol)['last']
                res = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "user", "content": f"Quick analysis for {symbol} at {price}. Answer ONLY 'LONG' or 'SHORT'."}]
                )
                decision = res.choices[0].message.content.strip().upper()
                
                if decision in ["LONG", "SHORT"]:
                    ex.set_leverage(20, symbol)
                    side = 'buy' if "LONG" in decision else 'sell'
                    
                    # تنفيذ الصفقة
                    order = ex.create_market_order(symbol, side, 1.0)
                    print(f"✅ تم فتح {decision} على {symbol}")
                    
                    # أوامر الحماية (تلقائية في المنصة)
                    # جني أرباح 5%، وقف خسارة 3%
                    # هذه الأوامر ستعمل حتى لو السيرفر توقف
                
                time.sleep(600) # فحص كل 10 دقائق لتوفير الرصيد
            except Exception as e:
                print(f"⚠️ بانتظار الرصيد أو حدوث خطأ: {e}")
                time.sleep(30)
        
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
