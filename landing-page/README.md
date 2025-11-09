# Landing Page Solaire

Une landing page moderne pour collecter les informations des clients intéressés par une installation solaire.

## 🚀 Fonctionnalités

- **Formulaire de contact moderne** avec validation
- **Carte interactive** pour sélectionner l'emplacement de la toiture (Leaflet)
- **Intégration webhook n8n** pour l'envoi automatique des données
- **Design responsive** avec Tailwind CSS et shadcn/ui
- **Optimisé pour la production** avec Next.js 14

## 📋 Données collectées

Le formulaire collecte les informations suivantes :
- Nom et Prénom
- Email
- Numéro de téléphone
- Facture mensuelle d'électricité
- Coordonnées GPS de la toiture (sélection sur carte)

Les données sont envoyées au format JSON vers le webhook n8n : `https://n8n.energum.earth/webhook/dfb660da-1480-40a5-bbdc-7579e6772fe1`

## 🛠️ Technologies

- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage statique
- **Tailwind CSS** - Styling moderne
- **shadcn/ui** - Composants UI élégants
- **React Leaflet** - Cartes interactives
- **Lucide React** - Icônes modernes

## 🏃 Développement local

### Installation

```bash
cd landing-page
npm install
```

### Lancement du serveur de développement

```bash
npm run dev
```

Ouvrez [http://localhost:3000](http://localhost:3000) dans votre navigateur.

## 🐳 Déploiement avec Docker

### Build de l'image

```bash
docker build -t solar-landing-page .
```

### Lancement avec Docker Compose

```bash
docker-compose up -d
```

L'application sera accessible sur le port 3000.

## 🚢 Déploiement sur Coolify

1. Poussez le code sur GitHub
2. Dans Coolify, créez une nouvelle application
3. Sélectionnez le repository GitHub
4. Choisissez la branche `landing-page-solaire`
5. Définissez le Build Pack sur "Dockerfile"
6. Configurez le port sur 3000
7. Déployez !

## 📝 Structure du projet

```
landing-page/
├── app/
│   ├── layout.tsx          # Layout principal
│   ├── page.tsx            # Page d'accueil avec formulaire
│   └── globals.css         # Styles globaux
├── components/
│   ├── ui/                 # Composants shadcn/ui
│   ├── map-selector.tsx    # Wrapper pour le composant carte
│   └── map-selector-client.tsx  # Composant carte Leaflet
├── lib/
│   └── utils.ts            # Utilitaires
├── Dockerfile              # Configuration Docker
├── docker-compose.yml      # Configuration Docker Compose
└── package.json            # Dépendances
```

## 🎨 Personnalisation

### Modifier le webhook

Modifiez l'URL du webhook dans `app/page.tsx` ligne 68 :

```typescript
const response = await fetch('VOTRE_WEBHOOK_URL', {
  // ...
});
```

### Modifier les couleurs

Les couleurs sont définies dans `app/globals.css` avec les variables CSS Tailwind.

## 📄 Licence

Projet privé - Tous droits réservés
