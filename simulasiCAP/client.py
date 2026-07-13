import socket
import json
import time

GATEWAY_PORT = 5000

def send_request(payload):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', GATEWAY_PORT))
        s.sendall(json.dumps(payload).encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        s.close()
        return json.loads(response)
    except Exception as e:
        return {"status": "FAILED", "message": f"Tidak bisa terhubung ke Gateway: {e}"}

def run_simulation():
    print("=== SIMULASI DISTRIBUTED SYSTEM KELOMPOK 4 ===")
    print("[INFO] Membuka koneksi ke Node_A, Node_B, Node_C...\n")
    time.sleep(1)

    # 1. READ AWAL (Cek Saldo di setiap node)
    print("--- 1. MEMBACA SALDO AWAL ---")
    for node in ['A', 'B', 'C']:
        res = send_request({"action": "READ", "target": node})
        print(f"[READ] Node_{node} saldo: {res.get('saldo', 'Error')}")
    
    time.sleep(2)

    # 2. WRITE (Mengubah saldo ketika jaringan normal)
    print("\n--- 2. MENULIS DATA BARU (JARINGAN NORMAL) ---")
    write_res = send_request({"action": "WRITE", "target": "A", "saldo": 650000})
    print(f"Status Gateway: {write_res.get('message')}")
    
    # Cek apakah hasil tulis masuk ke semua node
    for node in ['A', 'B', 'C']:
        res = send_request({"action": "READ", "target": node})
        print(f"[READ] Node_{node} saldo: {res.get('saldo', 'Error')}")

    print("\n" + "#"*50)
    print("PENTING: Sekarang, silakan pergi ke terminal SERVER1.PY")
    print("Ketik kata 'putus' lalu tekan Enter untuk membuat partisi jaringan.")
    print("#"*50 + "\n")
    
    input("Jika sudah mengetik 'putus' di server1, tekan [ENTER] di sini untuk lanjut simulasi penolakan...")

    # 3. WRITE SAAT PARTISI (Membuktikan Aturan CP)
    print("\n--- 3. MENCOBA MENULIS DATA SAAT TERJADI PARTISI ---")
    # Mencoba menulis ke Node C yang terisolasi atau melalui klaster bermasalah
    fail_res = send_request({"action": "WRITE", "target": "C", "saldo": 800000})
    
    if "message" in fail_res:
        print(fail_res["message"])

if __name__ == "__main__":
    run_simulation()