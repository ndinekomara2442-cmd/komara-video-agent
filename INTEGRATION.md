# Komara Agency 🇬🇳 — Intégration Hugging Face

## Configuration

1. Obtenir un token Hugging Face (gratuit)
   - Aller sur https://huggingface.co/settings/tokens
   - Créer un token (Read permissions)

2. Définir les variables d'environnement :
   ```bash
   export TELEGRAM_BOT_TOKEN_2="your_bot_token"
   export HUGGING_FACE_ACCESS_TOKEN="your_hf_token"
   export WEBHOOK_URL="https://your-app.up.railway.app"
   ```

3. Lancer le bot :
   ```bash
   python telegram_bot.py
   ```

## API utilisées

- Hugging Face Inference API (gratuit) — génération vidéo/image
- Pollinations.ai (fallback gratuit) — génération image
- Telegram Bot API — messagerie

## Aucune clé payante requise
