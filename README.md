# Personal VPN

Un VPN Python sécurisé avec authentification par certificats clients.

## Structure du projet
- `vpn.py` : Classes principales VPNHost et VPNClient
- `certs.py` : Gestionnaire de certificats
- `user_manager.py` : Gestionnaire d'utilisateurs
- `generate_certs.py` : Script de génération des certificats
- `host.py`, `client.py`, `test.py` : Scripts de lancement

## Fonctionnalités
- Connexion chiffrée SSL/TLS
- Authentification par certificats clients
- Gestion des utilisateurs avec dossiers dédiés
- **Tunneling complet** : Tout le trafic réseau passe par la connexion VPN
- Certificats auto-signés

## Installation
```bash
pip install -r requirements.txt
```

## Configuration
1. **Générer les certificats :**
   ```bash
   python generate_certs.py
   ```
   Cela crée :
   - `ca.crt`, `ca.key` : Autorité de certification
   - `users.json` : Liste des utilisateurs
   - `users/<username>/` : Dossier avec certificat et clé pour chaque utilisateur

2. **Modifier la liste des utilisateurs :**
   Éditez `generate_certs.py` pour changer `users_list`.

## Utilisation
- **Lancer l'hôte (avec interface admin) :**
  ```bash
  python host.py
  ```
  L'interface d'administration sera disponible sur http://localhost (port 80)

- **Interface d'administration :**
  - Accédez à http://localhost:60 dans un navigateur
  - Créez de nouveaux utilisateurs via le formulaire
  - Les certificats sont générés automatiquement

- **Lancer un client :**
  ```bash
  python client.py <username>
  ```
  Exemple : `python client.py alice`

- **Test automatique :**
  ```bash
  python test.py
  ```

## Sécurité
- Les connexions sont chiffrées avec TLS
- Seuls les utilisateurs avec un certificat valide peuvent se connecter
- Chaque utilisateur a son propre certificat dans `users/<username>/`

## Important
- **Droits administrateur** : Le tunneling nécessite des droits root/admin pour intercepter les paquets réseau
- **Configuration réseau** : Le routage doit être configuré pour diriger le trafic via le VPN
- **Plateforme** : Testé principalement sur Linux ; Windows peut nécessiter des pilotes TUN/TAP

## Note
Pour un VPN réel, ajoutez du tunneling de paquets réseau et une gestion plus avancée des certificats.