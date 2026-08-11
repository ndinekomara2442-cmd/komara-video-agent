"""
Komara Agency 🇬🇳 — Telegram Bot pour l'Agent Vidéo IA
Utilise Hugging Face Inference API (100% gratuit) + Pollinations.ai fallback.
Supporte Webhook (rapide) ET Polling (fallback).
"""

import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from komara_video_agent import (
    generate_video, generate_image, generate_from_image,
    generate_image_pollinations, build_prompt, PROMPT_TEMPLATES,
)

# ============================================
# CONFIGURATION
# ============================================

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_2", "")
BRAND_NAME = "Komara Agency 🇬🇳"

# Webhook config
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # e.g. https://komara-ai-agent.up.railway.app
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "komara_secret_2026")
PORT = int(os.environ.get("PORT", 8080))

# Mode: webhook if WEBHOOK_URL is set, otherwise polling
USE_WEBHOOK = bool(WEBHOOK_URL)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================
# KEYBOARDS
# ============================================

MAIN_MENU = ReplyKeyboardMarkup(
    [["🎬 Générer vidéo", "🖼️ Générer image"],
     ["📋 Templates", "ℹ️ Aide"]],
    resize_keyboard=True,
)

TEMPLATE_BUTTONS = [
    [InlineKeyboardButton("🎬 Promo Produit", callback_data="tpl_promo"),
     InlineKeyboardButton("🏢 Branding", callback_data="tpl_brand")],
    [InlineKeyboardButton("📱 Social", callback_data="tpl_social"),
     InlineKeyboardButton("🎉 Événement", callback_data="tpl_event")],
]

# ============================================
# HANDLERS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Bienvenue chez {BRAND_NAME} !\n\n"
        f"🎬 Agent Vidéo IA — Gratuit via Hugging Face\n\n"
        f"Je génère des vidéos et images IA à partir de texte.\n\n"
        f"Commandes :\n"
        f"• /start — Bienvenue\n"
        f"• /services — Nos services\n"
        f"• /templates — Templates\n"
        f"• /generer — Guide génération\n"
        f"• /contact — Contact\n\n"
        f"Envoyez votre prompt pour commencer !",
        reply_markup=MAIN_MENU,
    )

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎬 Services {BRAND_NAME}\n\n"
        f"1️⃣ Texte → Vidéo (T2V)\n"
        f"   Décrivez une scène, je génère la vidéo.\n\n"
        f"2️⃣ Texte → Image (T2I)\n"
        f"   Générez des images premium pour vos réseaux.\n\n"
        f"3️⃣ Image → Vidéo (I2V)\n"
        f"   Envoyez une image, je l'anime.\n\n"
        f"4️⃣ Templates prédéfinis\n"
        f"   Promo, branding, social, event.\n\n"
        f"💎 100% gratuit — Hugging Face + Pollinations\n"
        f"📐 Formats : 9:16, 16:9, 1:1\n"
        f"⏱️ Durée vidéo : ~2-6 secondes",
        reply_markup=MAIN_MENU,
    )

async def templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Templates — choisissez un template :",
        reply_markup=InlineKeyboardMarkup(TEMPLATE_BUTTONS),
    )

async def template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tpl_key = query.data.replace("tpl_", "")
    tpl = PROMPT_TEMPLATES.get(tpl_key, {})
    if tpl:
        await query.edit_message_text(
            f"🎬 Template : {tpl['name']}\n\n"
            f"Modèle : {tpl['template']}\n\n"
            f"Envoyez votre prompt avec le préfixe /{tpl_key}\n\n"
            f"Exemple : /{tpl_key} product=\"montre de luxe dorée\""
        )
    else:
        await query.edit_message_text("Template introuvable.")

async def generer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Génération de vidéo\n\n"
        "Envoyez la description de la vidéo.\n\n"
        "Exemple :\n"
        '"Drone shot over Conakry at sunset, golden hour, cinematic, 8k"\n\n'
        "Le bot génère la vidéo et vous l'envoie directement.\n"
        "⏱️ La génération prend ~30-60 secondes."
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 Contact {BRAND_NAME}\n\n"
        f"📍 Conakry, Guinée 🇬🇳\n"
        f"🌐 GitHub : github.com/ndinekomara2442-cmd\n"
        f"🤖 Telegram : @ndinekomara_Bot"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ℹ️ Aide — {BRAND_NAME}\n\n"
        f"• /start — Démarrer\n"
        f"• /services — Services\n"
        f"• /templates — Templates\n"
        f"• /generer — Guide génération\n"
        f"• /contact — Contact\n\n"
        f"💎 Gratuit via Hugging Face\n"
        f"Envoyez un prompt texte pour générer une vidéo !"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    if user_text == "🎬 Générer vidéo":
        await generer(update, context)
        return
    elif user_text == "🖼️ Générer image":
        await update.message.reply_text(
            "🖼️ Génération d'image\n\n"
            "Envoyez votre prompt pour générer une image premium.\n\n"
            "Exemple :\n"
            '"Luxury African brand portrait, golden hour, cinematic lighting, 8k"'
        )
        return
    elif user_text == "📋 Templates":
        await templates(update, context)
        return
    elif user_text == "ℹ️ Aide":
        await help_command(update, context)
        return

    await context.bot.send_message(chat_id, f"🎬 Génération en cours...\n📝 Prompt : {user_text[:200]}\n⏳ Patientez ~30-60s...")

    result = generate_video(prompt=user_text)

    if result.get("status") == "success" and result.get("file_path"):
        try:
            with open(result["file_path"], "rb") as video_file:
                await context.bot.send_video(chat_id, video=video_file, caption=f"🎬 Vidéo générée par {BRAND_NAME}\n📝 {user_text[:100]}")
        except Exception as e:
            await context.bot.send_message(chat_id, f"⚠️ Vidéo générée mais erreur d'envoi : {str(e)[:200]}\n📁 Fichier : {result['file_path']}")
    elif result.get("status") == "loading":
        await context.bot.send_message(chat_id, f"⏳ {result.get('message', 'Modèle en chargement. Réessayez dans 30s.')}")
    else:
        await context.bot.send_message(chat_id, "⚠️ Vidéo indisponible. Génération d'image en fallback...")
        img_result = generate_image(prompt=user_text)
        if img_result.get("status") == "success" and img_result.get("file_path"):
            try:
                with open(img_result["file_path"], "rb") as img_file:
                    await context.bot.send_photo(chat_id, photo=img_file, caption=f"🖼️ Image générée par {BRAND_NAME}\n📝 {user_text[:100]}")
            except Exception:
                poll_result = generate_image_pollinations(prompt=user_text)
                if poll_result.get("status") == "success" and poll_result.get("file_path"):
                    with open(poll_result["file_path"], "rb") as img_file:
                        await context.bot.send_photo(chat_id, photo=img_file, caption=f"🖼️ Image (Pollinations) — {BRAND_NAME}")
                else:
                    await context.bot.send_message(chat_id, f"❌ Erreur : {img_result.get('error', 'Inconnue')}")
        else:
            poll_result = generate_image_pollinations(prompt=user_text)
            if poll_result.get("status") == "success":
                with open(poll_result["file_path"], "rb") as img_file:
                    await context.bot.send_photo(chat_id, photo=img_file, caption=f"🖼️ {BRAND_NAME} — Pollinations")
            else:
                await context.bot.send_message(chat_id, f"❌ Erreur : {result.get('error', 'Génération échouée')}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1] if update.message.photo else None
    caption = update.message.caption or "Animate this image with cinematic movement"
    chat_id = update.effective_chat.id

    if not photo:
        await update.message.reply_text("❌ Aucune image reçue.")
        return

    await context.bot.send_message(chat_id, f"🎬 Image → Vidéo (I2V)\n📝 {caption[:200]}\n⏳ Génération...")

    try:
        file = await context.bot.get_file(photo.file_id)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            image_path = tmp.name

        result = generate_from_image(prompt=caption, first_frame_image=image_path)

        if result.get("status") == "success" and result.get("file_path"):
            with open(result["file_path"], "rb") as video_file:
                await context.bot.send_video(chat_id, video=video_file, caption=f"🎬 I2V par {BRAND_NAME}")
        else:
            await context.bot.send_message(chat_id, f"❌ I2V indisponible : {result.get('error', 'Inconnue')}\n💡 Essayez T2V (texte → vidéo) à la place.")

        os.unlink(image_path)
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Erreur : {str(e)[:200]}")

async def error_handler(update, context):
    logger.error("Exception: %s", context.error)

# ============================================
# APPLICATION SETUP
# ============================================

def build_application():
    """Build and configure the Telegram Application with all handlers."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("services", services))
    application.add_handler(CommandHandler("templates", templates))
    application.add_handler(CommandHandler("generer", generer))
    application.add_handler(CommandHandler("contact", contact))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(template_callback, pattern="^tpl_"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    return application

# ============================================
# FLASK WEBHOOK MODE
# ============================================

flask_app = Flask(__name__)
flask_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Global application instance for webhook
telegram_app: Application = None

@flask_app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": BRAND_NAME,
        "mode": "webhook" if USE_WEBHOOK else "polling",
        "bot": "@ndinekomara_Bot"
    })

@flask_app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": BRAND_NAME})

@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    """Receive updates from Telegram via webhook."""
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret_header != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, telegram_app.bot)
    
    # Process update asynchronously
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(telegram_app.process_update(update))
    finally:
        loop.close()

    return jsonify({"status": "ok"})

@flask_app.route("/setwebhook")
def set_webhook():
    """Set the Telegram webhook. Call this URL once after deploy."""
    import urllib.request
    full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = json.dumps({
        "url": full_url,
        "secret_token": WEBHOOK_SECRET,
        "max_connections": 40,
        "allowed_updates": ["message", "callback_query"]
    }).encode()
    req = urllib.request.Request(api_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
        return jsonify({"result": result, "webhook_url": full_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route("/delwebhook")
def del_webhook():
    """Remove the Telegram webhook (switch back to polling)."""
    import urllib.request
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    req = urllib.request.Request(api_url, data=b'{}', headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# MAIN — WEBHOOK OR POLLING
# ============================================

async def setup_webhook():
    """Set the webhook on Telegram."""
    full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    await telegram_app.bot.set_webhook(
        url=full_url,
        secret_token=WEBHOOK_SECRET,
        max_connections=40,
        allowed_updates=["message", "callback_query"]
    )
    logger.info("✅ Webhook set: %s", full_url)

async def run_webhook():
    """Run the Flask app with webhook mode."""
    global telegram_app
    telegram_app = build_application()
    await telegram_app.initialize()
    await setup_webhook()
    
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)

def run_polling():
    """Fallback: run with polling."""
    app = build_application()
    print(f"🚀 {BRAND_NAME} — Bot Vidéo IA (Hugging Face Edition)")
    print(f"🤖 @ndinekomara_Bot")
    print(f"💎 100% gratuit — HF + Pollinations")
    print("📡 Polling (fallback)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if not BOT_TOKEN:
        print("ERREUR : TELEGRAM_BOT_TOKEN_2 non défini.")
        return

    if USE_WEBHOOK:
        print(f"🚀 {BRAND_NAME} — Bot Vidéo IA")
        print(f"📡 Webhook mode — réponses instantanées")
        print(f"🌐 URL: {WEBHOOK_URL}{WEBHOOK_PATH}")
        
        global telegram_app
        telegram_app = build_application()
        
        # Initialize and set webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(setup_webhook())
        
        # Start Flask
        flask_app.run(host="0.0.0.0", port=PORT, debug=False)
    else:
        run_polling()

if __name__ == "__main__":
    main()
