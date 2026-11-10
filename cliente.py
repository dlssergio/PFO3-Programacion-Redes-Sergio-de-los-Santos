import socket
import time

HOST = 'localhost'
PORT = 5000

def conectar_con_reintentos(host, puerto, intentos=3, espera=2):
    # Manejo de errores y reintentos de conexión (visto en Clase 10)
    for intento in range(intentos):
        try:
            print(f"Intentando conectar al servidor (Intento {intento + 1}/{intentos})...")
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.connect((host, puerto))
            return cliente
        except socket.error as e:
            print(f"Error de conexión: {e}")
            time.sleep(espera)
    return None

def iniciar_cliente():
    cliente = conectar_con_reintentos(HOST, PORT)
    
    if not cliente:
        print("No se pudo establecer la conexión con el servidor. Asegurate de que esté ejecutándose.")
        return

    print(f"\nConectado exitosamente a {HOST}:{PORT}")
    print("Escribí las tareas a enviar al cluster. (Escribí 'salir' para terminar)")

    with cliente:
        while True:
            tarea = input("\nNueva tarea: ")
            
            if not tarea:
                continue
                
            try:
                cliente.sendall(tarea.encode('utf-8'))
                
                if tarea.strip().lower() == 'salir':
                    print("Cerrando conexión...")
                    break
                    
                # Esperar y mostrar el resultado procesado por alguno de los workers
                respuesta = cliente.recv(1024).decode('utf-8')
                print(f"-> {respuesta}")
                
            except socket.error as e:
                print(f"Error durante la comunicación: {e}")
                break

if __name__ == "__main__":
    iniciar_cliente()