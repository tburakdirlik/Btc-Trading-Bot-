#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitcoin Günlük Trading Botu - Düzeltilmiş Versiyon
15 dakikalık timeframe ile günlük %0.8 kar hedefi
Tüm hatalar giderilmiş, optimizasyonlar eklenmiş
"""

import ccxt
import pandas as pd
import numpy as np
import time
import requests
import logging
from datetime import datetime, timedelta
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange

# ============================================
# TELEGRAM AYARLARI - BURAYA TOKENLERİNİZİ YAZIN
# ============================================
TELEGRAM_BOT_TOKEN = "BURAYA_BOT_TOKEN_YAZIN"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZIN"

# ============================================
# GÜNLÜK TRADING İÇİN OPTİMİZE EDİLMİŞ AYARLAR
# ============================================

# İndikatör Parametreleri (15 Dakikalık Timeframe)
RSI_PERIOD = 9
RSI_OVERSOLD = 25
RSI_OVERBOUGHT = 75

EMA_SHORT = 9
EMA_MEDIUM = 21
EMA_LONG = 50

MACD_FAST = 8
MACD_SLOW = 17
MACD_SIGNAL = 9

BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

STOCHASTIC_K = 14
STOCHASTIC_D = 3

# Sinyal Eşik Değerleri
MIN_SIGNAL_SCORE = 5  # Minimum 5/7 skor gerekli
MIN_VOLUME_MULTIPLIER = 1.3

# Kar/Zarar Yönetimi
DAILY_PROFIT_TARGET = 0.8  # %0.8 günlük kar hedefi
SIGNAL_PROFIT_TARGET = 0.8
STOP_LOSS_PERCENT = 2.5

# Bot Kontrol Ayarları
CHECK_INTERVAL = 300  # 5 dakika
MIN_SIGNAL_INTERVAL = 900  # 15 dakika (900 saniye)

# Timeframe
TIMEFRAME = '15m'

# Commission (Binance spot)
COMMISSION_PERCENT = 0.1  # %0.1 per trade

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BitcoinDailyBot:
    def __init__(self, telegram_token=None, telegram_chat_id=None):
        """Bot başlatma"""
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.symbol = 'BTC/USDT'
        self.timeframe = TIMEFRAME
        
        # Telegram
        self.telegram_token = telegram_token or TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = telegram_chat_id or TELEGRAM_CHAT_ID
        
        # Günlük trading parametreleri
        self.daily_profit_target = DAILY_PROFIT_TARGET
        self.signal_profit_target = SIGNAL_PROFIT_TARGET
        self.stop_loss_percent = STOP_LOSS_PERCENT
        self.commission_percent = COMMISSION_PERCENT
        
        # Durum takibi
        self.daily_profit = 0.0
        self.buy_signals = 0
        self.sell_signals = 0
        self.last_reset_date = datetime.now().date()
        self.last_signal_time = None  # Sinyal aralığı kontrolü için
        
        # Pozisyon bilgileri
        self.in_position = False
        self.position_type = None  # 'BUY' veya 'SELL'
        self.entry_price = None
        self.entry_time = None
        
        logging.info("="*60)
        logging.info("🚀 Bitcoin Günlük Trading Botu Başlatıldı")
        logging.info("="*60)
        logging.info(f"⏱️  Timeframe: {TIMEFRAME} (15 dakika)")
        logging.info(f"💰 Günlük Hedef: %{self.daily_profit_target}")
        logging.info(f"🛑 Stop Loss: %{self.stop_loss_percent}")
        logging.info(f"🔄 Kontrol Aralığı: {CHECK_INTERVAL}s (5 dakika)")
        logging.info(f"⏳ Min Sinyal Aralığı: {MIN_SIGNAL_INTERVAL}s (15 dakika)")
        logging.info(f"📊 Min Skor: {MIN_SIGNAL_SCORE}/7")
        logging.info("="*60)
        
        self.send_telegram("🚀 *Günlük Bot Başlatıldı*\n\n"
                          f"⏱️ Timeframe: {TIMEFRAME}\n"
                          f"💰 Günlük Hedef: %{self.daily_profit_target}\n"
                          f"🛑 Stop Loss: %{self.stop_loss_percent}\n"
                          f"📊 Min Skor: {MIN_SIGNAL_SCORE}/7")
    
    def send_telegram(self, message):
        """Telegram mesajı gönder"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Telegram mesaj hatası: {e}")
            return False
    
    def check_daily_reset(self):
        """Günlük sayaçları sıfırla (gece yarısı)"""
        current_date = datetime.now().date()
        
        if current_date > self.last_reset_date:
            logging.info("="*60)
            logging.info("🌅 YENİ GÜN - Sayaçlar Sıfırlandı")
            logging.info("="*60)
            logging.info(f"📅 Tarih: {current_date}")
            logging.info(f"💰 Önceki Gün Kar: %{self.daily_profit:.2f}")
            logging.info(f"📊 Alış Sinyalleri: {self.buy_signals}")
            logging.info(f"📊 Satış Sinyalleri: {self.sell_signals}")
            logging.info("="*60)
            
            self.send_telegram(f"🌅 *Yeni Gün Başladı*\n\n"
                             f"📅 {current_date}\n"
                             f"💰 Dün Kar: %{self.daily_profit:.2f}\n"
                             f"📊 Alış: {self.buy_signals} | Satış: {self.sell_signals}")
            
            # Sıfırla
            self.daily_profit = 0.0
            self.buy_signals = 0
            self.sell_signals = 0
            self.last_reset_date = current_date
            
            # Pozisyon varsa uyar
            if self.in_position:
                logging.warning("⚠️ Gün değişti ama açık pozisyon var!")
                self.send_telegram("⚠️ *Dikkat*: Gün değişti, açık pozisyon var!\n"
                                 f"Tip: {self.position_type}\n"
                                 f"Giriş: ${self.entry_price:,.2f}")
    
    def check_signal_interval(self):
        """Minimum sinyal aralığını kontrol et (15 dakika)"""
        if self.last_signal_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        
        if time_since_last < MIN_SIGNAL_INTERVAL:
            remaining = MIN_SIGNAL_INTERVAL - time_since_last
            logging.debug(f"⏳ Sinyal aralığı: {remaining:.0f}s kaldı")
            return False
        
        return True
    
    def fetch_data(self):
        """15 dakikalık veri çek"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=200)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logging.error(f"Veri çekme hatası: {e}")
            return None
    
    def calculate_vwap(self, df):
        """VWAP (Volume Weighted Average Price) hesapla - günlük"""
        try:
            # Bugünün verilerini filtrele
            today = datetime.now().date()
            df_today = df[df['timestamp'].dt.date == today].copy()
            
            if len(df_today) == 0:
                return None
            
            # VWAP = (Price × Volume) toplamı / Volume toplamı
            df_today['typical_price'] = (df_today['high'] + df_today['low'] + df_today['close']) / 3
            df_today['vwap_numerator'] = df_today['typical_price'] * df_today['volume']
            
            vwap = df_today['vwap_numerator'].sum() / df_today['volume'].sum()
            return vwap
            
        except Exception as e:
            logging.error(f"VWAP hesaplama hatası: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Tüm indikatörleri hesapla (7 indikatör)"""
        try:
            # RSI (9 period - hızlı tepki)
            rsi = RSIIndicator(close=df['close'], window=RSI_PERIOD)
            df['rsi'] = rsi.rsi()
            
            # EMA (3 katman: 9, 21, 50)
            ema_short = EMAIndicator(close=df['close'], window=EMA_SHORT)
            ema_medium = EMAIndicator(close=df['close'], window=EMA_MEDIUM)
            ema_long = EMAIndicator(close=df['close'], window=EMA_LONG)
            
            df['ema_short'] = ema_short.ema_indicator()
            df['ema_medium'] = ema_medium.ema_indicator()
            df['ema_long'] = ema_long.ema_indicator()
            
            # MACD (8, 17, 9 - hızlı sinyal)
            macd = MACD(close=df['close'], window_slow=MACD_SLOW, 
                       window_fast=MACD_FAST, window_sign=MACD_SIGNAL)
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            
            # Bollinger Bands
            bb = BollingerBands(close=df['close'], window=BOLLINGER_PERIOD, window_dev=BOLLINGER_STD)
            df['bb_high'] = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            df['bb_mid'] = bb.bollinger_mavg()
            
            # Stochastic Oscillator
            stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'],
                                        window=STOCHASTIC_K, smooth_window=STOCHASTIC_D)
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Volume
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # ATR (stop loss için)
            atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'])
            df['atr'] = atr.average_true_range()
            
            # VWAP (günlük)
            vwap = self.calculate_vwap(df)
            df['vwap'] = vwap
            
            return df
            
        except Exception as e:
            logging.error(f"İndikatör hesaplama hatası: {e}")
            return None
    
    def generate_signals(self, df):
        """7 indikatör ile sinyal üret (minimum 5/7 skor)"""
        if df is None or len(df) < 100:
            return None, 0
        
        latest = df.iloc[-1]
        current_price = latest['close']
        
        # BUY SİNYALİ (7 kontrol)
        buy_score = 0
        buy_reasons = []
        
        # 1. RSI Oversold (<25)
        if latest['rsi'] < RSI_OVERSOLD:
            buy_score += 1
            buy_reasons.append(f"RSI({latest['rsi']:.1f})<{RSI_OVERSOLD}")
        
        # 2. Bollinger Alt Band
        bb_position = (current_price - latest['bb_low']) / (latest['bb_high'] - latest['bb_low'])
        if bb_position < 0.2:  # Alt %20 bölgede
            buy_score += 1
            buy_reasons.append(f"BB Alt(%{bb_position*100:.0f})")
        
        # 3. MACD Bullish
        if latest['macd'] > latest['macd_signal']:
            buy_score += 1
            buy_reasons.append("MACD+")
        
        # 4. EMA Trend (9>21 veya yükseliş)
        if latest['ema_short'] > latest['ema_medium']:
            buy_score += 1
            buy_reasons.append("EMA+")
        
        # 5. Stochastic Oversold (<20)
        if latest['stoch_k'] < 20:
            buy_score += 1
            buy_reasons.append(f"Stoch({latest['stoch_k']:.0f})<20")
        
        # 6. Volume Artışı
        if latest['volume_ratio'] > MIN_VOLUME_MULTIPLIER:
            buy_score += 1
            buy_reasons.append(f"Vol({latest['volume_ratio']:.1f}x)")
        
        # 7. VWAP Altında (değerli bölge)
        if latest['vwap'] and current_price < latest['vwap']:
            buy_score += 1
            buy_reasons.append(f"VWAP Altı")
        
        # SELL SİNYALİ (7 kontrol)
        sell_score = 0
        sell_reasons = []
        
        # 1. RSI Overbought (>75)
        if latest['rsi'] > RSI_OVERBOUGHT:
            sell_score += 1
            sell_reasons.append(f"RSI({latest['rsi']:.1f})>{RSI_OVERBOUGHT}")
        
        # 2. Bollinger Üst Band
        if bb_position > 0.8:  # Üst %20 bölgede
            sell_score += 1
            sell_reasons.append(f"BB Üst(%{bb_position*100:.0f})")
        
        # 3. MACD Bearish
        if latest['macd'] < latest['macd_signal']:
            sell_score += 1
            sell_reasons.append("MACD-")
        
        # 4. EMA Trend (9<21 veya düşüş)
        if latest['ema_short'] < latest['ema_medium']:
            sell_score += 1
            sell_reasons.append("EMA-")
        
        # 5. Stochastic Overbought (>80)
        if latest['stoch_k'] > 80:
            sell_score += 1
            sell_reasons.append(f"Stoch({latest['stoch_k']:.0f})>80")
        
        # 6. Volume Artışı
        if latest['volume_ratio'] > MIN_VOLUME_MULTIPLIER:
            sell_score += 1
            sell_reasons.append(f"Vol({latest['volume_ratio']:.1f}x)")
        
        # 7. VWAP Üstünde (pahalı bölge)
        if latest['vwap'] and current_price > latest['vwap']:
            sell_score += 1
            sell_reasons.append(f"VWAP Üstü")
        
        # Sinyal kararı (minimum 5/7)
        signal = None
        score = 0
        reasons = []
        
        if buy_score >= MIN_SIGNAL_SCORE:
            signal = 'BUY'
            score = buy_score
            reasons = buy_reasons
        elif sell_score >= MIN_SIGNAL_SCORE:
            signal = 'SELL'
            score = sell_score
            reasons = sell_reasons
        
        # Debug log
        if buy_score >= 4 or sell_score >= 4:
            logging.debug(f"📊 BUY: {buy_score}/7 | SELL: {sell_score}/7")
        
        return signal, score, reasons if signal else None
    
    def calculate_targets(self, signal, entry_price):
        """Kar hedefi ve stop loss hesapla"""
        if signal == 'BUY':
            take_profit = entry_price * (1 + self.signal_profit_target / 100)
            stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
        else:  # SELL
            take_profit = entry_price * (1 - self.signal_profit_target / 100)
            stop_loss = entry_price * (1 + self.stop_loss_percent / 100)
        
        return take_profit, stop_loss
    
    def check_profit_with_commission(self, signal, entry_price, current_price):
        """Commission dahil kar/zarar hesapla"""
        if signal == 'BUY':
            gross_profit_percent = ((current_price - entry_price) / entry_price) * 100
        else:  # SELL
            gross_profit_percent = ((entry_price - current_price) / entry_price) * 100
        
        # Commission düş (alış + satış)
        net_profit_percent = gross_profit_percent - (2 * self.commission_percent)
        
        return net_profit_percent
    
    def check_position(self, df):
        """Açık pozisyonu kontrol et"""
        if not self.in_position:
            return
        
        latest = df.iloc[-1]
        current_price = latest['close']
        
        # Commission dahil kar/zarar
        net_profit = self.check_profit_with_commission(
            self.position_type, self.entry_price, current_price
        )
        
        take_profit, stop_loss = self.calculate_targets(self.position_type, self.entry_price)
        
        # Kar hedefine ulaşıldı mı?
        profit_reached = False
        if self.position_type == 'BUY' and current_price >= take_profit:
            profit_reached = True
        elif self.position_type == 'SELL' and current_price <= take_profit:
            profit_reached = True
        
        # Stop loss tetiklendi mi?
        stop_hit = False
        if self.position_type == 'BUY' and current_price <= stop_loss:
            stop_hit = True
        elif self.position_type == 'SELL' and current_price >= stop_loss:
            stop_hit = True
        
        # Pozisyonu kapat
        if profit_reached:
            self.close_position(current_price, net_profit, "Kar Hedefi")
        elif stop_hit:
            self.close_position(current_price, net_profit, "Stop Loss")
        else:
            # Durum logu
            duration = (datetime.now() - self.entry_time).total_seconds() / 60
            logging.debug(f"💼 Pozisyon: {self.position_type} | Kar: %{net_profit:.2f} | "
                         f"Süre: {duration:.0f}dk | Hedef: ${take_profit:,.0f}")
    
    def close_position(self, exit_price, net_profit, reason):
        """Pozisyonu kapat"""
        duration = (datetime.now() - self.entry_time).total_seconds() / 60
        
        # Günlük kara ekle
        self.daily_profit += net_profit
        
        # Log
        logging.info("="*60)
        logging.info(f"🔔 POZİSYON KAPANDI: {reason}")
        logging.info("="*60)
        logging.info(f"📊 Tip: {self.position_type}")
        logging.info(f"💵 Giriş: ${self.entry_price:,.2f}")
        logging.info(f"💵 Çıkış: ${exit_price:,.2f}")
        logging.info(f"💰 Net Kar: %{net_profit:.2f} (commission dahil)")
        logging.info(f"⏱️  Süre: {duration:.1f} dakika")
        logging.info(f"📈 Günlük Toplam: %{self.daily_profit:.2f}")
        logging.info("="*60)
        
        # Telegram
        emoji = "✅" if net_profit > 0 else "❌"
        self.send_telegram(
            f"{emoji} *Pozisyon Kapandı*\n\n"
            f"📊 {self.position_type}\n"
            f"💵 Giriş: ${self.entry_price:,.0f}\n"
            f"💵 Çıkış: ${exit_price:,.0f}\n"
            f"💰 Net Kar: *%{net_profit:.2f}*\n"
            f"⏱️ Süre: {duration:.0f}dk\n"
            f"📝 Sebep: {reason}\n\n"
            f"📈 Günlük Toplam: %{self.daily_profit:.2f}"
        )
        
        # Pozisyonu sıfırla
        self.in_position = False
        self.position_type = None
        self.entry_price = None
        self.entry_time = None
    
    def execute_signal(self, signal, score, reasons, current_price):
        """Sinyali uygula"""
        # Günlük hedefe ulaşıldı mı?
        if self.daily_profit >= self.daily_profit_target:
            logging.info(f"🎯 Günlük hedef zaten ulaşıldı (%{self.daily_profit:.2f})")
            return
        
        # Günlük sinyal limitleri
        if signal == 'BUY' and self.buy_signals >= 1:
            logging.info("⚠️ Bugün zaten 1 alış sinyali üretildi")
            return
        
        if signal == 'SELL' and self.sell_signals >= 1:
            logging.info("⚠️ Bugün zaten 1 satış sinyali üretildi")
            return
        
        # Sinyal aralığı kontrolü
        if not self.check_signal_interval():
            return
        
        # Hedef ve stop loss hesapla
        take_profit, stop_loss = self.calculate_targets(signal, current_price)
        
        # Log
        logging.info("="*60)
        logging.info(f"🎯 {signal} SİNYALİ ÜRETİLDİ! (Skor: {score}/7)")
        logging.info("="*60)
        logging.info(f"💵 Fiyat: ${current_price:,.2f}")
        logging.info(f"📊 Sebepler: {', '.join(reasons)}")
        logging.info(f"🎯 Hedef: ${take_profit:,.2f} (+%{self.signal_profit_target})")
        logging.info(f"🛑 Stop Loss: ${stop_loss:,.2f} (-%{self.stop_loss_percent})")
        logging.info(f"💼 Risk/Reward: 1:{self.signal_profit_target/self.stop_loss_percent:.2f}")
        logging.info("="*60)
        
        # Telegram
        self.send_telegram(
            f"🎯 *{signal} Sinyali*\n\n"
            f"📊 Skor: {score}/7\n"
            f"💵 Fiyat: ${current_price:,.0f}\n"
            f"📝 {', '.join(reasons[:3])}\n\n"
            f"🎯 Hedef: ${take_profit:,.0f} (+%{self.signal_profit_target})\n"
            f"🛑 Stop: ${stop_loss:,.0f} (-%{self.stop_loss_percent})\n"
            f"💼 R/R: 1:{self.signal_profit_target/self.stop_loss_percent:.1f}"
        )
        
        # Sayaçları güncelle
        if signal == 'BUY':
            self.buy_signals += 1
        else:
            self.sell_signals += 1
        
        # Son sinyal zamanını kaydet
        self.last_signal_time = datetime.now()
        
        # Pozisyonu aç
        self.in_position = True
        self.position_type = signal
        self.entry_price = current_price
        self.entry_time = datetime.now()
    
    def run(self):
        """Ana döngü"""
        logging.info("🔄 Ana döngü başladı...")
        consecutive_errors = 0
        max_errors = 10
        
        while True:
            try:
                # Günlük reset kontrolü
                self.check_daily_reset()
                
                # Veri çek
                df = self.fetch_data()
                if df is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        self.send_telegram("❌ *HATA*: Çok fazla ardışık hata!")
                        break
                    time.sleep(60)
                    continue
                
                consecutive_errors = 0
                
                # İndikatörleri hesapla
                df = self.calculate_indicators(df)
                if df is None:
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                current_price = df.iloc[-1]['close']
                
                # Açık pozisyon varsa kontrol et
                if self.in_position:
                    self.check_position(df)
                else:
                    # Yeni sinyal ara
                    signal, score, reasons = self.generate_signals(df)
                    
                    if signal:
                        self.execute_signal(signal, score, reasons, current_price)
                
                # Bekleme
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logging.info("\n👋 Bot durduruldu (kullanıcı)")
                self.send_telegram("👋 Bot durduruldu")
                break
            
            except Exception as e:
                logging.error(f"❌ Beklenmeyen hata: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    self.send_telegram(f"❌ *HATA*: {e}")
                    break
                time.sleep(60)

def main():
    """Ana fonksiyon"""
    try:
        bot = BitcoinDailyBot()
        bot.run()
    except Exception as e:
        logging.error(f"Fatal hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
