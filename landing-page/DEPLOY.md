# Guide de Déploiement - Landing Page Solaire

## 📦 Prérequis

Avant de déployer, assurez-vous d'avoir :
- Un compte GitHub
- Accès à Coolify
- Le repository configuré

## 🚀 Déploiement sur Coolify

### Étape 1 : Pousser sur GitHub

```bash
# Si ce n'est pas déjà fait, configurer le repository distant
cd "c:\Users\wadie\GitHub Repo\Leads Tesla"
git remote add origin https://github.com/wadieelmasmodi/LeadsTesla.git

# Pousser la branche
git push -u origin landing-page-solaire
```

### Étape 2 : Configuration dans Coolify

1. **Connectez-vous à Coolify** : [https://coolify.energum.earth](https://coolify.energum.earth)

2. **Créer une nouvelle ressource** :
   - Cliquez sur "New Resource"
   - Sélectionnez "GitHub App"

3. **Configuration du repository** :
   - Repository: `wadieelmasmodi/LeadsTesla`
   - Branch: `landing-page-solaire`
   - Build Pack: `Dockerfile`
   - Dockerfile Path: `./landing-page/Dockerfile`
   - Working Directory: `./landing-page`

4. **Configuration du port** :
   - Port: `3000`
   - Health Check Path: `/`

5. **Variables d'environnement** :
   ```
   NODE_ENV=production
   NEXT_TELEMETRY_DISABLED=1
   ```

6. **Domaine** (optionnel) :
   - Ajoutez votre domaine personnalisé (ex: `solar.energum.earth`)

7. **Déployer** :
   - Cliquez sur "Deploy"
   - Attendez que le build se termine (environ 3-5 minutes)

### Étape 3 : Vérification

Une fois le déploiement terminé :
1. Accédez à l'URL fournie par Coolify
2. Testez le formulaire
3. Vérifiez que les données arrivent bien dans n8n

## 🧪 Test Local (optionnel)

Pour tester avant de déployer :

```bash
cd landing-page

# Installer les dépendances
npm install

# Lancer en mode développement
npm run dev
```

Ouvrez [http://localhost:3000](http://localhost:3000)

## 🐳 Test avec Docker (optionnel)

```bash
cd landing-page

# Build de l'image
docker build -t solar-landing .

# Lancer le container
docker run -p 3000:3000 solar-landing
```

## 🔧 Dépannage

### Le build échoue

- Vérifiez que le Dockerfile Path est correct : `./landing-page/Dockerfile`
- Vérifiez que le Working Directory est : `./landing-page`

### L'application ne démarre pas

- Vérifiez les logs dans Coolify
- Assurez-vous que le port 3000 est bien exposé
- Vérifiez les variables d'environnement

### Le formulaire ne s'envoie pas

- Vérifiez que le webhook n8n est actif
- Ouvrez la console du navigateur pour voir les erreurs
- Vérifiez la configuration CORS de n8n

## 📝 Webhook n8n

URL du webhook : `https://n8n.energum.earth/webhook/dfb660da-1480-40a5-bbdc-7579e6772fe1`

Format des données envoyées :
```json
{
  "nom": "string",
  "prenom": "string",
  "email": "string",
  "telephone": "string",
  "facture_mensuelle_electricite": "string",
  "coordonnees_gps": {
    "latitude": number,
    "longitude": number
  },
  "date_soumission": "ISO 8601 timestamp"
}
```

## 🎯 URLs importantes

- **Coolify** : https://coolify.energum.earth
- **n8n Webhook** : https://n8n.energum.earth/webhook/dfb660da-1480-40a5-bbdc-7579e6772fe1
- **GitHub** : https://github.com/wadieelmasmodi/LeadsTesla

## 📞 Support

En cas de problème, vérifiez :
1. Les logs dans Coolify
2. La console du navigateur
3. Les logs de n8n
4. La configuration du webhook

Bon déploiement ! 🚀
