from vpn import VPNHost, AdminInterface, UserManager, CertificateManager
import threading

if __name__ == "__main__":
    # Initialiser les gestionnaires
    user_manager = UserManager()
    cert_manager = CertificateManager()
    
    # Lancer l'interface d'administration dans un thread séparé
    admin = AdminInterface(port=80, user_manager=user_manager, cert_manager=cert_manager)
    admin_thread = threading.Thread(target=admin.run)
    admin_thread.daemon = True
    admin_thread.start()
    
    # Lancer l'hôte VPN
    host = VPNHost()
    host.start()