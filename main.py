import ccxt
import time
import os
import sys
from datetime import datetime

# ============ إعدادات القناص العدواني (تجاوز الحد الأدنى) ============
class Config:
    LEVERAGE = 50                     
    MAX_OPEN_POSITIONS = 1            # تركيز كامل الرصيد في صفقة واحدة لضمان قوتها
    STOP_LOSS_PERCENT = 1.2          
    TAKE_PROFIT_PERCENT = 1.5        
    RSI_BUY_THRESHOLD = 55           # دخول سريع جداً
    MIN_VOLUME_USDT = 500000         
    CHECK_INTERVAL = 10              

def log_print(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

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
        log_print("🔥 تم تشغيل النسخة النهائية - تجاوز قيود الحد الأدنى")
    except Exception as e:
        log_print(f"❌ خطأ اتصال: {e}")
        return

    while True:
        try:
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            
            positions = ex.fetch_positions()
            open_pos_count = len([p for p in positions if float(p['info'].get('positionAmt', 0)) != 0])

            if open_pos_count >= Config.MAX_OPEN_POSITIONS:
                time.sleep(20)
                continue

            if avail < 1.0:
                log_print(f"💰 الرصيد المتاح {avail:.2f}$ قليل جداً")
                time.sleep(30)
                continue

            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT') and t.get('quoteVolume', 0) > Config.MIN_VOLUME_USDT]
            symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:100]

            for symbol in symbols:
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    closes = [x[4] for x in ohlcv]
                    rsi = calculate_rsi(closes)
                    
                    if rsi < Config.RSI_BUY_THRESHOLD:
                        price = tickers[symbol]['last']
                        
                        # التعديل الجوهري: استخدام 95% من الرصيد مع الرافعة لكسر حاجز الـ 2.01$
                        # القيمة الإجمالية ستكون حوالي 70$ (1.47 * 0.95 * 50)
                        amount = (avail * 0.95 * Config.LEVERAGE) / price 
                        
                        log_print(f"⚡ محاولة دخول: {symbol} بقيمة إجمالية تقديرية {avail * 0.95 * Config.LEVERAGE:.2f}$")
                        
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        sl = price * (1 - Config.STOP_LOSS_PERCENT / 100)
                        
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        
                        log_print(f"✅ تم التنفيذ بنجاح في {symbol}")
                        break 
                except Exception as e:
                    continue
            
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    run_bot()

