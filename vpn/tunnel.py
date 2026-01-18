import os
import sys
import threading
import time
from scapy.all import IP, TCP, UDP, ICMP, send, sniff, Raw, conf
import socket
import ssl
import errno

# Configurer scapy pour utiliser L3 sockets (évite le besoin de Npcap sur Windows)
if sys.platform == "win32":
    try:
        from scapy.all import L3RawSocket
        conf.L3socket = L3RawSocket
        print("Scapy configuré pour utiliser L3 sockets (pas de Npcap requis)")
    except ImportError:
        print("L3RawSocket non disponible, Npcap recommandé pour Windows")

class VpnTunnel:
    def __init__(self, vpn_socket, is_client=True, server_ip=None):
        self.vpn_socket = vpn_socket  # The SSL socket for VPN communication
        self.is_client = is_client
        self.running = False
        self.client_packets_sent = 0
        self.client_packets_received = 0
        self.server_packets_received = 0
        self.server_packets_sent = 0
        self.disconnected = False
        self.send_failures = 0
        self.server_ip = server_ip
        self.nat_table = {}

    def client_receive(self):
        """Reçoit les paquets du serveur et les injecte localement"""
        while self.running:
            try:
                packet_data = self.vpn_socket.recv(65535)
                if not packet_data:
                    break
                pkt = IP(packet_data)
                self.client_packets_received += 1
                if self.client_packets_received % 10 == 0:  # Plus fréquent pour debug
                    print(f"Client: {self.client_packets_received} paquets reçus")
                # Injecter le paquet réponse dans le réseau local
                send(pkt, verbose=0)
            except Exception as e:
                print(f"Erreur réception client: {e}")
                break
        """Sniffer pour les réponses et les envoyer au client via NAT inverse"""
        while self.running:
            try:
                pkts = sniff(count=1, timeout=1, filter=f"ip dst {self.server_ip}")
                if pkts:
                    pkt = pkts[0]
                    if IP in pkt:
                        # Vérifier si c'est une réponse à NAT
                        key = None
                        if TCP in pkt:
                            key = (self.server_ip, pkt[TCP].sport)
                        elif UDP in pkt:
                            key = (self.server_ip, pkt[UDP].sport)
                        
                        if key and key in self.nat_table:
                            print(f"Reverse NAT: Paquet reçu de {pkt[IP].src}, envoyé au client {self.nat_table[key][0]}")
                            # Traduire l'adresse de destination
                            pkt[IP].dst = self.nat_table[key][0]
                            if TCP in pkt:
                                pkt[TCP].dport = self.nat_table[key][1]
                            elif UDP in pkt:
                                pkt[UDP].dport = self.nat_table[key][1]
                            
                            # Envoyer au client
                            packet_data = bytes(pkt)
                            self.vpn_socket.send(packet_data)
            except Exception as e:
                if not (hasattr(e, 'errno') and e.errno == errno.EMSGSIZE):
                    print(f"Erreur reverse NAT: {e}")
    def reverse_nat(self):
        """Sniffer pour les réponses et les envoyer au client via NAT inverse"""
        while self.running:
            try:
                pkts = sniff(count=1, timeout=1, filter=f"ip dst {self.server_ip}")
                if pkts:
                    pkt = pkts[0]
                    if IP in pkt:
                        # Vérifier si c'est une réponse à NAT
                        key = None
                        if TCP in pkt:
                            key = (self.server_ip, pkt[TCP].sport)
                        elif UDP in pkt:
                            key = (self.server_ip, pkt[UDP].sport)
                        
                        if key and key in self.nat_table:
                            print(f"Reverse NAT: Paquet reçu de {pkt[IP].src}, envoyé au client {self.nat_table[key][0]}")
                            # Traduire l'adresse de destination
                            pkt[IP].dst = self.nat_table[key][0]
                            if TCP in pkt:
                                pkt[TCP].dport = self.nat_table[key][1]
                            elif UDP in pkt:
                                pkt[UDP].dport = self.nat_table[key][1]
                            
                            # Envoyer au client
                            packet_data = bytes(pkt)
                            self.vpn_socket.send(packet_data)
            except Exception as e:
                if not (hasattr(e, 'errno') and e.errno == errno.EMSGSIZE):
                    print(f"Erreur reverse NAT: {e}")
    def start_tunnel(self):
        """Démarre le tunneling"""
        self.running = True
        if self.is_client:
            # Client: intercepter les paquets sortants et les envoyer via VPN
            self.client_send_thread = threading.Thread(target=self.client_tunnel)
            self.client_send_thread.start()
            # Recevoir les paquets entrants du VPN
            self.client_receive_thread = threading.Thread(target=self.client_receive)
            self.client_receive_thread.start()
        else:
            # Serveur: recevoir les paquets et les forwarder
            # Démarrer le thread reverse NAT
            self.reverse_thread = threading.Thread(target=self.reverse_nat)
            self.reverse_thread.start()
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
                # Exclure le trafic vers l'IP du serveur VPN (pour accéder à l'admin directement)
                if self.server_ip and pkt[IP].dst == self.server_ip:
                    return  # Ne pas tunneler
                
                # Sérialiser le paquet
                packet_data = bytes(pkt)
                try:
                    # Envoyer via le VPN
                    self.vpn_socket.send(packet_data)
                    self.client_packets_sent += 1
                    if self.client_packets_sent % 100 == 0:
                        print(f"Client: {self.client_packets_sent} paquets envoyés")
                    self.send_failures = 0  # reset on success
                except:
                    self.send_failures += 1
                    if self.send_failures > 10:
                        print("Déconnexion de l'hôte VPN détectée (échecs d'envoi répétés)")
                        self.disconnected = True
                        self.running = False

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
                
                self.server_packets_received += 1
                
                # Désérialiser le paquet
                pkt = IP(packet_data)
                
                # Vérifier la taille du paquet (éviter les erreurs "Message too long")
                if len(pkt) > 65535:  # Taille max IP
                    print(f"Paquet trop grand ({len(pkt)} bytes), ignoré")
                    continue
                
                # NAT: Changer l'IP source pour celle du serveur
                if IP in pkt:
                    original_src = pkt[IP].src
                    pkt[IP].src = self.server_ip
                    
                    # Enregistrer le mapping pour les réponses (TCP/UDP)
                    if TCP in pkt:
                        key = (self.server_ip, pkt[TCP].dport)
                        self.nat_table[key] = (original_src, pkt[TCP].dport)
                    elif UDP in pkt:
                        key = (self.server_ip, pkt[UDP].dport)
                        self.nat_table[key] = (original_src, pkt[UDP].dport)
                
                # Forwarder le paquet
                send(pkt, verbose=0)
                self.server_packets_sent += 1
                
            except Exception as e:
                if hasattr(e, 'errno') and e.errno == errno.EMSGSIZE:
                    # Paquet trop grand pour l'interface, ignorer silencieusement
                    continue
                print(f"Erreur de tunneling serveur: {e}")
                continue  # Continuer au lieu d'arrêter le tunnel

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