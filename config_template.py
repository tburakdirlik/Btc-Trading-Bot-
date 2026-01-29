# TELEGRAM AYARLARI
# Bu dosyayı kopyalayıp config.py olarak kaydedin ve bilgilerinizi girin

# 1. Telegram Bot Token
# BotFather'dan alacağınız token
# Örnek: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_BOT_TOKEN = "BURAYA_BOT_TOKEN_YAZIN"

# 2. Telegram Chat ID
# @userinfobot'tan alacağınız ID
# Örnek: "987654321"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZIN"

# ============================================
# İSTEĞE BAĞLI AYARLAR
# ============================================

# İndikatör Parametreleri
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

EMA_SHORT = 20
EMA_LONG = 50

BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# Sinyal Eşik Değerleri
MIN_SIGNAL_SCORE = 4.0  # Minimum 4/5 skor gerekli
MIN_VOLUME_MULTIPLIER = 1.2  # Hacim en az %20 fazla olmalı

# Kar/Zarar Yönetimi
TAKE_PROFIT_PERCENT = 5.0  # %5 kar hedefi
STOP_LOSS_ATR_MULTIPLIER = 2.0  # 2x ATR stop-loss

# Bot Kontrol Sıklığı (saniye)
CHECK_INTERVAL = 1800  # 30 dakika
