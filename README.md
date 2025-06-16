# Spese GPT WebApp

Webapp per gestione note spese tramite Excel + analisi GPT-4 Vision + login tradizionale e Google OAuth.

## Features
- Login email/password + Google
- Upload Excel mensile
- Upload e analisi scontrini con GPT-4 Vision
- Compilazione automatica righe
- Generazione PDF allegati

## Deploy su Render
- Aggiungi variabili da `.env.example` nella dashboard Render
- Upload automatico da GitHub
- Usa `render.yaml` per configurazione

## Avvio locale
```bash
pip install -r requirements.txt
flask --app app.py init-db
flask --app app.py run
```
