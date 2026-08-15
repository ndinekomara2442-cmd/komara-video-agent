"""
Komara Agency 🇬🇳 — Bot Telegram de génération visuelle + Assistant IA
Génère des images photoréalistes à partir de prompts texte.
Pollinations.ai (gratuit, fiable) + Hugging Face (backup).
Q&A avec base de connaissances via Gemini API.
Mode Webhook (instantané) ET Polling (fallback).
"""

import os
import sys
import json
import time
import signal
import logging
import asyncio
import urllib.parse
import requests
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
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
# BASE DE CONNAISSANCES
# ============================================

KNOWLEDGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge.json")
try:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        KNOWLEDGE = json.load(f)
    logger.info(f"knowledge.json chargé ({len(KNOWLEDGE.get('services', []))} services)")
except FileNotFoundError:
    logger.warning("knowledge.json introuvable — Q&A désactivé")
    KNOWLEDGE = None
except json.JSONDecodeError as e:
    logger.warning(f"knowledge.json invalide: {e}")
    KNOWLEDGE = None

# ============================================
# Q&A IA — Gemini avec base de connaissances
# ============================================

QA_KEYWORDS = [
    "vos services", "service", "tarif", "prix", "combien", "coût", "cout",
    "contact", "aide", "info", "information", "horaires", "délai", "delai",
    "réclamation", "question", "proposez", "offre", "disponible",
    "whatsapp", "email", "telegram", "facebook", "tiktok",
    "komara", "agence", "guinée", "guinee", "conakry",
]

def is_qa_question(text):
    text_lower = text.lower().strip()
    if text_lower.startswith("variations:"):
        return False
    for keyword in QA_KEYWORDS:
        if keyword in text_lower:
            return True
    if "?" in text:
        return True
    return False

def ask_gemini_with_knowledge(question):
    if not GEMINI_API_KEY:
        return f"Désolé, le service de Q&A n'est pas configuré. Contactez-nous via WhatsApp: {WHATSAPP}"

    knowledge_str = json.dumps(KNOWLEDGE, ensure_ascii=False) if KNOWLEDGE else "{}"

    system_prompt = (
        "Tu es Komara Agency, une agence digitale basée à Conakry, Guinée. "
        "Réponds aux questions des clients en utilisant UNIQUEMENT ces informations:\n\n"
        f"{knowledge_str}\n\n"
        "Règles:\n"
        "- Réponds de manière claire, professionnelle et concise\n"
        "- Si l'info n'est pas dans la base, dis-le honnêtement\n"
        "- Utilise des émojis légèrement pour un ton chaleureux\n"
        "- Réponds toujours en français\n"
        "- Ne dépasse pas 500 mots"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\nQuestion du client: {question}"}]}
        ],
        "generationConfig": {
            "responseModalities": ["TEXT"],
            "temperature": 0.7,
            "maxOutputTokens": 800,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        parts = data["candidates"][0]["content"]["parts"]
        text_response = ""
        for part in parts:
            if "text" in part:
                text_response += part["text"]

        return text_response.strip() or "Désolé, je n'ai pas pu générer une réponse."
    except Exception as e:
        logger.error(f"Erreur Gemini Q&A: {e}")
        return f"Erreur lors du traitement. Contactez-nous via WhatsApp: {WHATSAPP}"

# ============================================
# KEYBOARDS
# ============================================

MAIN_MENU = ReplyKeyboardMarkup(
    [["🖼️ Générer une image", "📋 Templates"],
     ["💼 Vos services", "ℹ️ Aide", "📞 Contact"]],
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
        f"📸 Je génère des images photoréalistes 8K à partir de tes descriptions.\n"
        f"💼 Je réponds aussi à tes questions sur nos services.\n\n"
        f"Comment m'utiliser :\n"
        f"1. Pour une image : envoie ta description\n"
        f"2. Pour nos services : tape « Vos services »\n"
        f"3. Pour une question : tape ta question simplement\n\n"
        f"Exemple image :\n"
        f"« Portrait d'un homme africain en costume noir, lumière dorée, studio pro »\n\n"
        f"💎 Gratuit — Pollinations.ai + Hugging Face",
        reply_markup=MAIN_MENU,
    )

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Je récupère les infos... ⏳")
    question = "Présente tous vos services avec leurs prix, descriptions et délais. Sois clair et organisé."
    try:
        loop = asyncio.get_event_loop()
        reponse = await loop.run_in_executor(None, ask_gemini_with_knowledge, question)
        if len(reponse) > 4000:
            mid = reponse[:4000].rfind('\n')
            if mid < 2000:
                mid = 4000
            await update.message.reply_text(reponse[:mid], reply_markup=MAIN_MENU)
            await update.message.reply_text(reponse[mid:], reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(reponse, reply_markup=MAIN_MENU)
    except Exception as e:
        logger.error(f"Erreur services: {e}")
        await update.message.reply_text(
            f"Erreur: {str(e)[:200]}\n\nContactez-nous: WhatsApp {WHATSAPP}",
            reply_markup=MAIN_MENU,
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
        f"• /services — Nos services\n"
        f"• /templates — Templates\n"
        f"• /generer — Guide génération\n"
        f"• /contact — Contact\n\n"
        f"💡 Envoie ta description d'image pour générer.\n"
        f"💡 'variations: [prompt]' pour 2 versions.\n"
        f"💡 Pose une question sur nos services pour obtenir une réponse IA.\n"
        f"💎 Gratuit — Pollinations + HF"
    )

# ============================================
# TRAITEMENT DES MESSAGES
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    if user_text == "🖼️ Générer une image":
        await generer(update, context)
        return
    elif user_text == "📋 Templates":
        await templates(update, context)
        return
    elif user_text == "💼 Vos services":
        await services(update, context)
        return
    elif user_text == "ℹ️ Aide":
        await help_command(update, context)
        return
    elif user_text == "📞 Contact":
        await contact(update, context)
        return

    if user_text.lower().startswith("variations:"):
        prompt = user_text[11:].strip()
        if not prompt:
            await update.message.reply_text("❌ Ajoute un prompt après 'variations:'")
            return
        await _generate_and_send(chat_id, context, prompt, variations=True)
        return

    if is_qa_question(user_text):
        await update.message.reply_text("Je regarde ça... ⏳")
        try:
            loop = asyncio.get_event_loop()
            reponse = await loop.run_in_executor(None, ask_gemini_with_knowledge, user_text)
            if len(reponse) > 4000:
                mid = reponse[:4000].rfind('\n')
                if mid < 2000:
                    mid = 4000
                await context.bot.send_message(chat_id, reponse[:mid])
                await context.bot.send_message(chat_id, reponse[mid:], reply_markup=MAIN_MENU)
            else:
                await context.bot.send_message(chat_id, reponse, reply_markup=MAIN_MENU)
        except Exception as e:
            logger.error(f"Erreur Q&A: {e}")
            await context.bot.send_message(
                chat_id,
                f"Erreur: {str(e)[:200]}\n\nContactez-nous: WhatsApp {WHATSAPP}",
                reply_markup=MAIN_MENU,
            )
        return

    await _generate_and_send(chat_id, context, user_text, variations=False)

async def _generate_and_send(chat_id, context, prompt, variations=False):
    is_valid, reason = validate_prompt(prompt)
    if not is_valid:
        await context.bot.send_message(
            chat_id,
            f"🤔 {reason}\n\n"
            f"Donne-moi une vraie description visuelle, par exemple :\n"
            f"« Portrait d'un homme africain, costume noir, lumière dorée, studio »\n"
            f"« Logo luxury noir et or pour une marque de mode »\n"
            f"« Paysage de Conakry au coucher du soleil, vue aérienne »\n\n"
            f"💡 Pour poser une question sur nos services, tape « Vos services »"
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
            await context.bot.send_message(chat_id, "❌ Échec de génération. Réessaie avec un prompt plus précis.")
            return
        for i, result in enumerate(results):
            if result.get("status") == "success" and result.get("file_path"):
                try:
                    with open(result["file_path"], "rb") as img_file:
                        await context.bot.send_photo(
                            chat_id, photo=img_file,
                            caption=f"🖼️ Variation {i+1}/2 — {BRAND_NAME}\n📝 {prompt[:100]}"
                        )
                except Exception as e:
                    logger.error(f"Envoi variation {i+1}: {e}")
        return

    result = generate_image(prompt)
    if result.get("status") == "success" and result.get("file_path"):
        try:
            with open(result["file_path"], "rb") as img_file:
                await context.bot.send_photo(
                    chat_id, photo=img_file,
                    caption=f"✅ Image générée — {BRAND_NAME}\n📝 {prompt[:100]}\n🎨 Genre : {genre}"
                )
        except Exception as e:
            await context.bot.send_message(chat_id, f"⚠️ Image générée mais erreur d'envoi : {str(e)[:200]}")
    elif result.get("status") == "invalid":
        await context.bot.send_message(chat_id, f"🤔 {result.get('error')}")
    else:
        error = result.get("error", "Erreur inconnue")
        await context.bot.send_message(
            chat_id,
            f"❌ Génération échouée : {error[:200]}\n\n💡 Essaie avec un prompt plus simple ou reformule."
        )

# ============================================
# WEBHOOK / POLLING — anti-conflit
# ============================================

flask_app = Flask(__name__)

@flask_app.route("/health")
def health():
    return jsonify({"status": "ok", "bot": BRAND_NAME})

@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 403
    update = Update.de_json(request.get_json(force=True), None)
    asyncio.run(application.process_update(update))
    return jsonify({"ok": True})

application = None

# Verrou anti-double-instance — si un fichier lock existe, on attend qu'il disparaisse
LOCK_FILE = "/tmp/komara_bot.lock"

def acquire_lock():
    """Crée un fichier lock pour éviter les doubles instances."""
    import fcntl
    global lock_fd
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        logger.info("Lock acquis — instance unique garantie")
        return True
    except (IOError, OSError):
        logger.warning("Lock déjà pris — une autre instance tourne déjà. Arrêt.")
        lock_fd.close()
        return False

def main():
    global application

    # 1. Vérifier le token
    if not BOT_TOKEN:
        sys.exit("ERREUR: TELEGRAM_BOT_TOKEN_2 manquant dans les variables d'environnement.")

    # 2. Acquérir le lock anti-double-instance
    if not acquire_lock():
        sys.exit("ERREUR: Une autre instance du bot tourne déjà. Arrêt pour éviter le conflit.")

    # 3. Nettoyer les webhooks/polling existants AVANT de démarrer
    #    Ça force Telegram à déconnecter l'ancienne session getUpdates
    logger.info("Nettoyage des sessions Telegram existantes...")
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    try:
        bot.delete_webhook(drop_pending_updates=False)
        logger.info("Webhook supprimé — ancienne session nettoyée.")
    except Exception as e:
        logger.warning(f"delete_webhook: {e}")

    # Petite pause pour laisser Telegram fermer l'ancien polling
    time.sleep(2)

    # 4. Construire l'application
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("services", services))
    application.add_handler(CommandHandler("templates", templates))
    application.add_handler(CommandHandler("generer", generer))
    application.add_handler(CommandHandler("contact", contact))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(template_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 5. Démarrer
    if USE_WEBHOOK:
        logger.info(f"Mode Webhook — URL: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
            secret_token=WEBHOOK_SECRET,
        )
    else:
        logger.info("Mode Polling — instance unique garantie par lock file")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )

if __name__ == "__main__":
    main()
