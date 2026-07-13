import socket
import threading
import json
import time

HOST = '127.0.0.1'
PORT = 5000  # Pintu masuk utama dari Client

NODES = {'A': 5001, 'B': 5002, 'C': 5003}
# Simulasi status jaringan: True = Terhubung, False = Putus (Partitioned)
network_status = {'A': True, 'B': True, 'C': True}

def forward_to_node(node_port, payload):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(('127.0.0.1', node_port))
        s.sendall(json.dumps(payload).encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        s.close()
        return json.loads(response)
    except:
        return {"status": "FAILED"}

def handle_client(conn, addr):
    global network_status
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data: return
        
        request = json.loads(data)
        action = request.get("action")
        target_node = request.get("target", "A") # Default ke Node A
        
        # 1. CEK KONDISI PARTISI JARINGAN (Skenario CAP)
        if not network_status[target_node]:
            # Proteksi Konsistensi (Consistency Guard) aktif
            err_msg = {
                "status": "FAILED", 
                "message": f"[ERR] Jaringan terputus ke Node_{target_node}! Mode Trade-off Aktif: Mengutamakan Konsistensi (CP). Transaksi ditolak."
            }
            conn.sendall(json.dumps(err_msg).encode('utf-8'))
            return

        if action == "READ":
            # Baca data dari target node
            res = forward_to_node(NODES[target_node], {"action": "READ"})
            conn.sendall(json.dumps(res).encode('utf-8'))
            
        elif action == "WRITE":
            new_saldo = request.get("saldo")
            payload = {"action": "WRITE", "saldo": new_saldo}
            
            print(f"\n[WRITE] Menerima request update saldo -> {new_saldo} via Node_{target_node}...")
            
            # Cek apakah semua node sehat sebelum melakukan replikasi (Prinsip CP)
            all_healthy = all(network_status.values())
            
            if all_healthy:
                # Replikasi ke semua Node secara sinkron (A, B, dan C)
                print("[SYNC] Menyebarkan pembaruan ke Node_A, Node_B, dan Node_C...")
                resA = forward_to_node(NODES['A'], payload)
                resB = forward_to_node(NODES['B'], payload)
                resC = forward_to_node(NODES['C'], payload)
                
                if resA["status"]=="SUCCESS" and resB["status"]=="SUCCESS" and resC["status"]=="SUCCESS":
                    conn.sendall(json.dumps({"status": "SUCCESS", "message": "Replikasi berhasil disinkronkan ke seluruh node."}).encode('utf-8'))
                else:
                    conn.sendall(json.dumps({"status": "FAILED", "message": "Gagal sinkronisasi data."}).encode('utf-8'))
            else:
                # Jika ada salah satu jaringan node yang drop, batalkan tulis demi Konsistensi (CP)
                conn.sendall(json.dumps({"status": "FAILED", "message": ">>> Status: Operation Failed (Consistency Guard Active)"}).encode('utf-8'))

    except Exception as e:
        print(f"[GATEWAY ERROR]: {e}")
    finally:
        conn.close()

# Terminal interaktif untuk mensimulasikan Network Partition secara manual saat presentasi
def CLI_control():
    global network_status
    time.sleep(2)
    print("\n" + "="*46)
    print("=== CONTROL PANEL SIMULASI CAP KELOMPOK 4 ===")
    print("Ketik 'putus' untuk mensimulasikan Jaringan Terputus (Partisi)")
    print("Ketik 'sambung' untuk menormalkan kembali jaringan")
    print("="*46 + "\n")
    while True:
        cmd = input().strip().lower()
        if cmd == "putus":
            network_status['C'] = False
            print("\n" + "-"*50)
            print("[ERR] Jaringan terputus! Terjadi Network Partition pada Node_C!")
            print("[ALERT] Gerbang pengaman mendeteksi gangguan jaringan.")
            print("-"*50 + "\n")
        elif cmd == "sambung":
            network_status['C'] = True
            print("\n[INFO] Jaringan pulih. Semua node terhubung kembali.\n")

def start_gateway():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER1 - GATEWAY] Berjalan di port {PORT}...")
    
    # Jalankan thread control panel
    threading.Thread(target=CLI_control, daemon=True).start()
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_gateway()