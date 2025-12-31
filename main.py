import ccxt
import time
import os
import sys
from datetime import datetime

class Config:
    LEVERAGE = 20                     
    MAX_OPEN_POSITIONS = 1            
    TAKE_PROFIT_PERCENT = 1.2        
    MAX_LOSS_USD = 0.05              # خط أحمر لا يتجاوزه البوت
    CHECK_INTERVAL = 5               

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
        log_print("🤖 البوت الذكي نشط.. يبحث عن أفضل فرصة متاحة الآن")
    except Exception as e:
        log_print(f"❌ خطأ اتصال: {e}")
        return

    while True:
        try:
            positions = ex.fetch_positions()
            open_pos = [p for p in positions if float(p['info'].get('positionAmt', 0)) != 0]

            if len(open_pos) >= Config.MAX_OPEN_POSITIONS:
                time.sleep(20)
                continue

            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT')]
            
            best_opportunity = None
            max_deviation = 0 # لقياس مدى ابتعاد العملة عن المنطقة المستقرة

            for symbol in symbols[:40]: 
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                    closes = [x[4] for x in ohlcv]
                    rsi = calculate_rsi(closes)
                    
                    # البوت يبحث عن العملة الأكثر انحرافاً عن رقم 50 (سواء صعوداً أو هبوطاً)
                    deviation = abs(rsi - 50)
                    if deviation > max_deviation:
                        max_deviation = deviation
                        best_opportunity = {'symbol': symbol, 'rsi': rsi, 'price': tickers[symbol]['last']}
                except: continue

            if best_opportunity and max_deviation > 5: # إذا وجد انحرافاً واضحاً عن الاستقرار
                symbol = best_opportunity['symbol']
                rsi = best_opportunity['rsi']
                price = best_opportunity['price']
                
                margin_to_use = 3.5 
                raw_amount = (margin_to_use * Config.LEVERAGE) / price
                amount = float(ex.amount_to_precision(symbol, raw_amount))

                if rsi < 50: # الاتجاه هابط، إذاً هي فرصة شراء (Long)
                    sl = price - (Config.MAX_LOSS_USD / amount)
                    tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                    log_print(f"🌟 أفضل فرصة شراء: {symbol} (RSI: {rsi:.1f})")
                    ex.set_leverage(Config.LEVERAGE, symbol)
                    ex.create_market_buy_order(symbol, amount)
                    ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                    ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                
                else: # الاتجاه صاعد، إذاً هي فرصة بيع (Short)
                    sl = price + (Config.MAX_LOSS_USD / amount)
                    tp = price * (1 - Config.TAKE_PROFIT_PERCENT / 100)
                    log_print(f"🌟 أفضل فرصة بيع: {symbol} (RSI: {rsi:.1f})")
                    ex.set_leverage(Config.LEVERAGE, symbol)
                    ex.create_market_sell_order(symbol, amount)
                    ex.create_order(symbol, 'limit', 'buy', amount, tp, {'reduceOnly': True})
                    ex.create_order(symbol, 'stop', 'buy', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                
                log_print(f"✅ تم التنفيذ آلياً بناءً على تحليل السوق.")
                time.sleep(30) # انتظار بعد التنفيذ
            
            time.sleep(Config.CHECK_INTERVAL)
        except: time.sleep(10)

if __name__ == "__main__":
    run_bot()

