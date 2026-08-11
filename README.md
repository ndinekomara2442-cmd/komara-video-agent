# Komara Agency 🇬🇳 — Video Agent IA

Agent de génération vidéo et image IA pour Telegram.
100% gratuit — propulsé par Hugging Face + Pollinations.ai

## Fonctionnalités

1. Texte → Vidéo (T2V)
2. Texte → Image (T2I)
3. Image → Vidéo (I2V)
4. Templates prédéfinis (promo, branding, social, event)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Voir `.env.example` pour les variables d'environnement requises.

## Démarrage

```bash
python telegram_bot.py
```

## Mode Webhook (recommandé)

Pour des réponses instantanées, définissez `WEBHOOK_URL` avec votre domaine public.
Le mode polling est utilisé automatiquement si `WEBHOOK_URL` n'est pas défini.

## Technologies

- Hugging Face Inference API (gratuit)
- Pollinations.ai (fallback gratuit)
- Telegram Bot API
- Flask (serveur webhook)

---

© 2026 Komara Agency 🇬🇳 — Luxury African Digital Solutions
