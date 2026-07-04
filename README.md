# 🛡️ APK Protector Bot

Telegram bot that protects Android APK files using multiple layers of obfuscation and security.

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 String Encryption | Smali-level XOR + Base64 string fog |
| 🛡️ Anti-Tamper | Signature & package name verification, crash on modify |
| 🔩 Libs Protection | ELF .so symbol stripping, build-id randomization |
| 🎨 Resource Obfuscation | Drawable/layout name randomization |
| ✍️ Auto Sign | Automatic APK zipalign + signing |

## 🏗️ Architecture

```
Telegram User
     ↓
Node.js Bot (Grammy)
     ↓ HTTP POST /protect
Python FastAPI Engine
     ↓
APK Pipeline:
  apktool (decompile)
  → string_encryptor.py
  → anti_tamper.py
  → libs_protector.py
  → resource_obfuscator.py
  → apktool (recompile)
  → uber-apk-signer
     ↓
Protected APK → User
```

## 🚀 Local Setup

### Requirements
- Node.js 18+
- Python 3.10+
- Java 17+
- apktool
- zipalign

### 1. Clone & Setup

```bash
git clone <your-repo>
cd apk-protector-bot

# Copy env file
cp .env.example .env
# Edit .env with your BOT_TOKEN
```

### 2. Start Python Engine

```bash
cd engine
pip install -r requirements.txt

# Download apktool
mkdir -p /tools
wget https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /tools/apktool.jar
wget https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar -O /tools/uber-apk-signer.jar

python main.py
```

### 3. Start Node.js Bot

```bash
cd bot
npm install
node index.js
```

## ☁️ Render Deployment

1. GitHub এ push করো
2. Render.com → New → Blueprint
3. `render.yaml` select করো
4. Environment variables set করো:
   - `BOT_TOKEN` = Telegram bot token

### Render এ BOT_TOKEN set করা:
```
Render Dashboard → apk-protector-bot service → Environment → Add BOT_TOKEN
```

## 📁 Project Structure

```
apk-protector-bot/
├── bot/
│   ├── index.js          # Telegram bot (Grammy)
│   └── package.json
├── engine/
│   ├── main.py           # FastAPI server
│   ├── processor/
│   │   ├── decompiler.py       # apktool wrapper
│   │   ├── string_encryptor.py # XOR string fog
│   │   ├── anti_tamper.py      # Tamper detection
│   │   ├── libs_protector.py   # .so ELF protection
│   │   ├── resource_obfuscator.py
│   │   └── signer.py           # APK signing
│   ├── requirements.txt
│   └── Dockerfile
├── render.yaml
└── .env.example
```

## ⚠️ Notes

- Max APK size: 50MB (Telegram limit)
- Processing time: 1-3 minutes depending on APK size
- Render free tier sleeps after inactivity — paid tier recommended for 24/7
- Only use on APKs you own or have rights to protect
