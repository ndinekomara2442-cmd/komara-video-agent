"""
Komara Agency 🇬🇳 — Moteur de génération visuelle
Génération d'images photoréalistes via Pollinations.ai (gratuit, fiable, suit les prompts).
Hugging Face en backup pour les images.
"""

import os
import time
import json
import requests
import tempfile
import urllib.parse
from io import BytesIO

# ============================================
# CONFIGURATION
# ============================================

HF_TOKEN = os.environ.get("HUGGING_FACE_ACCESS_TOKEN", os.environ.get("HF_TOKEN", ""))
HF_API_URL = "https://api-inference.huggingface.co/models"

# Pollinations — gratuit, pas de clé, suit bien les prompts
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

# Modèles HF pour images (backup)
MODEL_T2I = "stabilityai/stable-diffusion-xl-base-1.0"

BRAND = "Komara Agency 🇬🇳"

# ============================================
# PROMPT ENHANCEMENT — Komara Brand Aesthetic
# ============================================

# Qualité de base injectée dans chaque prompt pour du photoréalisme
QUALITY_TAGS = (
    "photorealistic, 8K, ultra detailed, sharp focus, "
    "cinematic lighting, natural skin texture, visible pores, "
    "no plastic look, no cartoon, professional photography"
)

# Tags par genre pour cohérence
GENRE_TAGS = {
    "portrait": "studio portrait, 85mm lens, shallow depth of field, bokeh background, soft lighting on face",
    "product": "product photography, studio lighting, clean background, macro detail, sharp focus",
    "fashion": "fashion editorial, luxury aesthetic, dramatic lighting, full body shot, vogue style",
    "landscape": "landscape photography, golden hour, wide angle, deep depth of field, atmospheric",
    "street": "street photography, candid, natural light, urban environment, 35mm lens",
    "food": "food photography, overhead shot, natural lighting, appetizing, macro detail",
    "architecture": "architectural photography, clean lines, natural light, wide angle, professional",
    "branding": "luxury African brand aesthetic, black and gold palette, warm tones, premium feel",
}

def detect_genre(prompt):
    """Détecte le genre visuel basé sur les mots-clés du prompt."""
    p = prompt.lower()
    if any(w in p for w in ["portrait", "personne", "visage", "homme", "femme", "fille", "garçon", "face", "head"]):
        return "portrait"
    if any(w in p for w in ["produit", "product", "montre", "bijoux", "bouteille", "chaussure", "sneaker", "bag"]):
        return "product"
    if any(w in p for w in ["mode", "fashion", "vêtement", "tenue", "runway", "modèle", "model", "style"]):
        return "fashion"
    if any(w in p for w in ["paysage", "landscape", "nature", "montagne", "mer", "coucher soleil", "forêt"]):
        return "landscape"
    if any(w in p for w in ["rue", "street", "ville", "urban", "candid", "reportage"]):
        return "street"
    if any(w in p for w in ["plat", "food", "cuisine", "repas", "restaurant", "dessert", "boisson"]):
        return "food"
    if any(w in p for w in ["bâtiment", "architecture", "immeuble", "building", "design intérieur", "interior"]):
        return "architecture"
    if any(w in p for w in ["logo", "brand", "marque", "affiche", "poster", "flyer", "branding"]):
        return "branding"
    return "portrait"  # défaut

def enhance_prompt(prompt):
    """
    Améliore le prompt utilisateur avec les tags de qualité Komara.
    PRÉSERVE le prompt original — ajoute seulement la qualité autour.
    """
    genre = detect_genre(prompt)
    genre_tags = GENRE_TAGS.get(genre, "")

    # Le prompt utilisateur est au centre, les tags de qualité autour
    enhanced = f"{prompt}, {genre_tags}, {QUALITY_TAGS}"
    return enhanced

# ============================================
# GÉNÉRATION D'IMAGE — Pollinations (principal)
# ============================================

def generate_image_pollinations(prompt, width=768, height=1024):
    """
    Génère une image via Pollinations.ai.
    Avantages: gratuit, pas de clé, suit les prompts, rapide.
    """
    enhanced = enhance_prompt(prompt)

    # Pollinations prend le prompt encodé dans l'URL
    encoded = urllib.parse.quote(enhanced)
    url = f"{POLLINATIONS_URL}/{encoded}?width={width}&height={height}&nologo=true&seed={int(time.time()) % 1000000}"

    try:
        response = requests.get(url, timeout=60)

        if response.status_code == 200 and len(response.content) > 1000:
            output_path = os.path.join(tempfile.gettempdir(), f"komara_img_{int(time.time())}.png")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return {
                "status": "success",
                "file_path": output_path,
                "prompt": enhanced,
                "model": "pollinations-flux",
                "file_size": len(response.content),
            }
        else:
            return {"status": "error", "error": f"Pollinations HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Timeout — Pollinations"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============================================
# GÉNÉRATION D'IMAGE — Hugging Face (backup)
# ============================================

def generate_image_hf(prompt, model=MODEL_T2I):
    """Génère une image via Hugging Face Inference API (backup)."""
    if not HF_TOKEN:
        return {"status": "error", "error": "HF token non configuré"}

    enhanced = enhance_prompt(prompt)
    url = f"{HF_API_URL}/{model}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    try:
        response = requests.post(url, headers=headers, json={"inputs": enhanced}, timeout=60)

        if response.status_code == 200:
            output_path = os.path.join(tempfile.gettempdir(), f"komara_img_{int(time.time())}.png")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return {"status": "success", "file_path": output_path, "prompt": enhanced}
        elif response.status_code == 503:
            return {"status": "loading", "message": "Modèle HF en chargement. Réessayez dans 20s."}
        else:
            return {"status": "error", "error": f"HF HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============================================
# GÉNÉRATION D'IMAGE — Orchestrateur
# ============================================

def generate_image(prompt, width=768, height=1024):
    """
    Génère une image photoréaliste à partir d'un prompt.
    1. Pollinations (rapide, fiable, suit les prompts)
    2. Hugging Face (backup)
    """
    # Tentative 1: Pollinations
    result = generate_image_pollinations(prompt, width, height)
    if result.get("status") == "success":
        return result

    # Tentative 2: Hugging Face
    result = generate_image_hf(prompt)
    if result.get("status") == "success":
        return result

    # Échec
    return {"status": "error", "error": "Tous les fournisseurs ont échoué"}

# ============================================
# GÉNÉRATION MULTIPLE — Variations
# ============================================

def generate_variations(prompt, count=2):
    """Génère plusieurs variations de la même image."""
    results = []
    for i in range(count):
        result = generate_image_pollinations(prompt)
        if result.get("status") == "success":
            results.append(result)
        time.sleep(1)  # éviter le rate limit
    return results

# ============================================
# INFO POUR LE BOT
# ============================================

PROMPT_TEMPLATES = {
    "promo": {
        "name": "🎬 Promo Produit",
        "template": "Luxury product photography of {product}, studio lighting, black and gold background, premium aesthetic, 8K",
    },
    "brand": {
        "name": "🏢 Branding",
        "template": "Luxury African brand visual, black and gold palette, warm tones, premium aesthetic, {concept}, 8K photorealistic",
    },
    "social": {
        "name": "📱 Social Media",
        "template": "Cinematic social media post, {subject}, golden hour lighting, luxury African aesthetic, vertical format, 8K",
    },
    "event": {
        "name": "🎉 Événement",
        "template": "Event poster photography, {event_name}, elegant atmosphere, warm lighting, luxury African premium feel, 8K",
    },
}
