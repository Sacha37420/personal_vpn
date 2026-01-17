from vpn import VPNClient
import sys
import time

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else 'alice'
    client = VPNClient(username=username)
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