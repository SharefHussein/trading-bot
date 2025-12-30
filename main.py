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
        'options': {'defaultType': 'swap', 'accountsByType': {'swap': 'future'}}
    })
    log_print("⚡ تم تفعيل وضع القوة القصوى (RSI المزدوج + فحص فائق السرعة)")
except Exception as e:
    log_print(f"❌ خطأ في الاتصال بالمنصة: {e}")

# القائمة المختارة لأكثر العملات حركة (Volatility) لضمان فرص سريعة
symbols = [
    "AVAX/USDT", "DOGE/USDT", "NEAR/USDT", "MATIC/USDT", "ADA/USDT", "XRP/USDT", 
    "LINK/USDT", "DOT/USDT", "SHIB/USDT", "LTC/USDT", "OP/USDT", "ARB/USDT", 
    "SUI/USDT", "PEPE/USDT", "FLOKI/USDT", "BONK/USDT", "WIF/USDT", "JUP/USDT",
    "TIA/USDT", "SEI/USDT", "FET/USDT", "RNDR/USDT", "INJ/USDT", "STX/USDT"
]

def get_rsi(symbol, timeframe, period=14):
    try:
        bars = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=period + 5)
        closes = [x[4] for x in bars]
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except: return 50

def run_bot():
    log_print(f"📡 الرادار يمسح الآن {len(symbols)} عملة بأقصى طاقة...")
    while True:
        try:
            # التحقق من الحالة العامة للمحفظة قبل كل دورة
            positions = ex.fetch_positions()
            open_positions = [p for p in positions if float(p['info'].get('positionAmt', 0)) != 0]
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
        except Exception as e:
            log_print(f"⚠️ تنبيه: تعذر جلب البيانات (سيتم المحاولة ثانية): {e}")
            time.sleep(10)
            continue

        # الالتزام بشرط "صفقتين بحد أقصى" للأمان
        if len(open_positions) < 2:
            for symbol in symbols:
                try:
                    # فحص مزدوج: RSI لدقيقة واحدة ولـ 5 دقائق
                    rsi_1m = get_rsi(symbol, '1m')
                    rsi_5m = get_rsi(symbol, '5m')
                    
                    # طباعة النشاط اللحظي (تفاعلية كاملة)
                    log_print(f"🔍 فحص {symbol} -> RSI(1m): {rsi_1m:.1f} | RSI(5m): {rsi_5m:.1f}")

                    # شرط الدخول الاحترافي (منطقة التشبع البيعي الحقيقي)
                    if rsi_1m < 32 and rsi_5m < 38:
                        if avail > 0.1:
                            ticker = ex.fetch_ticker(symbol)
                            price = ticker['last']
                            amount = 2.1 / price # قيمة الصفقة المضمونة لقبول المنصة
                            
                            # أمر الشراء السوقي
                            ex.create_market_order(symbol, 'buy', amount)
                            log_print(f"🚀 صيد ثمين! تم شراء {symbol} بسعر {price}")
                            
                            # حساب وضبط الأهداف التلقائية (10% ربح / 2% خسارة)
                            tp_price = price * 1.005 
                            sl_price = price * 0.999 
                            
                            # إرسال أوامر الإغلاق للمنصة
                            ex.create_order(symbol, 'limit', 'sell', amount, tp_price, {'reduceOnly': True})
                            ex.create_order(symbol, 'stop', 'sell', amount, None, {
                                'stopPrice': sl_price, 'reduceOnly': True
                            })
                            log_print(f"🎯 تم تفعيل درع الحماية والهدف لـ {symbol}")
                            # الخروج من قائمة العملات لضمان عدم فتح أكثر من المطلوب في لحظة واحدة
                            break 
                    
                    time.sleep(0.5) # سرعة فحص فائقة جداً (نصف ثانية بين كل عملة)
                except: continue
        
        # إذا كانت الصفقات مكتملة (2/2)، انتظر دقيقة قبل الفحص التالي
        if len(open_positions) >= 2:
            log_print("⏸️ الصفقات مكتملة (2/2). بانتظار إغلاق إحداها لبدء صيد جديد...")
            time.sleep(60)
        else:
            time.sleep(10)

if __name__ == "__main__":
    run_bot()

