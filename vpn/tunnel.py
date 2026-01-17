import os
import sys
import threading
import time
from scapy.all import IP, TCP, UDP, ICMP, send, sniff, Raw, conf
import socket
import ssl

# Configurer scapy pour utiliser L3 sockets (évite le besoin de Npcap sur Windows)
if sys.platform == "win32":
    try:
        from scapy.all import L3RawSocket
        conf.L3socket = L3RawSocket
        print("Scapy configuré pour utiliser L3 sockets (pas de Npcap requis)")
    except ImportError:
        print("L3RawSocket non disponible, Npcap recommandé pour Windows")

class VpnTunnel:
    def __init__(self, vpn_socket, is_client=True):
        self.vpn_socket = vpn_socket  # The SSL socket for VPN communication
        self.is_client = is_client
        self.running = False

    def start_tunnel(self):
        """Démarre le tunneling"""
        self.running = True
        if self.is_client:
            # Client: intercepter les paquets et les envoyer via VPN
            self.client_tunnel()
        else:
            # Serveur: recevoir les paquets et les forwarder
            self.server_tunnel()

    def stop_tunnel(self):
        self.running = False

    def client_tunnel(self):
        """Tunneling côté client: intercepter et envoyer les paquets"""
        print("Tentative de tunneling réseau...")
        
        # Vérifier si on peut faire du sniffing
        try:
            # Tester si sniff fonctionne
            test_sniff = sniff(count=1, timeout=1, filter="ip")
            can_sniff = True
        except Exception as e:
            print(f"Sniffing non disponible: {e}")
            print("Le tunneling réseau complet nécessite Npcap sur Windows")
            can_sniff = False
        
        if not can_sniff:
            print("Mode dégradé: Seule la connexion SSL VPN est active")
            print("Pour le tunneling complet, installez Npcap depuis https://npcap.com/")
            # Garder le thread actif pour maintenir la connexion SSL
            while self.running:
                time.sleep(1)
            return

        def packet_handler(pkt):
            if self.running and IP in pkt:
                # Sérialiser le paquet
                packet_data = bytes(pkt)
                try:
                    # Envoyer via le VPN
                    self.vpn_socket.send(packet_data)
                except:
                    pass  # Ignorer les erreurs d'envoi

        # Intercepter tous les paquets IP (nécessite root/admin)
        try:
            sniff(prn=packet_handler, filter="ip", store=0)
        except PermissionError:
            print("Erreur: Droits administrateur requis pour intercepter les paquets")
        except Exception as e:
            print(f"Erreur de tunneling client: {e}")

    def server_tunnel(self):
        """Tunneling côté serveur: recevoir et forwarder les paquets"""
        while self.running:
            try:
                # Recevoir un paquet via VPN
                packet_data = self.vpn_socket.recv(65535)
                if not packet_data:
                    break
                
                # Désérialiser le paquet
                pkt = IP(packet_data)
                
                # Modifier les adresses si nécessaire (NAT simple)
                if self.is_client:  # Attendre, c'est le serveur
                    # Pour un vrai VPN, implémenter NAT
                    pass
                
                # Forwarder le paquet
                send(pkt, verbose=0)
                
            except Exception as e:
                print(f"Erreur de tunneling serveur: {e}")
                break

# Fonction pour configurer le routage (nécessite admin)
def setup_routing(tun_interface, vpn_gateway):
    """Configure le routage pour envoyer tout le trafic via le VPN"""
    if sys.platform == "win32":
        # Windows
        os.system(f"route add 0.0.0.0 mask 0.0.0.0 {vpn_gateway}")
    else:
        # Linux/Mac
        os.system(f"ip route add default via {vpn_gateway} dev {tun_interface}")

def create_tun_interface():
    """Crée une interface TUN/TAP (simplifié, nécessite des bibliothèques spécifiques)"""
    # Note: Créer une vraie interface TUN nécessite des droits et des libs comme python-tuntap
    # Pour cette démo, on simule
    print("Interface TUN simulée créée (remplacer par une vraie implémentation)")
    return "tun0"