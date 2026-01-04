# Telegram Bot Setup Guide

A comprehensive guide for setting up and configuring the Telegram bot for the lighter-paradex-arbitrage trading system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Creating a Telegram Bot](#creating-a-telegram-bot)
3. [Configuration](#configuration)
4. [Installation](#installation)
5. [Running the Bot](#running-the-bot)
6. [Available Commands](#available-commands)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

## Prerequisites

Before setting up the Telegram bot, ensure you have:

- Python 3.8 or higher installed
- A Telegram account
- Access to Telegram's BotFather (@BotFather)
- The lighter-paradex-arbitrage repository cloned
- Required dependencies installed (see [Installation](#installation))

## Creating a Telegram Bot

### Step 1: Open Telegram and Find BotFather

1. Open Telegram on your device or web client
2. Search for **@BotFather** in the search box
3. Start a conversation with BotFather

### Step 2: Create a New Bot

1. Send the command `/newbot` to BotFather
2. Follow the prompts:
   - **Bot name**: Enter a display name for your bot (e.g., "Paradex Arbitrage Bot")
   - **Username**: Enter a unique username (must end with "bot", e.g., "paradex_arb_bot")
3. BotFather will provide you with:
   - **API Token**: A long string that looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
   - Keep this token secure and never share it

### Step 3: Configure Bot Settings (Optional)

To customize your bot further:

1. Send `/mybots` to BotFather
2. Select your bot
3. Choose "Edit Bot" to customize:
   - Description: Brief info about what the bot does
   - Commands: List of commands the bot supports
   - Profile picture: Add a bot avatar
   - Default administrator rights: Configure permissions

### Step 4: Get Your Chat ID

To enable private messages to your bot:

1. Start a conversation with your bot by sending `/start`
2. Use this URL to get your Chat ID: `https://api.telegram.org/bot<YOUR_API_TOKEN>/getUpdates`
3. Replace `<YOUR_API_TOKEN>` with your actual token
4. Look for the `"id"` field in the chat object - this is your Chat ID
5. Alternatively, forward a message from the bot to @userinfobot to get your user ID

## Configuration

### Environment Variables

Create a `.env` file in the project root directory with the following variables:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=<YOUR_BOT_API_TOKEN>
TELEGRAM_CHAT_ID=<YOUR_CHAT_ID>

# Trading Configuration
EXCHANGE_API_KEY=<YOUR_EXCHANGE_API_KEY>
EXCHANGE_API_SECRET=<YOUR_EXCHANGE_API_SECRET>

# Optional: Logging and Monitoring
LOG_LEVEL=INFO
WEBHOOK_URL=<OPTIONAL_WEBHOOK_URL>
```

### Configuration File

Alternatively, create a `config.yaml` file:

```yaml
telegram:
  bot_token: <YOUR_BOT_API_TOKEN>
  chat_id: <YOUR_CHAT_ID>
  polling_interval: 60  # seconds

trading:
  exchange_api_key: <YOUR_EXCHANGE_API_KEY>
  exchange_api_secret: <YOUR_EXCHANGE_API_SECRET>
  
monitoring:
  log_level: INFO
  enable_webhooks: false
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage.git
cd lighter-paradex-arbitrage
```

### 2. Create a Virtual Environment

```bash
# Using Python's venv
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If a `requirements.txt` doesn't exist, install the necessary packages:

```bash
pip install python-telegram-bot requests pyyaml
```

### 4. Set Up Environment Variables

```bash
# Create .env file
cp .env.example .env  # if template exists
# or
touch .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

## Running the Bot

### Method 1: Direct Execution

```bash
python bot.py
```

### Method 2: Using a Systemd Service (Linux)

Create `/etc/systemd/system/paradex-bot.service`:

```ini
[Unit]
Description=Paradex Arbitrage Telegram Bot
After=network.target

[Service]
Type=simple
User=<your_username>
WorkingDirectory=/path/to/lighter-paradex-arbitrage
Environment="PATH=/path/to/lighter-paradex-arbitrage/venv/bin"
ExecStart=/path/to/lighter-paradex-arbitrage/venv/bin/python bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable paradex-bot
sudo systemctl start paradex-bot
```

### Method 3: Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Build and run:

```bash
docker build -t paradex-bot .
docker run -d --env-file .env --name paradex-bot paradex-bot
```

### Method 4: Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: paradex-bot
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
```

Run:

```bash
docker-compose up -d
```

## Available Commands

Once your bot is running, you can use the following commands in Telegram:

### Basic Commands

- `/start` - Start the bot and receive welcome message
- `/help` - Display list of available commands
- `/status` - Get current bot status and trading metrics
- `/balance` - Check current account balance
- `/positions` - View open trading positions

### Trading Commands

- `/trade <action> <amount>` - Execute a trading action
- `/stop_loss <price>` - Set stop loss level
- `/take_profit <price>` - Set take profit level
- `/cancel_order <order_id>` - Cancel a specific order

### Configuration Commands

- `/set_mode <mode>` - Set trading mode (manual/auto)
- `/set_threshold <value>` - Set profit threshold percentage
- `/enable_notifications` - Enable trading notifications
- `/disable_notifications` - Disable trading notifications

### Admin Commands

- `/logs` - Retrieve recent bot logs
- `/restart` - Restart the bot
- `/stats` - Get detailed trading statistics
- `/export_data` - Export trading history

## Troubleshooting

### Common Issues and Solutions

#### 1. Bot Token Invalid

**Problem**: "Invalid Telegram token"

**Solution**:
- Verify the token is correct (copy from BotFather again)
- Ensure no extra spaces or quotes in `.env` file
- Check token hasn't been reset in BotFather

#### 2. Connection Timeout

**Problem**: "Connection timeout" or "Network error"

**Solution**:
- Check internet connection
- Verify firewall isn't blocking Telegram API
- Try using a VPN if Telegram is restricted in your region
- Check Telegram API status

#### 3. Chat ID Not Found

**Problem**: "Chat ID invalid" or messages not sending

**Solution**:
- Verify Chat ID is correct (use @userinfobot)
- Ensure you've started a conversation with the bot first
- Check bot has permission to send messages

#### 4. Module Import Errors

**Problem**: "No module named 'telegram'" or similar

**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or specifically:
pip install python-telegram-bot
```

#### 5. Bot Not Responding

**Problem**: Bot doesn't respond to commands

**Solution**:
- Check bot is running: `ps aux | grep bot.py`
- Check logs for errors
- Ensure environment variables are loaded
- Restart the bot: `systemctl restart paradex-bot`

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in `.env`:

```bash
LOG_LEVEL=DEBUG
```

Check logs:

```bash
# If using systemd
sudo journalctl -u paradex-bot -f

# If using Docker
docker logs -f paradex-bot

# Check local log file
tail -f logs/bot.log
```

## Security Best Practices

### 1. Token Management

- ✅ **DO**: Store token in `.env` file
- ✅ **DO**: Add `.env` to `.gitignore`
- ❌ **DON'T**: Commit token to version control
- ❌ **DON'T**: Share token in messages or code snippets

### 2. Chat ID Security

- ✅ **DO**: Use environment variables for Chat IDs
- ✅ **DO**: Restrict bot to authorized users
- ❌ **DON'T**: Use default/public Chat IDs

### 3. API Keys

- ✅ **DO**: Use API keys with minimal required permissions
- ✅ **DO**: Rotate keys periodically
- ✅ **DO**: Use IP whitelisting if available
- ❌ **DON'T**: Use master/admin API keys

### 4. Logging and Monitoring

- ✅ **DO**: Enable audit logging
- ✅ **DO**: Monitor for suspicious activity
- ✅ **DO**: Set up alerts for errors
- ❌ **DON'T**: Log sensitive data (passwords, keys)

### 5. Network Security

- ✅ **DO**: Use HTTPS/TLS for webhooks
- ✅ **DO**: Validate webhook signatures
- ✅ **DO**: Use firewall rules to restrict access
- ❌ **DON'T**: Expose bot endpoints publicly

### 6. Access Control

```python
# Example: Restrict bot to authorized users
AUTHORIZED_USERS = [
    <YOUR_CHAT_ID>,
    # Add other trusted user IDs
]

def check_authorization(user_id):
    return user_id in AUTHORIZED_USERS
```

### 7. Regular Updates

- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Monitor security advisories for python-telegram-bot
- Update Python version regularly

## Additional Resources

- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Help](https://t.me/botfather)
- [Telegram Bot Security Tips](https://core.telegram.org/bots/faq#keeping-your-bot-token-safe)

## Support and Contributions

For issues, questions, or contributions:

1. Check the [Issues](https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage/issues) page
2. Review existing [Discussions](https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage/discussions)
3. Submit a Pull Request with improvements
4. Contact the maintainers

---

**Last Updated**: 2026-01-03

For the latest updates and changes, please refer to the main repository README and documentation.
