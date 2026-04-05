import os
import sys
import subprocess
import time
import socket
import argparse
from typing import List, Tuple

def check_port(port: int, host: str = "localhost", timeout: float = 0.5) -> bool:
    """Check if a port is open and accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False

def main():
    parser = argparse.ArgumentParser(description="Run a command alongside background servers.")
    parser.add_argument("--server", action="append", help="Server command (can be specified multiple times)")
    parser.add_argument("--port", type=int, action="append", help="Port to wait for (matches --server order)")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run once servers are ready")

    args = parser.parse_args()

    if not args.server or not args.command:
        parser.print_help()
        sys.exit(1)

    servers = args.server
    ports = args.port or []
    # If fewer ports than servers, pad with 0 (no wait)
    ports.extend([0] * (len(servers) - len(ports)))

    processes: List[subprocess.Popen] = []

    try:
        # 1. Start Servers
        for i, server_cmd in enumerate(servers):
            port = ports[i]
            print(f"[*] Starting server {i+1}: {server_cmd} ...")
            # Run in a new process group to allow clean termination
            proc = subprocess.Popen(server_cmd, shell=True, env=os.environ.copy())
            processes.append(proc)

            if port > 0:
                print(f"[*] Waiting for port {port} to become active...")
                start_time = time.time()
                while time.time() - start_time < 30: # 30s timeout
                    if check_port(port):
                        print(f"[*] Port {port} is ready!")
                        break
                    time.sleep(1)
                else:
                    print(f"[!] Warning: Port {port} did not become ready after 30s.")

        # 2. Run Command
        final_cmd = " ".join(args.command)
        if final_cmd.startswith("-- "):
            final_cmd = final_cmd[3:]

        print(f"[*] Running command: {final_cmd} ...")
        result = subprocess.run(final_cmd, shell=True)
        print(f"[*] Command exited with code: {result.returncode}")

    finally:
        # 3. Cleanup
        print("[*] Shutting down servers...")
        for proc in processes:
            if proc.poll() is None:
                # Force kill on Windows
                subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
                proc.wait()

if __name__ == "__main__":
    main()
