#!/usr/bin/env python3

import socket
import json
import logging
import argparse
import subprocess
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Tuple

class SGXCommandServer:
    def __init__(self, port: int = 8080, log_level: int = logging.INFO):
        self.port = port
        self.logger = self._setup_logger(log_level)
        self.server_socket = None
        self.start_time = time.time()
        self._setup_signal_handlers()

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """Setup logger with custom formatter"""
        logger = logging.getLogger('SGXServer')
        logger.setLevel(log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def start(self):
        """Start the SGX command server"""
        self.logger.info("=== SGX Command Server Starting ===")
        self.logger.info(f"Port: {self.port}")
        self.logger.info("Available commands: gencert, process")
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(1)
            
            self.logger.info(f"Server listening on port {self.port}")
            self.logger.info(f"Send commands via: echo 'command' | nc localhost {self.port}")
            self.logger.info("=== Server Ready ===")
            
            while True:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self._handle_client(client_socket, client_address)
                except Exception as e:
                    self.logger.error(f"Error accepting client: {e}")
                    
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self._shutdown()

    def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle individual client connection"""
        client_info = f"{client_address[0]}:{client_address[1]}"
        self.logger.info(f"Client connected: {client_info}")
        
        try:
            # Read command from client
            data = client_socket.recv(1024).decode('utf-8').strip()
            
            if not data:
                client_socket.send(b"ERROR: No command received\n")
                return
            
            self.logger.info(f"Received command from {client_info}: '{data}'")
            
            # Execute command directly
            start_time = time.time()
            command = data.lower()
            
            if command == 'gencert':
                response = self._handle_gencert()
            elif command == 'process':
                response = self._handle_process()
            else:
                self.logger.warning(f"Unknown command: '{data}'")
                response = {
                    'status': 'ERROR',
                    'message': f"ERROR: Unknown command '{data}'. Available commands: gencert, process"
                }
            
            duration = time.time() - start_time
            self.logger.info(f"Command '{command}' completed in {duration:.3f}s")
            
            # Send response
            response_text = response['message'] + '\n'
            client_socket.send(response_text.encode('utf-8'))
            self.logger.info(f"Response sent to {client_info}: {response['status']}")
            
        except Exception as e:
            error_msg = f"ERROR: {e}\n"
            client_socket.send(error_msg.encode('utf-8'))
            self.logger.error(f"Error handling client {client_info}: {e}")
        finally:
            client_socket.close()
            self.logger.info(f"Client disconnected: {client_info}")

    def _handle_gencert(self) -> Dict[str, str]:
        """Handle certificate generation command"""
        self.logger.info("Executing SGX certificate generation...")
        
        cmd = "gramine-sgx ./python -gencert"
        success, output = self._run_system_command(cmd)
        
        if success:
            return {
                'status': 'SUCCESS',
                'message': f"SUCCESS: Certificate generated successfully\n{output}"
            }
        else:
            return {
                'status': 'ERROR',
                'message': f"ERROR: Certificate generation failed\n{output}"
            }

    def _handle_process(self) -> Dict[str, str]:
        """Handle data processing command"""
        self.logger.info("Executing SGX data processing...")
        
        cmd = "gramine-sgx ./python code/main.py"
        success, output = self._run_system_command(cmd)
        
        if success:
            return {
                'status': 'SUCCESS',
                'message': f"SUCCESS: Data processing completed successfully\n{output}"
            }
        else:
            return {
                'status': 'ERROR',
                'message': f"ERROR: Data processing failed\n{output}"
            }

    def _run_system_command(self, cmd: str) -> Tuple[bool, str]:
        """Execute system command in background and return immediately"""
        self.logger.debug(f"Executing in background: {cmd}")
        
        start_time = time.time()
        try:
            # Start process in background without waiting
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            time.sleep(3)

            self.logger.info(f"Started background process (PID:{process.pid}, command:{cmd})")

            # Return immediately without waiting for completion
            return True, f"Command started in background (PID:{process.pid}, command:{cmd})"
            
        except Exception as e:
            self.logger.error(f"Failed to start background process: {e}")
            return False, f"Failed to start background process: {e}"

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name} signal")
        self._shutdown()
        sys.exit(0)

    def _shutdown(self):
        """Shutdown server gracefully"""
        self.logger.info("=== Shutting down SGX server ===")
        
        if self.server_socket:
            try:
                self.server_socket.close()
                self.logger.info("Server socket closed")
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")
        
        self.logger.info("Server shutdown complete")

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="SGX Command Server")
    parser.add_argument(
        "-p", "--port", 
        type=int, 
        default=8080,
        help="Port number (default: 8080)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    try:
        server = SGXCommandServer(port=args.port, log_level=log_level)
        server.start()
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
