import ccxt
import time
import os
import sys

# التأكد من الطباعة الفورية في سجلات GitHub لسهولة المراقبة
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# جلب مفاتيح الوصول من GitHub Secrets
BK = os.getenv("BINGX_APIKEY")
BS = os.getenv("BINGX_SECRETKEY")

try:
    # إعداد الاتصال ليجبر البوت على استخدام سوق العقود الآجلة (Swap)
    ex = ccxt.bingx({
        'apiKey': BK, 
        'secret': BS, 
        'options': {
            'defaultType': 'swap'  # توجيه العمليات لمحفظة العقود الآجلة حصراً
        }
    })
    log_print("✅ تم الاتصال بـ BingX بنجاح (وضع العقود الآجلة)")
except Exception as e:
    log_print(f"❌ خطأ في الاتصال بـ BingX: {e}")

# قائمة العملات التي سيراقبها البوت
symbols = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "NEAR/USDT"]

def get_signal(symbol):
    try:
        # جلب بيانات الشموع لتحليل السوق برمجياً (بدلاً من OpenAI المكلف)
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='15m', limit=50)
        closes = [x[4] for x in ohlcv]
        last_price = closes[-1]
        avg_price = sum(closes) / len(closes)
        
        # استراتيجية بسيطة: الشراء عند الهبوط والبيع عند الارتفاع عن المتوسط
        if last_price < avg_price * 0.99: return "LONG"
        elif last_price > avg_price * 1.01: return "SHORT"
        return "WAIT"
    except:
        return "WAIT"

def run_bot():
    log_print("🚀 انطلاق البوت في سوق العقود الآجلة (المبلغ: 1.1$)")
    
    while True:
        for symbol in symbols:
            try:
                decision = get_signal(symbol)
                
                if decision in ["LONG", "SHORT"]:
                    log_print(f"📊 إشارة لـ {symbol}: {decision}")
                    
                    # ضبط الرافعة المالية لزيادة القوة الشرائية
                    try:
                        ex.set_leverage(50, symbol) 
                    except:
                        pass
                    
                    ticker = ex.fetch_ticker(symbol)
                    price = ticker['last']
                    
                    # حساب الكمية لتكون القيمة الإجمالية حوالي 1.1 دولار
                    # ملاحظة: إذا رفضت المنصة المبلغ لصغره، ستحتاج لرفعه إلى 2.1
                    amount = 1.1 / price 
                    
                    side = 'buy' if decision == "LONG" else 'sell'
                    
                    # تنفيذ أمر السوق في محفظة العقود الآجلة
                    order = ex.create_market_order(symbol, side, amount)
                    log_print(f"✅ تم تنفيذ صفقة {decision} بنجاح على {symbol}")
                
                time.sleep(30) # فحص العملة التالية بعد 30 ثانية
            except Exception as e:
                log_print(f"⚠️ تنبيه في {symbol}: {e}")
                time.sleep(10)
        
        # انتظار 5 دقائق قبل بدء دورة فحص جديدة للعملات
        time.sleep(300)

if __name__ == "__main__":
    run_bot()

