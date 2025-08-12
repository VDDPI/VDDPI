import socket
import ssl
import time

client_cert = 'consumer.crt'
client_key = 'consumer.key'

ca_cert = 'code/RootCA.pem'

PRIVATE_CA_ISSUE_URL = "http://192.168.220.5:8001/issue"
SUBSCRIPTION_KEY = "1234567890abcdef1234567890abcdef"

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)
context.load_verify_locations(cafile=ca_cert)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
with context.wrap_socket(client_socket, server_hostname='192.168.220.5') as tls_socket:
    tls_socket.connect(('192.168.220.5', 8001))
    tls_socket.send((PRIVATE_CA_ISSUE_URL + "\n" + SUBSCRIPTION_KEY).encode())

    while True:
        data = tls_socket.recv(1024)
        if not data:
            break
        print(f"Received Result: {data.decode()}")

client_socket.close()
print("App certificate issued.")

waiting_sec = 10
print("Waiting for " + str(waiting_sec) + " seconds.", end="", flush=True)
for _ in range(waiting_sec):
    print(".", end="", flush=True)
    time.sleep(1)
print()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
with context.wrap_socket(client_socket, server_hostname='192.168.220.6') as tls_socket:
    tls_socket.connect(('192.168.220.6', 8002))

    with open('code/tokens', 'rb') as f:
        tokens = f.read()
    tls_socket.send(str(len(tokens.decode().split("\n")) - 1).encode())
    tls_socket.send(tokens)

    while True:
        data = tls_socket.recv(1024)
        if not data:
            break
        print(f"Received: {data.decode()}")

client_socket.close()
