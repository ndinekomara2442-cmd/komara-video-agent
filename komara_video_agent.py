"""
Komara Agency 🇬🇳 — Moteur de génération visuelle
Génération d'images photoréalistes via Pollinations.ai (gratuit, fiable, suit les prompts).
Hugging Face en backup pour les images.
"""

import os
import re
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

QUALITY_TAGS = (
    "photorealistic, 8K, ultra detailed, sharp focus, "
    "cinematic lighting, natural skin texture, visible pores, "
    "no plastic look, no cartoon, professional photography"
)

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

# Mots-clés par genre — utilisés avec correspondance de MOTS ENTIERS (pas de sous-chaîne)
GENRE_KEYWORDS = {
    "portrait": ["portrait", "personne", "visage", "homme", "femme", "fille", "garcon", "garçon", "face", "head", "man", "woman", "person"],
    "product": ["produit", "product", "montre", "bijoux", "bouteille", "chaussure", "sneaker", "bag", "sac", "parfum"],
    "fashion": ["mode", "fashion", "vetement", "vêtement", "tenue", "runway", "modele", "modèle", "model", "look"],
    "landscape": ["paysage", "landscape", "nature", "montagne", "mer", "ocean", "océan", "plage", "beach", "coucher", "foret", "forêt", "campagne"],
    "street": ["rue", "street", "ville", "urban", "candid", "reportage"],
    "food": ["plat", "food", "cuisine", "repas", "restaurant", "dessert", "boisson", "gastronomie"],
    "architecture": ["batiment", "bâtiment", "architecture", "immeuble", "building", "interieur", "intérieur"],
    "branding": ["logo", "brand", "marque", "affiche", "poster", "flyer", "branding", "identite", "identité"],
}

# Mots-clés visuels génériques — si aucun n'apparaît, le prompt n'est probablement pas une description d'image
VISUAL_INDICATOR_WORDS = [
    "photo", "image", "portrait", "genere", "génère", "cree", "crée", "montre", "dessine",
    "homme", "femme", "personne", "produit", "paysage", "logo", "affiche", "scene", "scène",
    "lumiere", "lumière", "fond", "style", "couleur", "studio", "eclairage", "éclairage",
    "man", "woman", "person", "product", "landscape", "scene", "light", "background",
    "vetement", "vêtement", "voiture", "animal", "ville", "nature", "batiment", "bâtiment",
    "portrait", "visage", "cheveux", "yeux", "sourire", "vue", "plan", "cadrage",
    # Sujets courants (animaux, objets, véhicules) — pour éviter de rejeter des prompts simples valides
    "chien", "chat", "dog", "cat", "cheval", "horse", "oiseau", "bird", "lion", "tigre",
    "elephant", "éléphant", "voiture", "car", "moto", "avion", "plane", "bateau", "boat",
    "fleur", "flower", "arbre", "tree", "fruit", "montagne", "mountain", "riviere", "rivière",
    "enfant", "child", "bebe", "bébé", "couple", "famille", "family", "groupe", "group",
]

# Mots grossiers / non-descriptifs à rejeter (liste non exhaustive, en minuscule)
BLOCKED_WORDS = {
    "merde", "putain", "connard", "connasse", "salope", "encule", "enculé", "batard", "bâtard",
    "shit", "fuck", "bitch", "asshole", "damn", "crap",
}

def _normalize(text):
    """Normalise le texte pour la comparaison (minuscule, sans accents complexes)."""
    return text.lower().strip()

def _contains_word(text, word):
    """Vérifie qu'un mot entier (pas une sous-chaîne) est présent dans le texte."""
    pattern = r'\b' + re.escape(word) + r'\b'
    return re.search(pattern, text, flags=re.IGNORECASE) is not None

def validate_prompt(prompt):
    """
    Valide qu'un prompt est une description d'image exploitable.
    Retourne (is_valid, reason_si_invalide).
    """
    text = _normalize(prompt)

    if len(text) < 3:
        return False, "Description trop courte."

    words = re.findall(r"[a-zàâäéèêëïîôöùûüç']+", text)

    # Prompt composé uniquement d'un mot bloqué / grossier
    if len(words) <= 2 and any(w in BLOCKED_WORDS for w in words):
        return False, "Ce n'est pas une description d'image valide."

    # Aucun mot visuel reconnu ET prompt très court (1-2 mots) → probablement pas une description
    has_visual_word = any(_contains_word(text, w) for w in VISUAL_INDICATOR_WORDS)
    has_genre_word = any(
        _contains_word(text, kw)
        for kws in GENRE_KEYWORDS.values()
        for kw in kws
    )

    if not has_visual_word and not has_genre_word and len(words) <= 3:
        return False, "Je n'ai pas compris ta demande. Décris ce que tu veux voir (sujet, ambiance, style)."

    return True, None

def detect_genre(prompt):
    """Détecte le genre visuel — compte les correspondances de MOTS ENTIERS par genre
    et retourne celui avec le plus de correspondances (pas juste le premier trouvé)."""
    text = _normalize(prompt)
    scores = {}
    for genre, keywords in GENRE_KEYWORDS.items():
        count = sum(1 for kw in keywords if _contains_word(text, kw))
        if count > 0:
            scores[genre] = count
    if not scores:
        return "portrait"  # défaut si rien de spécifique détecté
    return max(scores, key=scores.get)

def enhance_prompt(prompt):
    """
    Améliore le prompt utilisateur avec les tags de qualité Komara.
    PRÉSERVE le prompt original — ajoute seulement la qualité autour.
    """
    genre = detect_genre(prompt)
    genre_tags = GENRE_TAGS.get(genre, "")
    enhanced = f"{prompt}, {genre_tags}, {QUALITY_TAGS}"
    return enhanced

# ============================================
# GÉNÉRATION D'IMAGE — Pollinations (principal)
# ============================================

def generate_image_pollinations(prompt, width=768, height=1024):
    """Génère une image via Pollinations.ai."""
    enhanced = enhance_prompt(prompt)
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
    Valide d'abord le prompt, puis:
    1. Pollinations (rapide, fiable, suit les prompts)
    2. Hugging Face (backup)
    """
    is_valid, reason = validate_prompt(prompt)
    if not is_valid:
        return {"status": "invalid", "error": reason}

    result = generate_image_pollinations(prompt, width, height)
    if result.get("status") == "success":
        return result

    result = generate_image_hf(prompt)
    if result.get("status") == "success":
        return result

    return {"status": "error", "error": "Tous les fournisseurs ont échoué"}

# ============================================
# GÉNÉRATION MULTIPLE — Variations
# ============================================

def generate_variations(prompt, count=2):
    """Génère plusieurs variations de la même image."""
    is_valid, reason = validate_prompt(prompt)
    if not is_valid:
        return []

    results = []
    for i in range(count):
        result = generate_image_pollinations(prompt)
        if result.get("status") == "success":
            results.append(result)
        time.sleep(1)
    return results

# ============================================
# TEMPLATES
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
