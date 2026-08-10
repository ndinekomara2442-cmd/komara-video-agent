"""
Komara Video Agent - MiniMax H3 Integration
Génère des vidéos IA à partir de texte ou d'images.

API: https://platform.minimax.io/docs/api-reference/video-generation-v2-create
"""

import os
import json
import requests

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_API_URL = "https://api.minimax.io/v1/video_generation"

def generate_video(prompt, model="MiniMax-H3", duration=6, resolution="1080p", aspect_ratio="9:16"):
    """
    Génère une vidéo à partir d'un prompt texte.
    
    Args:
        prompt: Description de la vidéo souhaitée
        model: Modèle à utiliser (MiniMax-H3)
        duration: Durée en secondes (4-15)
        resolution: Résolution (768p, 1080p, 2k)
        aspect_ratio: Ratio (16:9, 9:16, 1:1, 4:3, 3:4, 21:9)
    
    Returns:
        task_id pour suivre la génération
    """
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
    }
    
    response = requests.post(MINIMAX_API_URL, headers=headers, json=payload)
    return response.json()

def check_video_status(task_id):
    """Vérifie le statut d'une génération vidéo."""
    headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}"}
    response = requests.get(f"{MINIMAX_API_URL}/{task_id}", headers=headers)
    return response.json()

def generate_from_image(prompt, first_frame_image=None, last_frame_image=None, duration=6):
    """
    Génère une vidéo à partir d'images (I2VA, FL2VA, L2VA).
    
    Modes:
    - 1 image = I2VA (première frame) ou L2VA (dernière frame)
    - 2 images = FL2VA (première + dernière frame)
    """
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "MiniMax-H3",
        "prompt": prompt,
        "duration": duration,
    }
    
    if first_frame_image:
        payload["first_frame_image"] = first_frame_image
    if last_frame_image:
        payload["last_frame_image"] = last_frame_image
    
    response = requests.post(f"{MINIMAX_API_URL}", headers=headers, json=payload)
    return response.json()

# Templates de prompts optimisés pour Komara Agency
PROMPT_TEMPLATES = {
    "promo": {
        "name": "Vidéo Promo Produit",
        "template": "Professional product promotional video, {product} showcased with dynamic camera movement, studio lighting, clean background, cinematic color grading, 8k quality"
    },
    "brand": {
        "name": "Vidéo Branding",
        "template": "Brand identity reveal video, logo animation with {brand_name} colors, modern motion graphics, professional corporate style, smooth transitions"
    },
    "social": {
        "name": "Vidéo Réseaux Sociaux",
        "template": "Vertical social media content, {topic} presented with engaging visuals, text overlays, energetic pacing, trendy style for TikTok/Instagram"
    },
    "event": {
        "name": "Vidéo Événement",
        "template": "Event promotional video, {event_name} with crowd atmosphere, dynamic shots, energetic music, professional event coverage style"
    }
}

def build_prompt(template_key, **kwargs):
    """Construit un prompt optimisé à partir d'un template."""
    template = PROMPT_TEMPLATES.get(template_key, {})
    if template:
        return template["template"].format(**kwargs)
    return kwargs.get("prompt", "")

if __name__ == "__main__":
    print("Komara Video Agent - MiniMax H3")
    print("API Key required: set MINIMAX_API_KEY environment variable")
    print(f"API URL: {MINIMAX_API_URL}")
    print(f"Templates disponibles: {list(PROMPT_TEMPLATES.keys())}")
