import os
import json
from vpn import CertificateManager, UserManager

def create_users_json(users_list, user_manager):
    """Crée le fichier users.json avec la liste des utilisateurs"""
    for username in users_list:
        folder = f"users/{username}"
        cert_file = f"{folder}/{username}.crt"
        key_file = f"{folder}/{username}.key"
        user_manager.add_user(username, folder, cert_file, key_file)

if __name__ == "__main__":
    # Liste des utilisateurs à créer
    users_list = ["root", "invite"]  # Modifiez cette liste selon vos besoins
    
    cert_manager = CertificateManager()
    user_manager = UserManager()
    
    print("Génération du certificat CA...")
    ca_key, ca_cert = cert_manager.generate_ca_cert()
    
    print("Génération du certificat serveur...")
    cert_manager.generate_server_cert(ca_key, ca_cert)
    
    print("Génération des certificats utilisateurs...")
    for username in users_list:
        cert_manager.generate_user_cert(username, ca_key, ca_cert)
        print(f"Certificat généré pour {username}")
    
    print("Création du fichier users.json...")
    create_users_json(users_list, user_manager)
    
    print("Certificats générés avec succès !")
    print("Fichiers créés :")
    print("- certs/ca.crt, certs/ca.key")
    print("- certs/server.crt, certs/server.key")
    print("- users.json")
    print("- users/<username>/<username>.crt, <username>.key, ca.crt")