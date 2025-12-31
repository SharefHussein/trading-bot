import ccxt
import time
import os
import sys

# تقليل الرسائل للحد الأدنى (فقط عند التنفيذ)
def log_print(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

class Config:
    LEVERAGE = 20
    MAX_OPEN_POSITIONS = 1
    TAKE_PROFIT_PERCENT = 1.0
    MAX_LOSS_USD = 0.05
    # حساسية قصوى للدخول الفوري
    BUY_TRIGGER = 49.9 
    SELL_TRIGGER = 50.1
    CHECK_INTERVAL = 1 # فحص كل ثانية واحدة

def calculate_rsi(prices):
    period = 14
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
    ex = ccxt.bingx({'apiKey': BK, 'secret': BS, 'options': {'defaultType': 'swap'}})
    
    log_print("🚀 تم تشغيل المحرك الصامت.. البحث عن صفقات قائم الآن")

    while True:
        try:
            # فحص سريع جداً لوجود صفقات
            positions = ex.fetch_positions()
            if any(float(p['info'].get('positionAmt', 0)) != 0 for p in positions):
                time.sleep(10)
                continue

            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT')]
            
            for symbol in symbols[:20]: # فحص أسرع 20 عملة في السوق
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=15)
                    rsi = calculate_rsi([x[4] for x in ohlcv])
                    price = tickers[symbol]['last']
                    
                    # حساب الكمية
                    amount = float(ex.amount_to_precision(symbol, (3.8 * Config.LEVERAGE) / price))

                    if rsi < Config.BUY_TRIGGER:
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_buy_order(symbol, amount)
                        # وضع الأهداف
                        ex.create_order(symbol, 'limit', 'sell', amount, price * (1 + Config.TAKE_PROFIT_PERCENT/100), {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': price - (Config.MAX_LOSS_USD/amount), 'reduceOnly': True})
                        log_print(f"✅ تم فتح شراء في {symbol}")
                        break
                    
                    elif rsi > Config.SELL_TRIGGER:
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_sell_order(symbol, amount)
                        # وضع الأهداف
                        ex.create_order(symbol, 'limit', 'buy', amount, price * (1 - Config.TAKE_PROFIT_PERCENT/100), {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'buy', amount, None, {'stopPrice': price + (Config.MAX_LOSS_USD/amount), 'reduceOnly': True})
                        log_print(f"✅ تم فتح بيع في {symbol}")
                        break
                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)
        except: time.sleep(5)

if __name__ == "__main__":
    run_bot()

