"""
Komara Agency 🇬🇳 — Video Agent (Hugging Face Edition)
Génère des vidéos IA à partir de texte — 100% gratuit via Hugging Face Inference API.

Modèles utilisés:
- Texte→Vidéo: damo-vilab/text-to-video-ms-1.7b
- Texte→Vidéo HD: cerspense/zeroscope_v2_576w
- Texte→Image: stabilityai/stable-diffusion-xl-base-1.0 (pour thumbnails)
"""

import os
import time
import json
import requests
import tempfile
from io import BytesIO

# ============================================
# CONFIGURATION
# ============================================

HF_TOKEN = os.environ.get("HUGGING_FACE_ACCESS_TOKEN", os.environ.get("HF_TOKEN", ""))
HF_API_URL = "https://api-inference.huggingface.co/models"

# Modèles gratuits
MODEL_T2V = "damo-vilab/text-to-video-ms-1.7b"
MODEL_T2V_HD = "cerspense/zeroscope_v2_576w"
MODEL_T2I = "stabilityai/stable-diffusion-xl-base-1.0"

# Brand identity
BRAND = "Komara Agency 🇬🇳"

# ============================================
# TEXTE → VIDÉO
# ============================================

def generate_video(prompt, model=None, duration=6, resolution="720p", aspect_ratio="9:16"):
    """
    Génère une vidéo à partir d'un prompt texte via Hugging Face.
    
    Args:
        prompt: Description de la vidéo
        model: Modèle HF à utiliser (défaut: damo-vilab)
        duration: Ignoré par HF (le modèle génère ~2s par défaut)
        resolution: 480p, 576p, 720p
        aspect_ratio: 9:16, 16:9, 1:1
    
    Returns:
        dict avec file_path ou error
    """
    if not HF_TOKEN:
        return {"error": "HUGGING_FACE_ACCESS_TOKEN non configuré", "status": "error"}
    
    model_name = model or MODEL_T2V
    url = f"{HF_API_URL}/{model_name}"
    
    # Enhance prompt with Komara quality tags
    enhanced_prompt = f"{prompt}, high quality, cinematic, detailed, 8k aesthetic"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "inputs": enhanced_prompt,
        "parameters": {
            "num_frames": min(duration * 8, 48),  # ~8fps
            "guidance_scale": 9.0,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            # HF retourne le fichier vidéo directement (binary)
            video_data = response.content
            output_path = os.path.join(tempfile.gettempdir(), f"komara_video_{int(time.time())}.mp4")
            
            with open(output_path, "wb") as f:
                f.write(video_data)
            
            return {
                "status": "success",
                "file_path": output_path,
                "model": model_name,
                "prompt": enhanced_prompt,
                "file_size": len(video_data),
            }
        elif response.status_code == 503:
            # Model loading
            return {
                "status": "loading",
                "message": "Le modèle est en cours de chargement. Réessayez dans 30 secondes.",
                "estimated_time": 30,
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "details": response.text[:500],
            }
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Timeout — la génération prend trop de temps"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# TEXTE → IMAGE (bonus: thumbnails)
# ============================================

def generate_image(prompt, model=MODEL_T2I):
    """
    Génère une image à partir d'un prompt (utile pour thumbnails de vidéos).
    """
    if not HF_TOKEN:
        return {"error": "HUGGING_FACE_ACCESS_TOKEN non configuré"}
    
    url = f"{HF_API_URL}/{model}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    enhanced = f"{prompt}, luxury African brand, noir and gold, cinematic, 8k, photorealistic"
    
    try:
        response = requests.post(url, headers=headers, json={"inputs": enhanced}, timeout=60)
        
        if response.status_code == 200:
            output_path = os.path.join(tempfile.gettempdir(), f"komara_img_{int(time.time())}.png")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return {"status": "success", "file_path": output_path}
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text[:300]}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# IMAGE → VIDÉO (I2VA)
# ============================================

def generate_from_image(prompt, first_frame_image=None, last_frame_image=None, duration=6):
    """
    Génère une vidéo à partir d'une image.
    Utilise le modèle Lightricks/LTX-Video ou fallback sur damo-vilab.
    """
    if not HF_TOKEN:
        return {"error": "HUGGING_FACE_ACCESS_TOKEN non configuré"}
    
    model_name = "Lightricks/LTX-Video"
    url = f"{HF_API_URL}/{model_name}"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Convert image to base64 if provided
    image_data = None
    if first_frame_image and os.path.exists(first_frame_image):
        import base64
        with open(first_frame_image, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_frames": min(duration * 8, 48),
        }
    }
    
    if image_data:
        payload["parameters"]["image"] = image_data
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            output_path = os.path.join(tempfile.gettempdir(), f"komara_i2v_{int(time.time())}.mp4")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return {"status": "success", "file_path": output_path}
        elif response.status_code == 503:
            return {"status": "loading", "message": "Modèle en chargement. Réessayez dans 30s."}
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text[:300]}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# POLLINATIONS.AI — FALLBACK 100% GRATUIT
# ============================================

def generate_image_pollinations(prompt, width=768, height=1366):
    """
    Génère une image via Pollinations.ai — gratuit, pas de clé API.
    Fallback quand Hugging Face est indisponible.
    """
    import urllib.parse
    encoded = urllib.parse.quote(f"{prompt}, high quality, cinematic, 8k")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            output_path = os.path.join(tempfile.gettempdir(), f"komara_poll_{int(time.time())}.jpg")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return {"status": "success", "file_path": output_path, "source": "pollinations"}
        return {"status": "error", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# TEMPLATES — Prompts optimisés Komara
# ============================================

PROMPT_TEMPLATES = {
    "promo": {
        "name": "Vidéo Promo Produit",
        "template": "Professional product promotional video, {product} showcased with dynamic camera movement, studio lighting, clean dark background with golden accents, cinematic color grading, luxury African brand aesthetic, 8k quality"
    },
    "brand": {
        "name": "Vidéo Branding",
        "template": "Brand identity reveal video, {brand_name} logo animation with black and gold colors, modern motion graphics, luxury African corporate style, smooth cinematic transitions"
    },
    "social": {
        "name": "Vidéo Réseaux Sociaux",
        "template": "Vertical social media content, {topic} presented with engaging visuals, dynamic text overlays, energetic pacing, trendy style, golden hour lighting, premium quality"
    },
    "event": {
        "name": "Vidéo Événement",
        "template": "Event promotional video, {event_name} with crowd atmosphere, dynamic camera shots, African cultural elements, energetic mood, professional event coverage, cinematic"
    }
}


def build_prompt(template_key, **kwargs):
    """Construit un prompt optimisé à partir d'un template."""
    template = PROMPT_TEMPLATES.get(template_key, {})
    if template:
        return template["template"].format(**kwargs)
    return kwargs.get("prompt", "")


def check_video_status(task_id):
    """
    Avec Hugging Face, la génération est synchrone (pas de task_id).
    Cette fonction est gardée pour compatibilité avec le bot Telegram.
    """
    return {
        "status": "completed",
        "message": "Hugging Face génère en direct — pas de task_id nécessaire.",
        "task_id": task_id,
    }


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print(f"🎬 {BRAND} — Video Agent (Hugging Face Edition)")
    print(f"🔑 HF Token: {'✅ Configuré' if HF_TOKEN else '❌ Manquant'}")
    print(f"🤖 Modèle T2V: {MODEL_T2V}")
    print(f"🤖 Modèle T2V HD: {MODEL_T2V_HD}")
    print(f"🖼️ Modèle Image: {MODEL_T2I}")
    print(f"📋 Templates: {list(PROMPT_TEMPLATES.keys())}")
    print(f"\nVariables d'environnement:")
    print(f"  HUGGING_FACE_ACCESS_TOKEN ou HF_TOKEN")
