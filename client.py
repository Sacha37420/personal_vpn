from vpn import VPNClient
import argparse
import time
import sys
import os

def check_and_install_npcap():
    """Vérifie si Npcap est installé et propose l'installation si nécessaire"""
    if sys.platform != "win32":
        return True  # Npcap seulement nécessaire sur Windows

    # Vérifier si Npcap est installé
    npcap_installed = False
    npcap_paths = [
        "C:\\Windows\\System32\\Npcap\\wpcap.dll",
        "C:\\Windows\\SysWOW64\\Npcap\\wpcap.dll"
    ]

    for path in npcap_paths:
        if os.path.exists(path):
            npcap_installed = True
            break

    # Tester scapy si les DLL ne sont pas trouvées
    if not npcap_installed:
        try:
            from scapy.all import sniff
            test_packets = sniff(count=1, timeout=1, store=False)
            npcap_installed = True
        except:
            pass

    if not npcap_installed:
        print("⚠️  Npcap n'est pas installé.")
        print("Npcap est nécessaire pour le tunneling réseau complet.")
        print()

        response = input("Voulez-vous installer Npcap automatiquement ? (o/N): ").lower().strip()
        if response in ['o', 'oui', 'y', 'yes']:
            print("Lancement de l'installateur Npcap...")
            try:
                result = os.system(f'python "{os.path.join(os.path.dirname(__file__), "install_npcap.py")}"')
                if result == 0:
                    print("Installation terminée. Redémarrez et relancez le client.")
                else:
                    print("Installation échouée.")
                return False
            except Exception as e:
                print(f"Erreur lors du lancement de l'installateur: {e}")
                return False
        else:
            print("Installation annulée. Le VPN fonctionnera en mode SSL uniquement.")
            print()

    return True

if __name__ == "__main__":
    # Vérifier Npcap avant de continuer
    if not check_and_install_npcap():
        sys.exit(1)

    parser = argparse.ArgumentParser(description='VPN Client')
    parser.add_argument('username', nargs='?', default='root', help='Nom d\'utilisateur')
    parser.add_argument('--host', default='localhost', help='Adresse du serveur VPN')
    args = parser.parse_args()
    
    client = VPNClient(host=args.host, username=args.username)
    client.connect()
    
    print("VPN tunneling actif. Tout le trafic réseau passe par la connexion VPN.")
    print("Appuyez sur Ctrl+C pour arrêter.")
    
    try:
        while True:
            time.sleep(1)  # Garder le programme actif
    except KeyboardInterrupt:
        print("Arrêt du client VPN...")
    finally:
        client.close()