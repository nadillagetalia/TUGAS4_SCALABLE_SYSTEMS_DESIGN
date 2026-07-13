import socket
import threading
import json

# Konfigurasi Node A
HOST = '127.0.0.1'
PORT = 5001
PEERS = {'B': 5002, 'C': 5003}

# Database Lokal (State)
db = {"saldo": 500000}

def handle_client(conn, addr):
    global db
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return
        
        request = json.loads(data)
        action = request.get("action")
        
        if action == "READ":
            conn.sendall(json.dumps({"status": "SUCCESS", "saldo": db["saldo"]}).encode('utf-8'))
            
        elif action == "WRITE":
            db["saldo"] = request.get("saldo")
            print(f"[NODE A] Saldo berhasil diperbarui secara lokal: {db['saldo']}")
            conn.sendall(json.dumps({"status": "SUCCESS"}).encode('utf-8'))
            
    except Exception as e:
        print(f"[NODE A] Error: {e}")
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[NODE A] Berjalan di port {PORT}...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()