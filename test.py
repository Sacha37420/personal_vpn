from vpn import VPNClient
import time

client = VPNClient(username='root')
client.connect()
print("Tunneling actif...")
time.sleep(10)  # Tester pendant 10 secondes
client.close()