# Personal VPN

Un VPN Python sécurisé avec authentification par certificats clients.

## Structure du projet
- `vpn/` : Package principal
  - `core.py` : Classes VPNHost et VPNClient
  - `tunnel.py` : Logique de tunneling
  - `admin.py` : Interface d'administration web
  - `certs.py` : Gestionnaire de certificats
  - `user_manager.py` : Gestionnaire d'utilisateurs
- `certs/` : Dossier des certificats CA et serveur
  - `ca.crt`, `ca.key` : Certificat et clé de l'Autorité de Certification
  - `server.crt`, `server.key` : Certificat et clé du serveur VPN
- `users/` : Dossiers des utilisateurs avec leurs certificats
- `generate_certs.py` : Script de génération des certificats
- `install_npcap.py` : Script d'installation automatique de Npcap (Windows)
- `test_installer.py` : Script de test de l'installateur Npcap
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

### Dépendances optionnelles (pour installation automatique de Npcap)
```bash
pip install requests pywin32
```

### Npcap (Windows uniquement)
Pour le tunneling réseau complet sur Windows, Npcap est requis :

**Installation automatique :**
```bash
python install_npcap.py
```
Le script détecte automatiquement si Npcap est installé et propose de l'installer avec élévation automatique des droits administrateur. L'installation nécessite une interaction utilisateur pour confirmer les options (notamment "WinPcap API compatibility").

**Installation manuelle :**
- Téléchargez Npcap depuis https://npcap.com/
- Choisissez "Npcap with WinPcap API compatibility"
- Redémarrez après l'installation

**Note :** Sans Npcap, le VPN fonctionne en mode SSL uniquement (connexion chiffrée mais pas de tunneling réseau).

### Tests
```bash
# Tester l'installateur Npcap (sans installation réelle)
python test_installer.py

# Tester la génération de certificats
python generate_certs.py

# Tester le serveur VPN
python host.py

# Tester le client VPN (dans un autre terminal)
python client.py root --host localhost
```

## Configuration
1. **Générer les certificats :**
   ```bash
   python generate_certs.py
   ```
   Cela crée :
   - `certs/ca.crt`, `certs/ca.key` : Autorité de certification
   - `certs/server.crt`, `certs/server.key` : Certificats du serveur
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
  Exemple : `python client.py root`

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