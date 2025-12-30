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
    log_print("✅ تفعيل البوت الاحترافي بمؤشر RSI (صفقتين كحد أقصى)")
except Exception as e:
    log_print(f"❌ خطأ اتصال: {e}")

# القائمة الشاملة المختارة بعناية
symbols = [
    "AVAX/USDT", "DOGE/USDT", "NEAR/USDT", "MATIC/USDT", "ADA/USDT", "XRP/USDT", 
    "LINK/USDT", "DOT/USDT", "SHIB/USDT", "LTC/USDT", "BCH/USDT", "UNI/USDT",
    "OP/USDT", "ARB/USDT", "APT/USDT", "SUI/USDT", "PEPE/USDT", "FLOKI/USDT",
    "BONK/USDT", "WIF/USDT", "JUP/USDT", "PYTH/USDT", "LDO/USDT", "ETC/USDT"
]

def calculate_rsi(symbol):
    try:
        bars = ex.fetch_ohlcv(symbol, timeframe='5m', limit=20)
        closes = [x[4] for x in bars]
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except:
        return 50 # قيمة محايدة في حال الخطأ

def run_bot():
    while True:
        for symbol in symbols:
            try:
                # 1. التأكد من عدد الصفقات المفتوحة (بحد أقصى 2)
                positions = ex.fetch_positions()
                open_positions = [p for p in positions if float(p['info'].get('positionAmt', 0)) != 0]
                
                if len(open_positions) < 2:
                    # 2. تحليل العملة باستخدام RSI
                    rsi_value = calculate_rsi(symbol)
                    
                    # لا يدخل إلا إذا كانت العملة رخيصة جداً (RSI < 35)
                    if rsi_value < 35:
                        balance = ex.fetch_balance()
                        avail = balance['free'].get('USDT', 0)
                        
                        if avail > 0.1: # هامش بسيط جداً مطلوب
                            ticker = ex.fetch_ticker(symbol)
                            price = ticker['last']
                            amount = 2.1 / price # قيمة الصفقة في السوق
                            
                            order = ex.create_market_order(symbol, 'buy', amount)
                            log_print(f"🎯 فرصة ذهبية! RSI={rsi_value:.2f} | تم دخول {symbol}")
                            
                            # أهدافك الثابتة (10% ربح / 2% خسارة)
                            tp_price = price * 1.005 
                            sl_price = price * 0.999 
                            
                            ex.create_order(symbol, 'limit', 'sell', amount, tp_price, {'reduceOnly': True})
                            ex.create_order(symbol, 'stop', 'sell', amount, None, {
                                'stopPrice': sl_price, 'reduceOnly': True
                            })
                            log_print(f"✅ تم ضبط الحماية والهدف لـ {symbol}")
                
                time.sleep(4) # فحص هادئ ودقيق
            except Exception as e:
                time.sleep(2)
        
        log_print("🔄 الرادار أكمل دورة فحص كاملة بمؤشرات RSI...")
        time.sleep(20)

if __name__ == "__main__":
    run_bot()

