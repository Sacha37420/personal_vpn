#!/usr/bin/env python3
"""
Script d'installation automatique de Npcap pour Windows
Requis pour le tunneling réseau complet avec Scapy

Dépendances optionnelles:
- pywin32 (pour relancement automatique en admin)
- requests (pour téléchargement automatique)
"""

import os
import sys
import platform
import subprocess
import tempfile
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("⚠️  Module 'requests' non trouvé. Installation manuelle recommandée.")
    print("pip install requests")
    requests = None

class NpcapInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()

        # URL de téléchargement Npcap (version stable)
        self.npcap_url = "https://npcap.com/dist/npcap-1.79.exe"
        self.npcap_msi_url = "https://npcap.com/dist/npcap-1.79.msi"

        # Chemins de vérification
        self.npcap_dll_paths = [
            "C:\\Windows\\System32\\Npcap\\wpcap.dll",
            "C:\\Windows\\SysWOW64\\Npcap\\wpcap.dll"
        ]

    def is_admin(self):
        """Vérifie si le script tourne en mode administrateur"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin(self):
        """Relance le script en tant qu'administrateur"""
        try:
            import win32api
            import win32con
            import win32event
            import win32process
            from win32com.shell.shell import ShellExecuteEx
            from win32com.shell import shellcon

            # Utiliser ShellExecuteEx pour relancer en tant qu'admin
            params = f'"{sys.executable}" "{sys.argv[0]}"'
            working_dir = os.getcwd()

            process_info = ShellExecuteEx(
                nShow=win32con.SW_SHOWNORMAL,
                fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                lpVerb='runas',  # runas = run as administrator
                lpFile=sys.executable,
                lpParameters=f'"{sys.argv[0]}"',
                lpDirectory=working_dir
            )

            # Attendre que le processus se termine
            win32event.WaitForSingleObject(process_info['hProcess'], win32event.INFINITE)
            win32api.CloseHandle(process_info['hProcess'])

            return True

        except ImportError:
            # Fallback si pywin32 n'est pas installé
            try:
                import subprocess
                # Utiliser PowerShell pour relancer
                cmd = [
                    'powershell',
                    '-Command',
                    f'Start-Process "{sys.executable}" -ArgumentList "{sys.argv[0]}" -Verb RunAs -Wait'
                ]
                subprocess.run(cmd, check=True)
                return True
            except:
                return False
        except:
            return False

    def is_npcap_installed(self):
        """Vérifie si Npcap est déjà installé"""
        print("Vérification de l'installation de Npcap...")

        # Méthode 1: Vérifier les fichiers DLL
        for dll_path in self.npcap_dll_paths:
            if os.path.exists(dll_path):
                print(f"✓ Npcap trouvé: {dll_path}")
                return True

        # Méthode 2: Tester scapy
        try:
            from scapy.all import sniff
            # Essayer un sniff rapide pour voir si ça fonctionne
            test_packets = sniff(count=1, timeout=1, store=False)
            print("✓ Scapy peut sniffer les paquets")
            return True
        except Exception as e:
            print(f"✗ Scapy ne peut pas sniffer: {e}")

        print("✗ Npcap n'est pas installé ou ne fonctionne pas")
        return False

    def download_file(self, url, dest_path):
        """Télécharge un fichier depuis une URL"""
        if requests is None:
            print("✗ Module 'requests' requis pour le téléchargement automatique")
            print("Installez avec: pip install requests")
            return False

        print(f"Téléchargement depuis {url}...")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(".1f", end='', flush=True)

            print(" ✓ Téléchargement terminé")
            return True

        except Exception as e:
            print(f"✗ Erreur de téléchargement: {e}")
            return False

    def install_npcap(self, installer_path):
        """Installe Npcap en utilisant l'installateur (version standard)"""
        print("Installation de Npcap...")
        print("⚠️  Note: L'installation silencieuse n'est disponible que pour les versions OEM")
        print("   L'installateur va s'ouvrir - suivez les instructions à l'écran")
        print()

        try:
            # Pour la version standard, on utilise l'interface normale
            # avec des paramètres pour réduire les interactions
            cmd = [
                installer_path,
                '/norestart',  # Ne pas redémarrer automatiquement
                '/passive'     # Installation passive (moins d'interactions)
            ]

            print("Lancement de l'installateur Npcap...")
            print("Veuillez suivre les instructions à l'écran...")
            print("(Cochez 'WinPcap API compatibility' si demandé)")
            print()

            result = subprocess.run(cmd, capture_output=False, timeout=600)  # 10 minutes timeout

            if result.returncode == 0:
                print("✓ Installation terminée")
                return True
            elif result.returncode == 3010:  # Restart required
                print("✓ Installation terminée (redémarrage requis)")
                return True
            else:
                print(f"⚠️  Code de retour: {result.returncode}")
                print("L'installation a peut-être réussi malgré tout")
                return True  # On considère que c'est réussi car l'utilisateur a pu interagir

        except subprocess.TimeoutExpired:
            print("⚠️  Timeout de l'installation")
            print("Vérifiez si Npcap a été installé malgré tout")
            return True
        except Exception as e:
            print(f"✗ Erreur lors de l'installation: {e}")
            return False

    def run(self):
        """Fonction principale"""
        print("=== Installateur automatique Npcap ===")
        print(f"Système: {self.system} {self.arch}")
        print()

        # Vérifier le système d'exploitation
        if self.system != "windows":
            print("✗ Ce script est uniquement pour Windows")
            return False

        # Vérifier les droits admin
        if not self.is_admin():
            print("✗ Droits administrateur requis pour installer Npcap")
            print()

            response = input("Voulez-vous relancer le script en tant qu'administrateur ? (o/N): ").lower().strip()
            if response in ['o', 'oui', 'y', 'yes']:
                print("Relancement en tant qu'administrateur...")
                if self.run_as_admin():
                    print("Script relancé avec succès. Fermeture de cette instance.")
                    return True
                else:
                    print("Échec du relancement automatique.")
            else:
                print("Installation annulée.")

            print()
            print("=== Installation manuelle ===")
            print("Pour installer Npcap manuellement :")
            print("1. Téléchargez depuis https://npcap.com/")
            print("2. Clic droit sur l'installateur > 'Exécuter en tant qu'administrateur'")
            print("3. Suivez les instructions d'installation")
            return False

        # Vérifier si déjà installé
        if self.is_npcap_installed():
            print("Npcap est déjà installé et fonctionnel !")
            return True

        # Demander confirmation
        print()
        print("Npcap n'est pas installé.")
        print("Npcap est nécessaire pour le tunneling réseau complet du VPN.")
        print("⚠️  Note: L'installation nécessite votre interaction (cocher 'WinPcap API compatibility')")
        response = input("Voulez-vous procéder à l'installation de Npcap ? (o/N): ").lower().strip()

        if response not in ['o', 'oui', 'y', 'yes']:
            print("Installation annulée.")
            return False

        # Créer un dossier temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            installer_path = os.path.join(temp_dir, "npcap-installer.exe")

            # Télécharger l'installateur
            if not self.download_file(self.npcap_url, installer_path):
                print("Échec du téléchargement. Vous pouvez installer Npcap manuellement depuis https://npcap.com/")
                return False

            # Installer
            if not self.install_npcap(installer_path):
                print("Échec de l'installation. Vous pouvez installer Npcap manuellement depuis https://npcap.com/")
                return False

        # Vérifier l'installation
        print()
        print("Vérification de l'installation...")
        time.sleep(2)  # Attendre un peu

        if self.is_npcap_installed():
            print("✓ Npcap installé avec succès !")
            print("Redémarrez votre ordinateur pour que les changements prennent effet.")
            return True
        else:
            print("✗ L'installation semble avoir échoué.")
            print("Vous pouvez installer Npcap manuellement depuis https://npcap.com/")
            return False

def main():
    installer = NpcapInstaller()
    success = installer.run()

    if success:
        print()
        print("=== Prochaines étapes ===")
        print("1. Redémarrez votre ordinateur")
        print("2. Relancez le client VPN: python client.py root --host 192.168.1.8")
        print("3. Le tunneling réseau devrait maintenant fonctionner")
    else:
        print()
        print("=== Installation manuelle ===")
        print("Téléchargez et installez Npcap depuis: https://npcap.com/")
        print("Choisissez la version 'Npcap with WinPcap API compatibility'")

    input("\nAppuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()