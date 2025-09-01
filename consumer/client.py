import socket
import ssl
import time
import sys

def send_sgx_command(command: str, sgx_host: str, sgx_port: int) -> bool:
    """
    Send command to SGX server and return success status
    
    Args:
        command: Command to send ('gencert' or 'process')
        sgx_host: SGX server hostname
        sgx_port: SGX server port
    
    Returns:
        bool: True if command succeeded, False otherwise
    """
    try:
        print(f"Sending '{command}' command to SGX server at {sgx_host}:{sgx_port}...")
        
        # Connect to SGX server
        sgx_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sgx_socket.settimeout(60)  # 60 second timeout
        sgx_socket.connect((sgx_host, sgx_port))
        
        # Send command
        sgx_socket.send((command + '\n').encode('utf-8'))
        
        # Receive response
        response = b''
        while True:
            try:
                data = sgx_socket.recv(1024)
                if not data:
                    break
                response += data
            except socket.timeout:
                break
        
        response_text = response.decode('utf-8').strip()
        print(f"SGX Server Response:\n{response_text}")
        
        # Check if command succeeded
        success = response_text.startswith('SUCCESS:')
        
        if success:
            print(f"✓ SGX command '{command}' completed successfully")
        else:
            print(f"✗ SGX command '{command}' failed")
        
        sgx_socket.close()

        time.sleep(3)

        return success
        
    except Exception as e:
        print(f"✗ Error communicating with SGX server: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="SGX Client Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 client.py consumer01.vddpi 8080 http://registry01.vddpi:8001/issue gencert
  python3 client.py consumer01.vddpi 8080 http://registry01.vddpi:8001/issue process token_file.txt
        """
    )
    
    parser.add_argument(
        'sgx_host',
        help='SGX server hostname'
    )
    parser.add_argument(
        'sgx_port',
        type=int,
        help='SGX server port'
    )
    parser.add_argument(
        'ca_url',
        help='Private CA URL'
    )
    parser.add_argument(
        'phase',
        choices=['gencert', 'process'],
        help='Mode to execute (gencert: certificate generation, process: data processing)'
    )
    parser.add_argument(
        'token_file',
        nargs='?',
        help='Token file path (required for process)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.phase == 'process' and not args.token_file:
        print("Error: Token file path is required for process")
        print("Usage: python3 client.py process <token_file_path>")
        sys.exit(1)
    
    # Configuration
    client_cert = 'consumer.crt'
    client_key = 'consumer.key'
    ca_cert = 'cache/RootCA.pem'
    
    SUBSCRIPTION_KEY = "1234567890abcdef1234567890abcdef"
    
    print(f"=== SGX Client Application Starting - {args.phase.upper()} ===")
    print(f"SGX Server: {args.sgx_host}:{args.sgx_port}")
    
    # SSL Context setup
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    if args.phase == 'gencert':
        execute_gencert(context, args.ca_url, SUBSCRIPTION_KEY, args.sgx_host, args.sgx_port)
    elif args.phase == 'process':
        execute_process(context, args.sgx_host, args.sgx_port, args.token_file)
    
    print(f"\n=== {args.phase.upper()} Completed ===")

def execute_gencert(context, private_ca_url: str, subscription_key: str, sgx_host: str, sgx_port: int):
    """Execute: Certificate Generation"""
    print("\n=== Certificate Generation ===")
    
    # Send 'gencert' command to SGX server before 8001 communication
    if not send_sgx_command('gencert', sgx_host, sgx_port):
        print("Failed to execute gencert command. Continuing anyway...")
    
    print("\nConnecting to certificate service on port 8001...")
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with context.wrap_socket(client_socket, server_hostname='consumer01.vddpi') as tls_socket:
            tls_socket.connect((sgx_host, 8001))
            
            # Send certificate request
            message = private_ca_url + "\n" + subscription_key
            tls_socket.send(message.encode())
            
            # Receive certificate response
            print("Waiting for certificate response...")
            while True:
                data = tls_socket.recv(1024)
                if not data:
                    break
                print(f"Received Result: {data.decode()}")
        
        client_socket.close()
        print("✓ App certificate issued successfully.")
        
    except Exception as e:
        print(f"✗ Error during certificate generation: {e}")
        sys.exit(1)

def execute_process(context, sgx_host: str, sgx_port: int, token_file: str):
    """Execute: Data Processing"""
    print("\n=== Data Processing ===")
    
    # Send 'process' command to SGX server before 8002 communication
    if not send_sgx_command('process', sgx_host, sgx_port):
        print("Failed to execute process command. Continuing anyway...")
    
    print("\nConnecting to data processing service on port 8002...")
    
    try:
        # Read token file
        try:
            with open(token_file, 'rb') as f:
                tokens = f.read()
        except FileNotFoundError:
            print(f"Error: Token file '{token_file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading token file: {e}")
            sys.exit(1)
        
        # Connect to data processing service
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with context.wrap_socket(client_socket, server_hostname=sgx_host) as tls_socket:
            tls_socket.connect((sgx_host, 8002))
            
            # Send token count and data
            token_count = str(len(tokens.decode().split("\n")) - 1)
            print(f"Sending {token_count} tokens...")
            
            tls_socket.send(token_count.encode())
            tls_socket.send(tokens)
            
            # Receive processing results
            print("Waiting for processing results...")
            while True:
                data = tls_socket.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode()}")
        
        client_socket.close()
        print("✓ Data processing completed successfully.")
        
    except Exception as e:
        print(f"✗ Error during data processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
