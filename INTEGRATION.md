# Intégration Komara Video Agent

## Étapes

1. Obtenir une clé API MiniMax
   - Aller sur https://platform.minimax.io
   - Créer un compte
   - Générer une API key

2. Configurer les variables d'environnement
   ```
   export MINIMAX_API_KEY="your_key"
   ```

3. Utiliser l'agent
   ```python
   from komara_video_agent import generate_video, check_video_status
   
   # Générer une vidéo
   result = generate_video("Logo animation with golden particles", duration=6)
   task_id = result["task_id"]
   
   # Vérifier le statut
   status = check_video_status(task_id)
   ```

## Intégration Telegram
Le bot Telegram @Komara_Agency_botbot peut être étendu pour:
- Recevoir un prompt texte
- Appeler l'API MiniMax H3
- Renvoyer le lien vidéo au client

## Tarifs vidéo (suggestion)
- Vidéo 6s: 500k GNF
- Vidéo 10s: 800k GNF
- Vidéo 15s: 1M GNF
- Express 24h: +30%
