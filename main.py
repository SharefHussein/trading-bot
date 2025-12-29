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
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {
            'defaultType': 'swap',
            'accountsByType': {'swap': 'future'}
        }
    })
    log_print("✅ متصل - تم استبعاد (BTC, ETH, SOL) من القائمة")
except Exception as e:
    log_print(f"❌ خطأ اتصال: {e}")

# قائمة العملات المختارة (بدون العملات المستبعدة)
symbols = [
    "AVAX/USDT", "DOGE/USDT", "NEAR/USDT", "MATIC/USDT", 
    "ADA/USDT", "XRP/USDT", "LINK/USDT", "DOT/USDT"
]

def run_bot():
    log_print(f"🚀 البوت يراقب الآن {len(symbols)} عملة مختارة")
    while True:
        for symbol in symbols:
            try:
                # التحقق من الرصيد المتاح في محفظة العقود
                balance = ex.fetch_balance()
                avail = balance['free'].get('USDT', 0)
                
                # طباعة الرصيد فقط عند توفر فرصة دخول
                if avail > 1.2:
                    ticker = ex.fetch_ticker(symbol)
                    price = ticker['last']
                    
                    # استراتيجية دخول: شراء إذا كان السعر الحالي أقل من متوسط الشموع الأخيرة
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='5m', limit=5)
                    avg_p = sum([x[4] for x in ohlcv]) / 5
                    
                    if price < avg_p:
                        amount = 1.2 / price
                        
                        # تنفيذ صفقة الشراء
                        order = ex.create_market_order(symbol, 'buy', amount)
                        log_print(f"✅ تم فتح صفقة على {symbol} بسعر {price}")
                        
                        # حساب مستويات الإغلاق (10% ربح / 2% خسارة)
                        # ملاحظة: الرافعة 20x تجعل هذه الأهداف سريعة جداً
                        tp_price = price * 1.005 # ربح 0.5% في السعر = 10% مع الرافعة
                        sl_price = price * 0.999 # خسارة 0.1% في السعر = 2% مع الرافعة
                        
                        # إرسال أوامر الإغلاق التلقائي
                        ex.create_order(symbol, 'limit', 'sell', amount, tp_price, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {
                            'stopPrice': sl_price,
                            'reduceOnly': True
                        })
                        
                        log_print(f"🎯 الأهداف ضبطت تلقائياً لعملة {symbol}")
                
                time.sleep(20) # فحص العملة التالية
            except Exception as e:
                time.sleep(10)
        time.sleep(120) # انتظار دقيقتين قبل إعادة فحص القائمة بالكامل

if __name__ == "__main__":
    run_bot()

