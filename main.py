import ccxt
import time
import os
import sys
from datetime import datetime

# ============ إعدادات القناص السريع (معدل لـ 1.3$) ============
class Config:
    LEVERAGE = 50                     
    MAX_OPEN_POSITIONS = 1            
    STOP_LOSS_PERCENT = 0.6          
    TAKE_PROFIT_PERCENT = 1.0        
    RSI_BUY_THRESHOLD = 42           
    MIN_VOLUME_USDT = 1000000        
    CHECK_INTERVAL = 15              

def log_print(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

# حساب RSI يدوي لتجنب مشاكل المكتبات
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def run_bot():
    BK = os.getenv("BINGX_APIKEY")
    BS = os.getenv("BINGX_SECRETKEY")
    
    try:
        ex = ccxt.bingx({'apiKey': BK, 'secret': BS, 'options': {'defaultType': 'swap'}})
        log_print("🚀 تم تشغيل القناص المطور - نسخة الاستقرار")
    except Exception as e:
        log_print(f"❌ خطأ اتصال: {e}")
        return

    while True:
        try:
            # فحص الرصيد والمراكز
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            
            positions = ex.fetch_positions()
            has_pos = any(float(p['info'].get('positionAmt', 0)) != 0 for p in positions)

            if has_pos:
                log_print("📦 توجد صفقة مفتوحة.. نراقبها")
                time.sleep(30)
                continue

            if avail < 1.0:
                log_print(f"💰 الرصيد {avail}$ منخفض")
                time.sleep(60)
                continue

            # مسح أفضل العملات
            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT') and t.get('quoteVolume', 0) > Config.MIN_VOLUME_USDT]
            symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:30]

            for symbol in symbols:
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    closes = [x[4] for x in ohlcv]
                    
                    rsi = calculate_rsi(closes)
                    
                    # شرط السعر: السعر الحالي فوق السعر السابق (بداية ارتداد)
                    if rsi < Config.RSI_BUY_THRESHOLD and closes[-1] > closes[-2]:
                        price = tickers[symbol]['last']
                        amount = (avail * 45) / price 
                        
                        log_print(f"🎯 فرصة في {symbol} | RSI: {rsi:.1f}")
                        
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        sl = price * (1 - Config.STOP_LOSS_PERCENT / 100)
                        
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        
                        log_print(f"✅ دخلنا الصفقة بسعر {price}")
                        break
                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            log_print(f"⚠️ تنبيه: {str(e)}")
            time.sleep(20)

if __name__ == "__main__":
    run_bot()

