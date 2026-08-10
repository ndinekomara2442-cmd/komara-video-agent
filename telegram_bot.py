"""
Komara Agency 🇬🇳 — Telegram Bot pour l'Agent Vidéo IA
Bot Telegram connecté au moteur de génération vidéo MiniMax H3.
"""

import os
import json
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from komara_video_agent import (
    generate_video,
    check_video_status,
    generate_from_image,
    build_prompt,
    PROMPT_TEMPLATES,
)

# ============================================
# CONFIGURATION
# ============================================

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_2", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BRAND_NAME = "Komara Agency 🇬🇳"
BRAND_TAGLINE = "Agent Vidéo IA — Génération & Retouche"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================
# KEYBOARDS
# ============================================

MAIN_MENU = ReplyKeyboardMarkup(
    [["🎬 Générer une vidéo", "📋 Templates"],
     ["📊 Mes tâches", "ℹ️ Aide"]],
    resize_keyboard=True,
)

TEMPLATE_BUTTONS = [
    [InlineKeyboardButton("🎬 Promo Produit", callback_data="tpl_promo")],
    [InlineKeyboardButton("🏢 Branding", callback_data="tpl_brand")],
    [InlineKeyboardButton("📱 Réseaux Sociaux", callback_data="tpl_social")],
    [InlineKeyboardButton("🎉 Événement", callback_data="tpl_event")],
]

# ============================================
# HANDLERS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        f"👋 Bienvenue chez {BRAND_NAME} !\n\n"
        f"🎬 {BRAND_TAGLINE}\n\n"
        f"Je génère des vidéos IA à partir de texte ou d'images.\n\n"
        f"Commandes :\n"
        f"• /start — Bienvenue\n"
        f"• /services — Nos services\n"
        f"• /templates — Templates de prompts\n"
        f"• /generer — Générer une vidéo\n"
        f"• /status <id> — Statut d'une tâche\n"
        f"• /contact — Nous contacter\n\n"
        f"Envoyez votre prompt pour générer une vidéo !"
    )
    await update.message.reply_text(welcome, reply_markup=MAIN_MENU)


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🎬 Services {BRAND_NAME}\n\n"
        f"1️⃣ Texte → Vidéo (T2VA)\n"
        f"   Décrivez une scène, je génère la vidéo.\n\n"
        f"2️⃣ Image → Vidéo (I2VA)\n"
        f"   Envoyez une image + un prompt.\n\n"
        f"3️⃣ Image+Image → Vidéo (FL2VA)\n"
        f"   Première et dernière frame.\n\n"
        f"4️⃣ Templates prédéfinis\n"
        f"   Promo, branding, social, event.\n\n"
        f"📐 Formats : 9:16, 16:9, 1:1, 4:3\n"
        f"🎥 Résolution : 768p, 1080p, 2K\n"
        f"⏱️ Durée : 4 à 15 secondes"
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)


async def templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = InlineKeyboardMarkup(TEMPLATE_BUTTONS)
    await update.message.reply_text(
        "📋 Templates disponibles — choisissez un template :", reply_markup=reply_markup
    )


async def template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tpl_key = query.data.replace("tpl_", "")
    tpl = PROMPT_TEMPLATES.get(tpl_key, {})
    if tpl:
        text = (
            f"🎬 Template : {tpl['name']}\n\n"
            f"Modèle : {tpl['template']}\n\n"
            f"Utilisez /{tpl_key} product=\"votre produit\""
        )
    else:
        text = "Template introuvable."
    await query.edit_message_text(text)


async def generer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎬 Génération de vidéo\n\n"
        "Envoyez la description de la vidéo souhaitée.\n\n"
        "Exemple :\n"
        '"Plan cinématique d\'une ville africaine au coucher du soleil, '
        'drone shot, golden hour, 8k"\n\n'
        "Options :\n"
        "• durée=10 (4-15 sec)\n"
        "• res=2k (768p, 1080p, 2k)\n"
        "• ratio=16:9 (9:16, 16:9, 1:1, 4:3)"
    )
    await update.message.reply_text(text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation : /status <task_id>")
        return
    task_id = context.args[0]
    try:
        result = check_video_status(task_id)
        status = result.get("status", "unknown")
        await update.message.reply_text(
            f"📊 Tâche {task_id}\n\nStatut : {status}\n"
            f"Réponse : {json.dumps(result, indent=2, ensure_ascii=False)[:500]}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📞 Contact {BRAND_NAME}\n\n"
        f"📍 Conakry, Guinée 🇬🇳\n"
        f"💬 WhatsApp : +224 XXX XXX XXX\n"
        f"🌐 GitHub : github.com/ndinekomara2442-cmd"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"ℹ️ Aide — {BRAND_NAME}\n\n"
        f"• /start — Démarrer\n"
        f"• /services — Nos services\n"
        f"• /templates — Templates\n"
        f"• /generer — Générer une vidéo\n"
        f"• /status <id> — Statut d'une tâche\n"
        f"• /contact — Nous contacter\n\n"
        f"Ou envoyez votre prompt directement !"
    )
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if user_text == "🎬 Générer une vidéo":
        await generer(update, context)
        return
    elif user_text == "📋 Templates":
        await templates(update, context)
        return
    elif user_text == "📊 Mes tâches":
        await update.message.reply_text("Utilisez : /status <task_id>")
        return
    elif user_text == "ℹ️ Aide":
        await help_command(update, context)
        return

    duration = 6
    resolution = "1080p"
    aspect_ratio = "9:16"

    lines = user_text.split("\n")
    prompt_lines = []
    for line in lines:
        if line.strip().startswith("durée="):
            try:
                duration = max(4, min(15, int(line.split("=")[1].strip())))
            except ValueError:
                pass
        elif line.strip().startswith("res="):
            resolution = line.split("=")[1].strip()
        elif line.strip().startswith("ratio="):
            aspect_ratio = line.split("=")[1].strip()
        else:
            prompt_lines.append(line)

    prompt = "\n".join(prompt_lines).strip()
    if not prompt:
        await update.message.reply_text("❌ Aucun prompt détecté.")
        return

    if not MINIMAX_API_KEY:
        await update.message.reply_text(
            f"⚠️ MINIMAX_API_KEY non configurée.\n\n"
            f"Prompt : \"{prompt[:100]}...\"\n\n"
            f"Configurez la clé API MiniMax pour activer la génération."
        )
        return

    await update.message.reply_text(
        f"🎬 Génération en cours...\n\n"
        f"📝 Prompt : {prompt[:200]}\n"
        f"⏱️ Durée : {duration}s\n"
        f"🎥 Résolution : {resolution}\n"
        f"📐 Format : {aspect_ratio}\n\n"
        f"⏳ Patientez..."
    )

    try:
        result = generate_video(
            prompt=prompt, duration=duration, resolution=resolution, aspect_ratio=aspect_ratio
        )
        task_id = result.get("task_id", "")
        status = result.get("status", "pending")
        if task_id:
            await update.message.reply_text(
                f"✅ Tâche créée !\n\n📋 Task ID : {task_id}\n📊 Statut : {status}\n\n"
                f"Vérifiez : /status {task_id}"
            )
        else:
            await update.message.reply_text(
                f"Réponse API :\n{json.dumps(result, indent=2, ensure_ascii=False)[:500]}"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1] if update.message.photo else None
    caption = update.message.caption or "Animate this image with cinematic movement"
    if not photo:
        await update.message.reply_text("❌ Aucune image reçue.")
        return
    if not MINIMAX_API_KEY:
        await update.message.reply_text("⚠️ MINIMAX_API_KEY non configurée.")
        return

    await update.message.reply_text(
        f"🎬 Image → Vidéo (I2VA)\n📝 Prompt : {caption[:200]}\n⏳ Génération..."
    )
    try:
        file = await context.bot.get_file(photo.file_id)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            image_path = tmp.name
        result = generate_from_image(prompt=caption, first_frame_image=image_path, duration=6)
        task_id = result.get("task_id", "")
        if task_id:
            await update.message.reply_text(f"✅ I2VA Tâche créée !\n📋 Task ID : {task_id}")
        else:
            await update.message.reply_text(
                f"Réponse API :\n{json.dumps(result, indent=2, ensure_ascii=False)[:500]}"
            )
        os.unlink(image_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur I2VA : {str(e)}")


async def error_handler(update, context):
    logger.error("Exception: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("❌ Une erreur est survenue. Réessayez.")


# ============================================
# MAIN
# ============================================

def main():
    if not BOT_TOKEN:
        print("ERREUR : TELEGRAM_BOT_TOKEN_2 non défini.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("templates", templates))
    app.add_handler(CommandHandler("generer", generer))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(template_callback, pattern="^tpl_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print(f"🚀 {BRAND_NAME} — Bot Vidéo IA démarré")
    print(f"🎥 MiniMax API : {'✅' if MINIMAX_API_KEY else '❌ Non configuré'}")
    print("📡 Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
