"""
Komara Agency 🇬🇳 — Telegram Bot pour l'Agent Vidéo IA
Utilise Hugging Face Inference API (100% gratuit) + Pollinations.ai fallback.
"""

import os
import json
import logging
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

    # Menu buttons
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

    # Génération vidéo
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
        # Fallback: générer une image au lieu d'une vidéo
        await context.bot.send_message(chat_id, "⚠️ Vidéo indisponible. Génération d'image en fallback...")
        img_result = generate_image(prompt=user_text)
        if img_result.get("status") == "success" and img_result.get("file_path"):
            try:
                with open(img_result["file_path"], "rb") as img_file:
                    await context.bot.send_photo(chat_id, photo=img_file, caption=f"🖼️ Image générée par {BRAND_NAME}\n📝 {user_text[:100]}")
            except Exception:
                # Pollinations fallback
                poll_result = generate_image_pollinations(prompt=user_text)
                if poll_result.get("status") == "success" and poll_result.get("file_path"):
                    with open(poll_result["file_path"], "rb") as img_file:
                        await context.bot.send_photo(chat_id, photo=img_file, caption=f"🖼️ Image (Pollinations) — {BRAND_NAME}")
                else:
                    await context.bot.send_message(chat_id, f"❌ Erreur : {img_result.get('error', 'Inconnue')}")
        else:
            # Pollinations last resort
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
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(template_callback, pattern="^tpl_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print(f"🚀 {BRAND_NAME} — Bot Vidéo IA (Hugging Face Edition)")
    print(f"🤖 @ndinekomara_Bot")
    print(f"💎 100% gratuit — HF + Pollinations")
    print("📡 Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
