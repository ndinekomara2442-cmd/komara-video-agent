# 🚀 Déploiement — Komara Agency Video Bot

## Option 1: Railway (Recommandé — Plus simple)

1. Va sur https://railway.app
2. Clique "New Project" → "Deploy from GitHub repo"
3. Sélectionne `ndinekomara2442-cmd/komara-video-agent`
4. Railway détecte automatiquement le `Procfile`
5. Va dans **Variables** → ajoute :
   - `TELEGRAM_BOT_TOKEN_2` = ton_token_telegram
   - `HUGGING_FACE_ACCESS_TOKEN` = ton_token_hf
6. Clique **Deploy**
7. Le bot démarre automatiquement ✅

## Option 2: Render (Gratuit)

1. Va sur https://render.com
2. New → "Background Worker"
3. Connect ton GitHub → sélectionne le repo
4. Render lit automatiquement `render.yaml`
5. Ajoute les variables d'environnement :
   - `TELEGRAM_BOT_TOKEN_2`
   - `HUGGING_FACE_ACCESS_TOKEN`
6. Clique "Create Worker"
7. Le bot tourne 24/7 ✅

## Option 3: Local (test rapide)

```bash
git clone https://github.com/ndinekomara2442-cmd/komara-video-agent.git
cd komara-video-agent
pip install -r agent_requirements.txt
export TELEGRAM_BOT_TOKEN_2="ton_token"
export HUGGING_FACE_ACCESS_TOKEN="ton_token_hf"
python telegram_bot.py
```

## Variables d'environnement requises

| Variable | Où la trouver |
|----------|--------------|
| `TELEGRAM_BOT_TOKEN_2` | @BotFather sur Telegram |
| `HUGGING_FACE_ACCESS_TOKEN` | https://huggingface.co/settings/tokens |

## Coût : 0€
- Hugging Face Inference API : gratuit
- Pollinations.ai : gratuit, pas de clé
- Railway : plan gratuit disponible
- Render : plan free disponible
