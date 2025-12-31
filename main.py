import ccxt
import time
import os
import sys
from datetime import datetime

class Config:
    LEVERAGE = 20                     
    MAX_OPEN_POSITIONS = 1            
    TAKE_PROFIT_PERCENT = 1.0        # تقليل الهدف لسرعة الخروج بربح
    MAX_LOSS_USD = 0.05              
    # حساسية فائقة: أي انحراف بسيط سيؤدي للدخول
    BUY_TRIGGER = 48                 # شراء إذا نزل RSI عن 48 (حساس جداً)
    SELL_TRIGGER = 52                # بيع إذا زاد RSI عن 52 (حساس جداً)
    CHECK_INTERVAL = 2               # فحص كل ثانيتين

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
        log_print("🔥 وضع الهجوم النشط: سأدخل في أول حركة للسوق!")
    except Exception as e:
        log_print(f"❌ خطأ: {e}")
        return

    while True:
        try:
            positions = ex.fetch_positions()
            open_pos = [p for p in positions if float(p['info'].get('positionAmt', 0)) != 0]

            if len(open_pos) >= Config.MAX_OPEN_POSITIONS:
                time.sleep(10)
                continue

            tickers = ex.fetch_tickers()
            # ترتيب العملات حسب التغير السعري لنجد الأكثر حركة
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT')]
            
            for symbol in symbols[:15]: # فحص أسرع 15 عملة فقط لضمان سرعة التنفيذ
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=15)
                    closes = [x[4] for x in ohlcv]
                    rsi = calculate_rsi(closes)
                    
                    log_print(f"👀 مراقبة {symbol} | RSI: {rsi:.1f}")

                    price = tickers[symbol]['last']
                    margin_to_use = 3.8 
                    raw_amount = (margin_to_use * Config.LEVERAGE) / price
                    amount = float(ex.amount_to_precision(symbol, raw_amount))

                    # شروط دخول فائقة الحساسية
                    if rsi < Config.BUY_TRIGGER:
                        sl = price - (Config.MAX_LOSS_USD / amount)
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        log_print(f"🚀 دخول شراء فوري: {symbol} (RSI: {rsi:.1f})")
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_buy_order(symbol, amount)
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        break
                    
                    elif rsi > Config.SELL_TRIGGER:
                        sl = price + (Config.MAX_LOSS_USD / amount)
                        tp = price * (1 - Config.TAKE_PROFIT_PERCENT / 100)
                        log_print(f"🔻 دخول بيع فوري: {symbol} (RSI: {rsi:.1f})")
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_sell_order(symbol, amount)
                        ex.create_order(symbol, 'limit', 'buy', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'buy', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        break
                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_bot()

