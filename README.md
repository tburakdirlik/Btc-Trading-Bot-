# 🤖 Bitcoin Weekly Trading Bot: Complete Setup Guide

## Target: 1.5% Weekly Profit Strategy

This bot is designed to achieve a **1.5% weekly profit target** by generating high-quality signals (1 Buy + 1 Sell per week). It analyzes Bitcoin (BTC/USDT) on a 1-hour timeframe using 6 professional indicators.

---

### 📋 Prerequisites

Before you begin, ensure you have:

* **Python:** Version 3.8 or higher installed.
* **Telegram App:** To receive signal notifications.
* **Internet:** A stable connection for Binance data.

---

### 📥 Step 1: Install Dependencies

Open your terminal (Command Prompt, PowerShell, or Terminal) in the folder where your bot files are located.

**1. Install required Python packages:**

```bash
pip install -r requirements.txt

```

*If you are on Mac/Linux and `pip` doesn't work, try `pip3`.*

**The following libraries will be installed:**

* `ccxt` (Binance API)
* `pandas` (Data analysis)
* `ta` (Technical indicators)
* `requests` (Telegram communication)

---

### 📱 Step 2: Create Telegram Bot & Get Credentials

You need two things: a **Bot Token** and your **Chat ID**.

**2.1. Get Bot Token:**

1. Open Telegram and search for **@BotFather**.
2. Send the command: `/newbot`
3. Follow the instructions to name your bot.
4. **BotFather** will give you a **Token** (e.g., `123456:ABC-DEF...`). **Save this.**

**2.2. Get Your Chat ID:**

1. Search for **@userinfobot** in Telegram.
2. Click "Start".
3. It will reply with your ID (e.g., `987654321`). **Save this.**
* *Alternative:* You can also find this by sending a message to your new bot and checking the Telegram API updates URL.



---

### ⚙️ Step 3: Configure the Bot

You need to paste your Telegram credentials into the main code.

1. Open `bitcoin_weekly_bot.py` with a text editor (Notepad, VSCode, etc.).
2. Scroll to the very bottom of the file (around line 530).


3. Find the **TELEGRAM SETTINGS** section and replace the placeholder text with your actual data:

```python
# BEFORE
TELEGRAM_BOT_TOKEN = "BURAYA_TELEGRAM_BOT_TOKEN_YAZ"
TELEGRAM_CHAT_ID = "BURAYA_TELEGRAM_CHAT_ID_YAZ"

# AFTER (Example)
TELEGRAM_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx"
TELEGRAM_CHAT_ID = "987654321"

```

**Important:** Keep the quote marks (`""`) and do not add spaces.

---

### 🧪 Step 4: Test the Setup

Before running the main bot, run the test script to ensure everything is correct.

**Run the test:**

```bash
python test_setup.py

```

**What to look for:**

* ✅ **Packages:** Should show "Installed".
* ✅ **Binance Connection:** Should show the current BTC price.
* ✅ **Data Fetch:** Should successfully calculate indicators (RSI, MACD, etc.).
* ✅ **Telegram:** Should confirm settings are configured.

If you see **"🎉 TÜM TESTLER BAŞARILI!" (All Tests Passed)**, you are ready.

---

### 🚀 Step 5: Run the Bot

You have two ways to start the bot:

**Option A (Direct):**

```bash
python bitcoin_weekly_bot.py

```

**Option B (via Launcher):**

```bash
python start_bot.py

```

**Successful Startup:**
You should see logs indicating the "Weekly 1.5% Target System" is active and it is fetching data.

---

### 🧠 Step 6: Understanding the Strategy

The bot does not trade randomly. It follows a strict set of rules.

**The Weekly Cycle:**
**Monday 00:00:** Weekly profit counter resets to 0%.


* **Goal:** Hit 1.5% profit.
**Limit:** Maximum 1 Buy and 1 Sell signal per week.



**Buy Signal Conditions (Need 4 out of 5):**

1. **RSI:** < 35 (Oversold).


2. **Bollinger Bands:** Price is near the Lower Band.


3. **MACD:** Bullish crossover or momentum.


4. **EMA:** EMA 20 > EMA 50 (Upward trend) or Golden Cross potential.


5. **Volume:** 20% higher than average.



**Sell Signal Conditions:**

* Opposite of Buy (RSI > 65, Price near Upper Band, etc.).



**Risk Management:**

**Take Profit:** Fixed at 1.5% per signal. 
**Stop Loss:** Calculated dynamically using ATR (Volatility).



---

### 🛠 Troubleshooting & Customization

**Common Issues:**

* **Telegram 401 Unauthorized:** You pasted the Token wrong. Check for missing characters or extra spaces.
* **ModuleNotFoundError:** You didn't run `pip install -r requirements.txt`.

**Customization (Optional):**
To change the profit target, edit `bitcoin_weekly_bot.py`:

```python
self.weekly_profit_target = 2.0  # Change 1.5 to 2.0 for higher targets
self.signal_profit_target = 2.0

```

To change check frequency (default is 30 mins):

```python
time.sleep(3600)  # Change 1800 to 3600 for 1 hour

```

---

### ⚠️ Important Notes

* **Patience is Key:** The bot checks every 30 minutes. It may take days for the perfect signal conditions (4/5 score) to align.
* **Logs:** Monitor `bot.log` to see what the bot is doing in the background.
* **Financial Warning:** This bot generates signals. Past performance (backtesting) does not guarantee future results. Always use proper risk management.
