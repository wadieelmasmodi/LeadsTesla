# Tesla Partner Portal Lead Scraper

## Description
Script Python automatisé pour récupérer les leads depuis le portail partenaire Tesla. Le script se connecte au portail, extrait les informations des leads des deux tableaux (tesla.com et shop.tesla.com), et envoie les nouveaux leads vers un webhook n8n.

## Fonctionnalités

- 🔐 Authentification automatique avec support MFA (TOTP)
- 📊 Extraction des leads depuis les deux tableaux du portail
- 🔄 Déduplication des leads via système d'état persistant
- 📝 Logging complet des opérations
- 🚀 Envoi des nouveaux leads vers webhook n8n
- 🐳 Prêt pour déploiement Docker/Coolify

## Prérequis

- Python 3.11+
- Playwright
- Docker (pour déploiement)

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/wadieelmasmodi/LeadsTesla.git
cd LeadsTesla
```

2. Installer les dépendances :
```bash
pip install -r app/requirements.txt
playwright install
```

3. Configurer l'environnement :
```bash
cp app/.env.example app/.env
```
Éditer `app/.env` avec vos informations :
- TESLA_EMAIL : Email de connexion Tesla
- TESLA_PASS : Mot de passe Tesla
- TOTP_SECRET : Secret TOTP pour MFA
- N8N_WEBHOOK_URL : URL du webhook n8n

## Utilisation

### En local

```bash
cd app
python main.py
```

### Avec Docker

```bash
docker build -t tesla-leads-scraper .
docker run -v $(pwd)/data:/data --env-file app/.env tesla-leads-scraper
```

### Avec Coolify

1. Créer un nouveau service dans Coolify
2. Utiliser le Dockerfile fourni
3. Configurer les variables d'environnement selon `.env.example`
4. Déployer

## Structure du Projet

```
/app
├─ main.py                     # Point d'entrée
├─ config.py                   # Configuration
├─ logger.py                   # Logging
├─ auth.py                     # Authentification
├─ scraper.py                 # Extraction des données
├─ state.py                   # Gestion de l'état
├─ notifier.py               # Envoi webhook
├─ readme.py                 # Génération documentation
├─ utils_text.py            # Utilitaires texte
├─ requirements.txt         # Dépendances
├─ Dockerfile              # Configuration Docker
└─ .env.example           # Template configuration
```

## Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| PORTAL_URL | URL du portail | https://partners.tesla.com/home/fr-fr/leads |
| TESLA_EMAIL | Email de connexion | - |
| TESLA_PASS | Mot de passe | - |
| TOTP_SECRET | Secret TOTP (Base32) | - |
| N8N_WEBHOOK_URL | URL webhook n8n | - |
| STATE_FILE | Fichier d'état | /data/state.json |
| LOG_FILE | Fichier de log | /data/leads.log |
| README_FILE | Documentation webhook | /data/README_webhook.md |

## Format des Données

Voir le fichier `/data/README_webhook.md` généré après le premier run pour la documentation complète du format JSON envoyé au webhook.

## Sécurité

- Les secrets sont gérés uniquement via variables d'environnement
- Support MFA pour l'authentification Tesla
- Pas de stockage des credentials en clair
- Exécution headless sécurisée

## Contributions

Les contributions sont bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## Licence

MIT