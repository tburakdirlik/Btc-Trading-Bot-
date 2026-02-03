"""
Bitcoin Haftalık Trading Botu
HAFTALıK %1.5 KAR HEDEFLİ VERSİYON

Haftada 1 alış, 1 satış sinyali üretir
Her sinyal %1.5 kar hedefine ulaşana kadar takip edilir
Telegram ile bildirim gönderir
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
import warnings
import logging
import sys

warnings.filterwarnings('ignore')

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BitcoinWeeklyBot:
    def __init__(self, telegram_token, telegram_chat_id):
        """
        Bot initialization - HAFTALIK %1.5 KAR HEDEFİ
        
        Args:
            telegram_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
        """
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'rateLimit': 1200,
            })
            self.symbol = 'BTC/USDT'
            self.timeframe = '1h'
            self.telegram_token = telegram_token
            self.telegram_chat_id = telegram_chat_id
            
            # HAFTALıK %1.5 KAR HEDEFİ SİSTEMİ
            self.weekly_profit_target = 1.5  # %1.5 haftalık hedef
            self.weekly_profit = 0.0  # Mevcut hafta kar
            self.week_start = self._get_week_start()
            
            # Sinyal durumu
            self.signals_this_week = {'buy': 0, 'sell': 0}
            self.signal_profit_target = 1.5  # Her sinyal %1.5 hedefler
            
            # İndikatör parametreleri
            self.rsi_period = 14
            self.rsi_oversold = 30
            self.rsi_overbought = 70
            self.ema_short = 20
            self.ema_long = 50
            self.bb_period = 20
            self.bb_std = 2
            
            # Minimum veri gereksinimleri
            self.min_data_length = max(
                self.rsi_period,
                self.ema_long,
                self.bb_period
            ) + 50
            
            logger.info("Bot başarıyla başlatıldı - Haftalık %1.5 kar hedefli sistem aktif")
            
        except Exception as e:
            logger.error(f"Bot başlatma hatası: {e}")
            raise
    
    def _get_week_start(self):
        """Haftanın başlangıcını hesapla (Pazartesi)"""
        today = datetime.now()
        start = today - timedelta(days=today.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _check_new_week(self):
        """Yeni hafta başladı mı kontrol et"""
        current_week_start = self._get_week_start()
        if current_week_start > self.week_start:
            logger.info(f"YENİ HAFTA BAŞLADI: {current_week_start.strftime('%Y-%m-%d')}")
            logger.info(f"Geçen hafta kar: %{self.weekly_profit:.2f}")
            
            self.week_start = current_week_start
            self.weekly_profit = 0.0  # Haftalık karı sıfırla
            self.signals_this_week = {'buy': 0, 'sell': 0}
            return True
        return False
    
    def _check_weekly_target_reached(self):
        """Haftalık %1.5 hedefe ulaşıldı mı?"""
        return self.weekly_profit >= self.weekly_profit_target
    
    def fetch_data(self, limit=200):
        """Binance'den OHLCV verisi çek"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    self.symbol, 
                    self.timeframe, 
                    limit=limit
                )
                
                if not ohlcv or len(ohlcv) == 0:
                    logger.warning(f"Veri boş geldi, deneme {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                
                df = pd.DataFrame(
                    ohlcv, 
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                if df.isnull().any().any():
                    logger.warning("Veri içinde NULL değerler var")
                    df = df.dropna()
                
                if len(df) < self.min_data_length:
                    logger.warning(f"Yetersiz veri: {len(df)} < {self.min_data_length}")
                    return None
                
                logger.info(f"{len(df)} adet mum verisi çekildi")
                return df
                
            except ccxt.RateLimitExceeded:
                logger.warning(f"Rate limit aşıldı, {retry_delay * 2} saniye bekleniyor...")
                time.sleep(retry_delay * 2)
            except ccxt.NetworkError as e:
                logger.error(f"Network hatası: {e}, deneme {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Veri çekme hatası: {e}, deneme {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
        
        return None
    
    def calculate_indicators(self, df):
        """Teknik indikatörleri hesapla"""
        try:
            df = df.copy()
            
            # RSI
            rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
            df['rsi'] = rsi.rsi()
            
            # EMA
            ema_short = EMAIndicator(close=df['close'], window=self.ema_short)
            ema_long = EMAIndicator(close=df['close'], window=self.ema_long)
            df['ema_20'] = ema_short.ema_indicator()
            df['ema_50'] = ema_long.ema_indicator()
            
            # MACD
            macd = MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = BollingerBands(
                close=df['close'], 
                window=self.bb_period, 
                window_dev=self.bb_std
            )
            df['bb_high'] = bb.bollinger_hband()
            df['bb_mid'] = bb.bollinger_mavg()
            df['bb_low'] = bb.bollinger_lband()
            
            # ATR
            atr = AverageTrueRange(
                high=df['high'], 
                low=df['low'], 
                close=df['close']
            )
            df['atr'] = atr.average_true_range()
            
            # Volume MA
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            
            df = df.dropna()
            
            if len(df) < 2:
                logger.error("İndikatör hesaplamadan sonra yetersiz veri")
                return None
            
            logger.info("İndikatörler başarıyla hesaplandı")
            return df
            
        except Exception as e:
            logger.error(f"İndikatör hesaplama hatası: {e}")
            return None
    
    def generate_signal(self, df):
        """Sinyal üret"""
        try:
            if df is None or len(df) < 2:
                return None, 0, [], None
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # NaN kontrolü
            required_fields = [
                'rsi', 'close', 'bb_low', 'bb_high', 'macd', 
                'macd_signal', 'ema_20', 'ema_50', 'volume', 
                'volume_ma', 'atr'
            ]
            
            for field in required_fields:
                if pd.isna(latest[field]):
                    logger.warning(f"{field} değeri NaN, sinyal üretilemiyor")
                    return None, 0, [], latest
            
            signal = None
            score = 0
            reasons = []
            
            # ALIŞ sinyali kontrolleri
            buy_conditions = 0
            buy_reasons = []
            
            if latest['rsi'] < 35:
                buy_conditions += 1
                buy_reasons.append(f"✓ RSI aşırı satım: {latest['rsi']:.1f}")
            
            bb_range = latest['bb_high'] - latest['bb_low']
            if bb_range > 0:
                price_to_lower = (latest['close'] - latest['bb_low']) / bb_range
                if price_to_lower < 0.2:
                    buy_conditions += 1
                    buy_reasons.append(f"✓ Fiyat BB alt bandına yakın")
            
            if not pd.isna(prev['macd']) and not pd.isna(prev['macd_signal']):
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    buy_conditions += 1
                    buy_reasons.append(f"✓ MACD bullish crossover")
                elif latest['macd'] > latest['macd_signal']:
                    buy_conditions += 0.5
                    buy_reasons.append(f"✓ MACD bullish")
            
            if latest['ema_20'] > latest['ema_50']:
                buy_conditions += 1
                buy_reasons.append(f"✓ EMA trend yukarı")
            elif latest['ema_50'] > 0:
                ema_diff_pct = abs(latest['ema_20'] - latest['ema_50']) / latest['ema_50']
                if ema_diff_pct < 0.01:
                    buy_conditions += 0.5
                    buy_reasons.append(f"✓ EMA'lar yakın (potansiyel golden cross)")
            
            if latest['volume_ma'] > 0:
                if latest['volume'] > latest['volume_ma'] * 1.2:
                    buy_conditions += 1
                    buy_reasons.append(f"✓ Hacim yüksek: {latest['volume']/latest['volume_ma']:.2f}x")
            
            # SATIŞ sinyali kontrolleri
            sell_conditions = 0
            sell_reasons = []
            
            if latest['rsi'] > 65:
                sell_conditions += 1
                sell_reasons.append(f"✓ RSI aşırı alım: {latest['rsi']:.1f}")
            
            if bb_range > 0:
                price_to_lower = (latest['close'] - latest['bb_low']) / bb_range
                if price_to_lower > 0.8:
                    sell_conditions += 1
                    sell_reasons.append(f"✓ Fiyat BB üst bandına yakın")
            
            if not pd.isna(prev['macd']) and not pd.isna(prev['macd_signal']):
                if latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    sell_conditions += 1
                    sell_reasons.append(f"✓ MACD bearish crossover")
                elif latest['macd'] < latest['macd_signal']:
                    sell_conditions += 0.5
                    sell_reasons.append(f"✓ MACD bearish")
            
            if latest['ema_20'] < latest['ema_50']:
                sell_conditions += 1
                sell_reasons.append(f"✓ EMA trend aşağı")
            elif latest['ema_50'] > 0:
                ema_diff_pct = abs(latest['ema_20'] - latest['ema_50']) / latest['ema_50']
                if ema_diff_pct < 0.01:
                    sell_conditions += 0.5
                    sell_reasons.append(f"✓ EMA'lar yakın (potansiyel death cross)")
            
            if latest['volume_ma'] > 0:
                if latest['volume'] > latest['volume_ma'] * 1.2:
                    sell_conditions += 1
                    sell_reasons.append(f"✓ Hacim yüksek: {latest['volume']/latest['volume_ma']:.2f}x")
            
            # Sinyal karar mekanizması
            if buy_conditions >= 4 and sell_conditions >= 4:
                if buy_conditions > sell_conditions:
                    signal = 'BUY'
                    score = buy_conditions
                    reasons = buy_reasons
                elif sell_conditions > buy_conditions:
                    signal = 'SELL'
                    score = sell_conditions
                    reasons = sell_reasons
            elif buy_conditions >= 4:
                signal = 'BUY'
                score = buy_conditions
                reasons = buy_reasons
            elif sell_conditions >= 4:
                signal = 'SELL'
                score = sell_conditions
                reasons = sell_reasons
            
            return signal, score, reasons, latest
            
        except Exception as e:
            logger.error(f"Sinyal üretme hatası: {e}")
            return None, 0, [], None
    
    def send_telegram_message(self, message):
        """Telegram'a mesaj gönder"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info("Telegram mesajı başarıyla gönderildi")
                    return True
                else:
                    logger.error(f"Telegram hatası (HTTP {response.status_code}): {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Telegram timeout, deneme {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"Telegram gönderim hatası: {e}, deneme {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
        
        logger.error("Telegram mesajı gönderilemedi (tüm denemeler başarısız)")
        return False
    
    def format_signal_message(self, signal, score, reasons, data):
        """Telegram mesajı formatla - %1.5 KAR HEDEFİ"""
        try:
            atr = data['atr'] if not pd.isna(data['atr']) else 0
            close = data['close'] if not pd.isna(data['close']) else 0
            
            if close == 0:
                logger.error("Fiyat bilgisi eksik, mesaj formatlanamıyor")
                return None
            
            # Stop-loss: ATR bazlı
            stop_loss_pct = (atr / close) * 100 * 2 if atr > 0 else 3
            
            # KAR HEDEFİ: %1.5 SABİT
            profit_target_pct = self.signal_profit_target  # %1.5
            
            if signal == 'BUY':
                emoji = "🟢"
                action = "ALIŞ"
                stop_loss = close * (1 - stop_loss_pct/100)
                take_profit = close * (1 + profit_target_pct/100)  # %1.5
            else:
                emoji = "🔴"
                action = "SATIŞ"
                stop_loss = close * (1 + stop_loss_pct/100)
                take_profit = close * (1 - profit_target_pct/100)  # %1.5
            
            rsi_val = data['rsi'] if not pd.isna(data['rsi']) else 0
            macd_val = data['macd'] if not pd.isna(data['macd']) else 0
            ema_20_val = data['ema_20'] if not pd.isna(data['ema_20']) else 0
            ema_50_val = data['ema_50'] if not pd.isna(data['ema_50']) else 0
            
            # Risk/Reward oranı
            risk_reward = profit_target_pct / stop_loss_pct if stop_loss_pct > 0 else 0
            
            message = f"""
{emoji} <b>BİTCOİN HAFTALIK SİNYAL</b> {emoji}

<b>Sinyal:</b> {action}
<b>Güç Skoru:</b> {score:.1f}/5.0
<b>Fiyat:</b> ${close:,.2f}

<b>Haftalık Durum:</b>
• Bu hafta kar: %{self.weekly_profit:.2f}
• Hedef: %{self.weekly_profit_target:.1f}
• Kalan: %{self.weekly_profit_target - self.weekly_profit:.2f}

<b>Teknik Analiz:</b>
{chr(10).join(reasons)}

<b>İndikatör Değerleri:</b>
• RSI: {rsi_val:.1f}
• MACD: {macd_val:.2f}
• EMA 20: ${ema_20_val:,.2f}
• EMA 50: ${ema_50_val:,.2f}

<b>Risk Yönetimi:</b>
• Stop-Loss: ${stop_loss:,.2f} ({stop_loss_pct:.1f}%)
• Take-Profit: ${take_profit:,.2f} ({profit_target_pct:.1f}%) ⭐
• Risk/Ödül: 1:{risk_reward:.2f}

<b>Tarih:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ <i>Bu sinyal %{profit_target_pct:.1f} kar hedefliyor</i>
"""
            return message
            
        except Exception as e:
            logger.error(f"Mesaj formatlama hatası: {e}")
            return None
    
    def run(self):
        """Ana bot döngüsü - HAFTALIK %1.5 HEDEFLİ"""
        logger.info("="*60)
        logger.info("Bitcoin Haftalık Trading Botu Başlatıldı")
        logger.info("HAFTALIK %1.5 KAR HEDEFİ SİSTEMİ AKTİF")
        logger.info("="*60)
        logger.info(f"Sembol: {self.symbol}")
        logger.info(f"Timeframe: {self.timeframe}")
        logger.info(f"Her sinyal hedefi: %{self.signal_profit_target}")
        logger.info(f"Haftalık toplam hedef: %{self.weekly_profit_target}")
        logger.info("="*60)
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while True:
            try:
                # Yeni hafta kontrolü
                self._check_new_week()
                
                # Haftalık hedefe ulaşıldı mı?
                if self._check_weekly_target_reached():
                    logger.info(f"✅ HAFTALIK %{self.weekly_profit_target} HEDEFE ULAŞILDI!")
                    logger.info(f"Bu hafta toplam kar: %{self.weekly_profit:.2f}")
                    logger.info("Yeni haftaya kadar bekleniyor...")
                    time.sleep(3600)  # 1 saat bekle
                    continue
                
                # Haftalık limit kontrolü (1 alış + 1 satış)
                if self.signals_this_week['buy'] >= 1 and self.signals_this_week['sell'] >= 1:
                    logger.info(
                        f"Bu hafta sinyal limiti doldu. "
                        f"Mevcut kar: %{self.weekly_profit:.2f} / Hedef: %{self.weekly_profit_target}"
                    )
                    time.sleep(3600)
                    continue
                
                # Veri çek
                logger.info("Veri çekiliyor...")
                df = self.fetch_data()
                
                if df is None:
                    consecutive_errors += 1
                    logger.warning(f"Veri çekme başarısız ({consecutive_errors}/{max_consecutive_errors})")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.critical("Çok fazla ardışık hata, bot durduruluyor!")
                        break
                    
                    time.sleep(300)
                    continue
                
                # İndikatörleri hesapla
                df = self.calculate_indicators(df)
                
                if df is None:
                    consecutive_errors += 1
                    logger.warning(f"İndikatör hesaplama başarısız ({consecutive_errors}/{max_consecutive_errors})")
                    time.sleep(300)
                    continue
                
                consecutive_errors = 0
                
                # Sinyal üret
                signal, score, reasons, latest_data = self.generate_signal(df)
                
                if latest_data is not None:
                    close_val = latest_data['close'] if not pd.isna(latest_data['close']) else 0
                    rsi_val = latest_data['rsi'] if not pd.isna(latest_data['rsi']) else 0
                    macd_val = latest_data['macd'] if not pd.isna(latest_data['macd']) else 0
                    logger.info(
                        f"Fiyat: ${close_val:,.2f} | RSI: {rsi_val:.1f} | MACD: {macd_val:.2f} | "
                        f"Haftalık kar: %{self.weekly_profit:.2f}/{self.weekly_profit_target}"
                    )
                
                if signal:
                    # Haftalık limit kontrolü
                    if signal == 'BUY' and self.signals_this_week['buy'] >= 1:
                        logger.info("ALIŞ sinyali var ama bu hafta limitine ulaşıldı")
                    elif signal == 'SELL' and self.signals_this_week['sell'] >= 1:
                        logger.info("SATIŞ sinyali var ama bu hafta limitine ulaşıldı")
                    else:
                        logger.info("="*60)
                        logger.info(f"🎯 {signal} SİNYALİ ÜRETİLDİ! (Skor: {score:.1f}/5.0)")
                        logger.info(f"Hedef kar: %{self.signal_profit_target}")
                        logger.info("="*60)
                        
                        # Telegram bildirimi gönder
                        message = self.format_signal_message(signal, score, reasons, latest_data)
                        
                        if message:
                            success = self.send_telegram_message(message)
                            
                            if success:
                                # Sinyal sayacını güncelle
                                if signal == 'BUY':
                                    self.signals_this_week['buy'] += 1
                                else:
                                    self.signals_this_week['sell'] += 1
                                
                                # Haftalık kar tahmini güncelle (sinyal başarılı olursa)
                                # Gerçek kar takibi için ayrı bir sistem gerekir
                                logger.info(
                                    f"Bu hafta sinyaller - "
                                    f"Alış: {self.signals_this_week['buy']}, "
                                    f"Satış: {self.signals_this_week['sell']}"
                                )
                            else:
                                logger.warning("Telegram mesajı gönderilemedi, sinyal sayılmadı")
                        else:
                            logger.error("Mesaj formatlanamadı")
                
                # 30 dakika bekle
                logger.info("Bekleniyor... (30 dakika)")
                time.sleep(1800)
                
            except KeyboardInterrupt:
                logger.info("\n\nBot kullanıcı tarafından durduruldu.")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Beklenmeyen hata: {e}", exc_info=True)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical("Çok fazla ardışık hata, bot durduruluyor!")
                    break
                
                time.sleep(300)


if __name__ == "__main__":
    # TELEGRAM AYARLARI - BU BİLGİLERİ DOLDUR
    TELEGRAM_BOT_TOKEN = "8551679910:AAHGcfPG2eYFSmGtK7azr5779xA88mMva_Q"
    TELEGRAM_CHAT_ID = "708692554"
    
    # Token kontrolü
    if "BURAYA" in TELEGRAM_BOT_TOKEN or "BURAYA" in TELEGRAM_CHAT_ID:
        print("\n" + "="*60)
        print("HATA: Telegram ayarları yapılmamış!")
        print("="*60)
        print("\n1. @BotFather ile bot oluştur ve TOKEN al")
        print("2. @userinfobot ile CHAT ID bul")
        print("3. Bu dosyayı düzenle ve bilgileri gir")
        print("\nDetaylı bilgi için KURULUM.md dosyasını oku")
        print("="*60)
        sys.exit(1)
    
    try:
        # Botu başlat
        bot = BitcoinWeeklyBot(
            telegram_token=TELEGRAM_BOT_TOKEN,
            telegram_chat_id=TELEGRAM_CHAT_ID
        )
        
        bot.run()
        
    except Exception as e:
        logger.critical(f"Bot başlatma hatası: {e}", exc_info=True)
        sys.exit(1)
