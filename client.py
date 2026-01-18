import os
import sys
import platform
import subprocess
import time
import argparse
from vpn import VPNClient

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

from vpn import VPNClient
import argparse
import time
import sys
import os
import platform
import subprocess
import ctypes

def is_admin():
    """Vérifie si le script tourne en mode administrateur"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relance le script en tant qu'administrateur"""
    if platform.system() == "Windows":
        # Windows
        try:
            script = sys.executable
            args = ' '.join(sys.argv)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", script, args, None, 1)
            sys.exit(0)  # Quitte le processus actuel
        except Exception as e:
            print(f"Erreur lors du relancement en admin: {e}")
            sys.exit(1)
    else:
        print("Mode admin automatique seulement sur Windows")
        return False

if __name__ == "__main__":
    # Vérifier les droits admin
    if platform.system() == "Windows" and not is_admin():
        print("❌ Le client VPN nécessite les droits administrateur pour intercepter les paquets réseau.")
        print("Veuillez relancer ce script en mode administrateur :")
        print("  - Clic droit sur l'invite de commande → 'Exécuter en tant qu'administrateur'")
        print("  - Puis : python client.py [username] --host [IP]")
        sys.exit(1)
    
    # Vérifier Npcap avant de continuer
    if not check_and_install_npcap():
        sys.exit(1)

    parser = argparse.ArgumentParser(description='VPN Client')
    parser.add_argument('username', nargs='?', default='lea', help='Nom d\'utilisateur')
    parser.add_argument('--host', default='192.168.1.8', help='Adresse du serveur VPN')
    args = parser.parse_args()
    
    client = VPNClient(host=args.host, username=args.username)
    client.connect()
    
    print("VPN tunneling actif. Tout le trafic réseau passe par la connexion VPN.")
    print("Appuyez sur Ctrl+C pour arrêter.")
    
    try:
        while True:
            time.sleep(1)  # Garder le programme actif
            if hasattr(client, 'tunnel') and client.tunnel.disconnected:
                print("Déconnexion de l'hôte VPN détectée.")
                break
    except KeyboardInterrupt:
        print("Arrêt du client VPN...")
    finally:
        client.close()