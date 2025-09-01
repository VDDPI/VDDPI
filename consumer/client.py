#!/usr/bin/env python3
import socket
import ssl
import argparse
import os
import sys

# ===== TLS settings and constants =====
client_cert = 'consumer.crt'
client_key  = 'consumer.key'
ca_cert     = 'cache/RootCA.pem'

PRIVATE_CA_ISSUE_URL = "http://registry01.vddpi:8001/issue"
SUBSCRIPTION_KEY     = "1234567890abcdef1234567890abcdef"

SERVER_HOST = 'consumer01.vddpi'
ISSUE_PORT  = 8001   # for certificate issuance
TOKEN_PORT  = 8002   # for token-driven processing
# =====================================

def create_context() -> ssl.SSLContext:
    """Create TLS context with client certificate; keep relaxed verification (same as original)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_cert_chain(certfile=client_cert, keyfile=client_key)
    ctx.load_verify_locations(cafile=ca_cert)
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx

def tls_gencert():
    """Trigger certificate issuance over TLS (port 8001)."""
    context = create_context()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with context.wrap_socket(client_socket, server_hostname=SERVER_HOST) as tls_socket:
            tls_socket.connect((SERVER_HOST, ISSUE_PORT))
            # Send URL + newline + subscription key (protocol preserved)
            payload = f"{PRIVATE_CA_ISSUE_URL}\n{SUBSCRIPTION_KEY}"
            tls_socket.send(payload.encode())

            while True:
                data = tls_socket.recv(1024)
                if not data:
                    break
                print(f"Received Result: {data.decode()}")
        print("App certificate issued.")
    finally:
        client_socket.close()

def tls_process(path_token: str):
    """
    Send tokens over TLS (port 8002) to trigger server-side data processing.
    The server uses the information in the token file to run its processing program.
    """
    if not os.path.isfile(path_token):
        print(f"ERROR: tokens file not found: {path_token}", file=sys.stderr)
        sys.exit(2)

    with open(path_token, 'rb') as f:
        tokens = f.read()

    try:
        token_text = tokens.decode()
    except UnicodeDecodeError:
        print("ERROR: tokens file must be decodable as text (e.g., UTF-8).", file=sys.stderr)
        sys.exit(2)

    # Protocol preserved: send (line_count - 1) first, then the token content.
    lines_count = len(token_text.split("\n")) - 1

    context = create_context()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with context.wrap_socket(client_socket, server_hostname=SERVER_HOST) as tls_socket:
            tls_socket.connect((SERVER_HOST, TOKEN_PORT))
            tls_socket.send(str(lines_count).encode())
            tls_socket.send(tokens)

            while True:
                data = tls_socket.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode()}")
    finally:
        client_socket.close()

def main():
    parser = argparse.ArgumentParser(
        description="Run either certificate generation (gencert) or server-side processing (process) over TLS."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # gencert: certificate issuance only
    subparsers.add_parser("gencert", help="Generate/issue app certificate over TLS (port 8001).")

    # process: token-driven processing only
    p_process = subparsers.add_parser("process", help="Send tokens to trigger server-side processing (port 8002).")
    p_process.add_argument("path_token", help="Path to token file used by the server-side processing program.")

    args = parser.parse_args()

    if args.mode == "gencert":
        tls_gencert()
    elif args.mode == "process":
        tls_process(args.path_token)

if __name__ == "__main__":
    main()
