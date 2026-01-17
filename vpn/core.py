import socket
import threading
import ssl
import json
import os
import time
from .user_manager import UserManager
import requests
from .tunnel import VpnTunnel  # Pour les requêtes HTTP

class VPNHost:
    def __init__(self, host='0.0.0.0', port=1194, ca_cert='certs/ca.crt', server_cert='certs/server.crt', server_key='certs/server.key', users_file='users.json'):
        self.host = host
        self.port = port
        self.ca_cert = ca_cert
        self.server_cert = server_cert
        self.server_key = server_key
        self.users_file = users_file
        
        # Charger la liste des utilisateurs
        self.user_manager = UserManager(self.users_file)
        
        # Socket serveur
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        # Contexte SSL avec vérification des certificats clients
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(certfile=self.server_cert, keyfile=self.server_key)
        self.ssl_context.load_verify_locations(cafile=self.ca_cert)
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED  # Exiger un certificat client valide
        self.ssl_context.check_hostname = False

    def start(self):
        print(f"VPN Host (SSL) started on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection attempt from {addr}")
            
            try:
                # Envelopper avec SSL
                ssl_client_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                
                # Vérifier le certificat client
                client_cert = ssl_client_socket.getpeercert()
                if not client_cert:
                    print("No client certificate provided")
                    ssl_client_socket.close()
                    continue
                
                # Extraire le nom d'utilisateur du CN
                username = None
                for attr in client_cert['subject']:
                    for key, value in attr:
                        if key == 'commonName':
                            username = value
                            break
                    if username:
                        break
                
                if not username or not self.user_manager.get_user(username):
                    print(f"Unauthorized user: {username}")
                    ssl_client_socket.close()
                    continue
                
                print(f"Authorized connection from {username} at {addr}")
                
                client_thread = threading.Thread(target=self.handle_client, args=(ssl_client_socket, username))
                client_thread.start()
                
            except ssl.SSLError as e:
                print(f"SSL Error: {e}")
                client_socket.close()
            except Exception as e:
                print(f"Error: {e}")
                client_socket.close()

    def handle_client(self, client_socket, username):
        try:
            # Démarrer le tunneling
            tunnel = VpnTunnel(client_socket, is_client=False)
            tunnel_thread = threading.Thread(target=tunnel.start_tunnel)
            tunnel_thread.start()
            
            # Garder la connexion ouverte
            while True:
                # Pour le mode tunneling, on ne fait qu'attendre
                time.sleep(1)
                
        except Exception as e:
            print(f"Error handling client {username}: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed for {username}")

class VPNClient:
    def __init__(self, host='localhost', port=1194, username='alice', admin_port=80):
        self.host = host
        self.port = port
        self.username = username
        self.admin_port = admin_port
        
        # Charger les infos utilisateur si existant
        self.user_manager = UserManager()
        user_info = self.user_manager.get_user(username)
        if user_info:
            self.cert_file = user_info['cert_file']
            self.key_file = user_info['key_file']
            self.ca_file = os.path.join(user_info['folder'], 'ca.crt')
            self.registered = True
        else:
            self.registered = False
        
        # Socket client
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Contexte SSL (initialisé seulement si enregistré)
        if self.registered:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            self.ssl_context.load_verify_locations(cafile=self.ca_file)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def register_user(self):
        """S'inscrire auprès de l'administration pour créer un nouvel utilisateur"""
        try:
            url = f"http://{self.host}:{self.admin_port}/create_user"
            response = requests.post(url, data={'username': self.username})
            if response.status_code == 201:
                print(f"Utilisateur {self.username} créé avec succès !")
                # Recharger les infos utilisateur
                self.user_manager = UserManager()  # Recharger
                user_info = self.user_manager.get_user(self.username)
                if user_info:
                    self.cert_file = user_info['cert_file']
                    self.key_file = user_info['key_file']
                    self.ca_file = os.path.join(user_info['folder'], 'ca.crt')
                    self.registered = True
                    # Initialiser le contexte SSL
                    self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                    self.ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
                    self.ssl_context.load_verify_locations(cafile=self.ca_file)
                    self.ssl_context.check_hostname = False
                    self.ssl_context.verify_mode = ssl.CERT_NONE
                    return True
            else:
                print(f"Erreur lors de l'inscription: {response.json()}")
                return False
        except Exception as e:
            print(f"Erreur de connexion à l'administration: {e}")
            return False

    def connect(self):
        if not self.registered:
            print(f"Utilisateur {self.username} non enregistré. Tentative d'inscription...")
            if not self.register_user():
                print("Échec de l'inscription. Connexion impossible.")
                return
        
        try:
            self.client_socket.connect((self.host, self.port))
            self.ssl_socket = self.ssl_context.wrap_socket(self.client_socket, server_hostname=self.host)
            print(f"Connected securely as {self.username} to VPN Host at {self.host}:{self.port}")
            
            # Démarrer le tunneling
            self.tunnel = VpnTunnel(self.ssl_socket, is_client=True)
            self.tunnel_thread = threading.Thread(target=self.tunnel.start_tunnel)
            self.tunnel_thread.start()
            
        except Exception as e:
            print(f"Failed to connect: {e}")

    def send_data(self, data):
        # Dans le mode tunneling, on n'envoie plus de messages texte
        # Tout le trafic passe par le tunnel
        pass

    def close(self):
        self.ssl_socket.close()
        print("Connection closed")