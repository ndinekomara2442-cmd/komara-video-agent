"""
Komara Agency 🇬🇳 — Bot Telegram de génération visuelle
Génère des images photoréalistes à partir de prompts texte.
Pollinations.ai (gratuit, fiable) + Hugging Face (backup).
Mode Webhook (instantané) ET Polling (fallback).
"""

import os
import json
import logging
import asyncio
import urllib.parse
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from komara_video_agent import (
    generate_image, generate_image_pollinations, generate_image_hf,
    generate_variations, enhance_prompt, detect_genre, validate_prompt,
    PROMPT_TEMPLATES,
)

# ============================================
# CONFIGURATION
# ============================================

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_2", "")
BRAND_NAME = "Komara Agency 🇬🇳"

# Contact info
WHATSAPP = "+212701986219"
EMAIL = "ndinekomara2442@gmail.com"
TELEGRAM = "@ndinekomara_Bot"
FACEBOOK = "facebook.com/ndine.komara"
TIKTOK = "tiktok.com/@ndine.komara"
SITE = "ndinekomara2442-cmd.github.io/komara-agency-site"

# Webhook config
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "komara_secret_2026")
PORT = int(os.environ.get("PORT", 8080))

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
    [["🖼️ Générer une image", "📋 Templates"],
     ["ℹ️ Aide", "📞 Contact"]],
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
        f"📸 Je génère des images photoréalistes 8K à partir de tes descriptions.\n\n"
        f"Comment m'utiliser :\n"
        f"1. Envoie ta description (prompt)\n"
        f"2. J'analyse et j'améliore ton prompt\n"
        f"3. Je génère l'image en ~10-20s\n\n"
        f"Exemple :\n"
        f"« Portrait d'un homme africain en costume noir, lumière dorée, studio pro »\n\n"
        f"💎 Gratuit — Pollinations.ai + Hugging Face",
        reply_markup=MAIN_MENU,
    )

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📸 Services {BRAND_NAME}\n\n"
        f"1️⃣ Génération d'images photoréalistes\n"
        f"   Décris une scène, je génère l'image 8K.\n\n"
        f"2️⃣ Templates prédéfinis\n"
        f"   Promo produit, branding, social, événement.\n\n"
        f"3️⃣ Variations\n"
        f"   Tape 'variations: [prompt]' pour 2 images.\n\n"
        f"💎 100% gratuit — Pollinations + Hugging Face\n"
        f"📐 Format : 9:16 (portrait), 16:9 (paysage)\n"
        f"🎨 Style : photoréaliste, luxury africain"
    )

async def templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Choisis un template :",
        reply_markup=InlineKeyboardMarkup(TEMPLATE_BUTTONS),
    )

async def template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tpl_key = query.data.replace("tpl_", "")
    tpl = PROMPT_TEMPLATES.get(tpl_key, {})
    if tpl:
        await query.edit_message_text(
            f"{tpl['name']}\n\n"
            f"Template :\n{tpl['template']}\n\n"
            f"Remplace les {{variables}} et envoie ton prompt.\n\n"
            f"Exemple : « {tpl['template'].replace('{product}', 'montre dorée').replace('{concept}', 'élégance').replace('{subject}', 'coucher de soleil à Conakry').replace('{event_name}', 'lancement produit')[:80]}... »"
        )
    else:
        await query.edit_message_text("Template introuvable.")

async def generer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Génération d'image\n\n"
        "Envoie ta description en français ou anglais.\n\n"
        "Plus tu es précis, meilleure est l'image :\n"
        "• Sujet (personne, objet, scène)\n"
        "• Éclairage (studio, golden hour, néon...)\n"
        "• Ambiance (luxury, minimaliste, cinématique...)\n"
        "• Fond (studio noir, paysage urbain...)\n\n"
        "Exemple :\n"
        "« Portrait femme africaine, robe dorée, fond noir studio, lumière cinématique »\n\n"
        "⏱️ ~10-20 secondes"
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 Contact {BRAND_NAME}\n\n"
        f"💬 WhatsApp : {WHATSAPP}\n"
        f"✈️ Telegram : {TELEGRAM}\n"
        f"📘 Facebook : {FACEBOOK}\n"
        f"🎵 TikTok : {TIKTOK}\n"
        f"📧 Email : {EMAIL}\n"
        f"🌐 Site : {SITE}\n\n"
        f"📍 Conakry, Guinée 🇬🇳"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ℹ️ Aide — {BRAND_NAME}\n\n"
        f"• /start — Démarrer\n"
        f"• /services — Services\n"
        f"• /templates — Templates\n"
        f"• /generer — Guide génération\n"
        f"• /contact — Contact\n\n"
        f"💡 Envoie simplement ta description d'image.\n"
        f"💡 'variations: [prompt]' pour 2 versions.\n"
        f"💎 Gratuit — Pollinations + HF"
    )

# ============================================
# TRAITEMENT DES MESSAGES — GÉNÉRATION
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # Boutons du menu
    if user_text == "🖼️ Générer une image":
        await generer(update, context)
        return
    elif user_text == "📋 Templates":
        await templates(update, context)
        return
    elif user_text == "ℹ️ Aide":
        await help_command(update, context)
        return
    elif user_text == "📞 Contact":
        await contact(update, context)
        return

    # Mode variations
    if user_text.lower().startswith("variations:"):
        prompt = user_text[11:].strip()
        if not prompt:
            await update.message.reply_text("❌ Ajoute un prompt après 'variations:'")
            return
        await _generate_and_send(chat_id, context, prompt, variations=True)
        return

    # Génération normale — la validation se fait dans _generate_and_send
    await _generate_and_send(chat_id, context, user_text, variations=False)

async def _generate_and_send(chat_id, context, prompt, variations=False):
    """Valide le prompt, génère et envoie l'image au chat Telegram."""

    # 1. Valider le prompt AVANT tout traitement
    is_valid, reason = validate_prompt(prompt)
    if not is_valid:
        await context.bot.send_message(
            chat_id,
            f"🤔 {reason}\n\n"
            f"Donne-moi une vraie description visuelle, par exemple :\n"
            f"« Portrait d'un homme africain, costume noir, lumière dorée, studio »\n"
            f"« Logo luxury noir et or pour une marque de mode »\n"
            f"« Paysage de Conakry au coucher du soleil, vue aérienne »"
        )
        return

    genre = detect_genre(prompt)

    await context.bot.send_message(
        chat_id,
        f"📸 Génération en cours...\n"
        f"📝 Prompt : {prompt[:150]}\n"
        f"🎨 Genre détecté : {genre}\n"
        f"⏳ ~10-20s..."
    )

    if variations:
        results = generate_variations(prompt, count=2)

        if not results:
            await context.bot.send_message(
                chat_id,
                f"❌ Échec de génération. Réessaie avec un prompt plus précis."
            )
            return

        for i, result in enumerate(results):
            if result.get("status") == "success" and result.get("file_path"):
                try:
                    with open(result["file_path"], "rb") as img_file:
                        await context.bot.send_photo(
                            chat_id,
                            photo=img_file,
                            caption=f"🖼️ Variation {i+1}/2 — {BRAND_NAME}\n📝 {prompt[:100]}"
                        )
                except Exception as e:
                    logger.error(f"Envoi variation {i+1}: {e}")
        return

    # Génération simple
    result = generate_image(prompt)

    if result.get("status") == "success" and result.get("file_path"):
        try:
            with open(result["file_path"], "rb") as img_file:
                await context.bot.send_photo(
                    chat_id,
                    photo=img_file,
                    caption=(
                        f"✅ Image générée — {BRAND_NAME}\n"
                        f"📝 {prompt[:100]}\n"
                        f"🎨 Genre : {genre}"
                    )
                )
        except Exception as e:
            await context.bot.send_message(
                chat_id,
                f"⚠️ Image générée mais erreur d'envoi : {str(e)[:200]}"
            )
    elif result.get("status") == "invalid":
        await context.bot.send_message(chat_id, f"🤔 {result.get('error')}")
    else:
        error = result.get("error", "Erreur inconnue")
        await context.bot.send_message(
            chat_id,
            f"❌ Génération échouée : {error[:200]}\n\n"
            f"💡 Essaie avec un prompt plus simple ou plus précis."
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quand l'utilisateur envoie une photo avec une description."""
    photo = update.message.photo[-1] if update.message.photo else None
    caption = update.message.caption or ""
    chat_id = update.effective_chat.id

    if not photo:
        await update.message.reply_text("❌ Aucune image reçue.")
        return

    if not caption:
        await update.message.reply_text(
            "📸 Photo reçue !\n"
            "Ajoute une description en légende pour générer une image inspirée.\n"
            "Ex: « même style mais fond noir studio »"
        )
        return

    is_valid, reason = validate_prompt(caption)
    if not is_valid:
        await context.bot.send_message(chat_id, f"🤔 {reason}")
        return

    await context.bot.send_message(
        chat_id,
        f"🎨 Génération inspirée de ta photo...\n📝 {caption[:150]}\n⏳ ~10-20s..."
    )

    result = generate_image(caption)

    if result.get("status") == "success" and result.get("file_path"):
        try:
            with open(result["file_path"], "rb") as img_file:
                await context.bot.send_photo(
                    chat_id,
                    photo=img_file,
                    caption=f"🎨 Image générée — {BRAND_NAME}\n📝 {caption[:100]}"
                )
        except Exception as e:
            await context.bot.send_message(chat_id, f"⚠️ Erreur d'envoi : {str(e)[:200]}")
    else:
        await context.bot.send_message(
            chat_id,
            f"❌ Génération échouée. Essaie une autre description."
        )

async def error_handler(update, context):
    logger.error("Exception: %s", context.error)

# ============================================
# APPLICATION SETUP
# ============================================

def build_application():
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

telegram_app: Application = None

@flask_app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": BRAND_NAME,
        "mode": "webhook" if USE_WEBHOOK else "polling",
        "bot": TELEGRAM,
    })

@flask_app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": BRAND_NAME})

@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret_header != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, telegram_app.bot)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(telegram_app.process_update(update))
    finally:
        loop.close()

    return jsonify({"status": "ok"})

@flask_app.route("/setwebhook")
def set_webhook():
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
# MAIN
# ============================================

async def setup_webhook():
    full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    await telegram_app.bot.set_webhook(
        url=full_url,
        secret_token=WEBHOOK_SECRET,
        max_connections=40,
        allowed_updates=["message", "callback_query"]
    )
    logger.info("Webhook set: %s", full_url)

def run_polling():
    app = build_application()
    print(f"🚀 {BRAND_NAME} — Bot de génération visuelle")
    print(f"🤖 {TELEGRAM}")
    print("📡 Polling (fallback)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if not BOT_TOKEN:
        print("ERREUR : TELEGRAM_BOT_TOKEN_2 non défini.")
        return

    if USE_WEBHOOK:
        print(f"🚀 {BRAND_NAME} — Bot de génération visuelle")
        print(f"📡 Webhook mode — réponses instantanées")
        print(f"🌐 URL: {WEBHOOK_URL}{WEBHOOK_PATH}")

        global telegram_app
        telegram_app = build_application()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(setup_webhook())

        flask_app.run(host="0.0.0.0", port=PORT, debug=False)
    else:
        run_polling()

if __name__ == "__main__":
    main()
