# Écran d’accueil — prototype

Application légère (Python standard library + SQLite) destinée à un écran d’accueil vertical.

## Fonctions

- Carousel plein écran automatique et adapté aux écrans portrait.
- Horloge/date locale du navigateur.
- Trois boutons d'information en bas d’écran.
- Administration à `/admin` : annonces, ordre, activation, texte, couleur, durée et informations pratiques.
- Les changements sont enregistrés dans `data/screen.db`; aucun code n'est nécessaire pour gérer le contenu courant.

## Démarrage de démonstration

```bash
cd /chemin/accueil-ecran
ADMIN_PASSWORD='un-mot-de-passe-long-et-unique' \
SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" \
PORT=8099 python3 app.py
```

Le service écoute volontairement uniquement sur `127.0.0.1`. Pour une mise en ligne, le publier derrière Nginx avec HTTPS, ne jamais employer les valeurs par défaut de `ADMIN_PASSWORD` / `SESSION_SECRET`, et conserver la base SQLite dans une sauvegarde régulière.

## Prochaine étape de déploiement

Créer un sous-domaine DNS-only (proposition : `ecran.jzs.fr`) et configurer Nginx pour proxyfier vers `127.0.0.1:8099`. Cette étape demande validation explicite car elle modifie DNS et la configuration du serveur public.
