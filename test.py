from vpn import VPNClient
import time

client = VPNClient(username='alice')
client.connect()
print("Tunneling actif...")
time.sleep(10)  # Tester pendant 10 secondes
client.close()