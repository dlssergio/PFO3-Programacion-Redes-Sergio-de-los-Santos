import socket
import threading
import queue
import time
import sys

HOST = 'localhost'
PORT = 5000
NUM_WORKERS = 3

# Cola de mensajes segura para hilos (simula RabbitMQ)
cola_tareas = queue.Queue()

def worker(id_worker):
    # Hilo worker que toma tareas de la cola y las procesa
    while True:
        cliente_sock, direccion, tarea = cola_tareas.get()
        
        if tarea is None:
            cola_tareas.task_done()
            break
            
        print(f"[Worker {id_worker}] Procesando tarea de {direccion}: '{tarea}'")
        
        # Simulamos el tiempo de procesamiento y guardado en almacenamiento distribuido
        time.sleep(2)
        
        respuesta = f"Resultado procesado por Worker {id_worker}: '{tarea.upper()}' [Guardado en DB/S3]"
        
        try:
            cliente_sock.sendall(respuesta.encode('utf-8'))
        except socket.error as e:
            print(f"[Worker {id_worker}] Error al enviar respuesta a {direccion}: {e}")
        finally:
            cola_tareas.task_done()

def manejar_cliente(cliente_sock, direccion):
    # Recibe múltiples tareas de un cliente y las encola para los workers
    print(f"[+] Conexión establecida desde {direccion[0]}:{direccion[1]}")
    try:
        while True:
            datos = cliente_sock.recv(1024).decode('utf-8')
            
            if not datos or datos.strip().lower() == 'salir':
                print(f"[-] Cliente {direccion[0]}:{direccion[1]} desconectado.")
                break
                
            print(f"[Balanceador/Servidor] Tarea recibida de {direccion[1]} -> Enviando a cola RabbitMQ")
            # Encolamos la tarea junto con el socket del cliente para que el worker le responda
            cola_tareas.put((cliente_sock, direccion, datos))
            
    except ConnectionResetError:
        print(f"[-] Conexión cerrada abruptamente por {direccion}")
    except socket.error as e:
        print(f"[!] Error con el cliente {direccion}: {e}")
    finally:
        # Esperamos un instante antes de cerrar por si quedó alguna tarea procesándose
        time.sleep(2.5)
        cliente_sock.close()

def iniciar_servidor():
    # Inicializar el pool de workers
    for i in range(1, NUM_WORKERS + 1):
        hilo_worker = threading.Thread(target=worker, args=(i,), daemon=True)
        hilo_worker.start()
    print(f"[*] Pool de {NUM_WORKERS} workers iniciado y esperando tareas...")

    # Configurar el socket TCP principal
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Timeout de 1 segundo para que Windows permita detectar el Ctrl + C en accept()
    servidor.settimeout(1.0)

    try:
        servidor.bind((HOST, PORT))
        servidor.listen(5)
        print(f"[*] Servidor distribuido escuchando en {HOST}:{PORT}...")
        print("[*] Presiona Ctrl + C para detener el servidor.\n")
        
        while True:
            try:
                cliente_sock, direccion = servidor.accept()
                # El socket del cliente no debe heredar el timeout de 1 segundo
                cliente_sock.settimeout(None)
                
                # Crear un hilo para atender la conexión entrante sin bloquear a otros clientes
                hilo_cliente = threading.Thread(target=manejar_cliente, args=(cliente_sock, direccion), daemon=True)
                hilo_cliente.start()
            except socket.timeout:
                # Si pasa 1 segundo sin conexiones, vuelve al inicio del bucle (permite leer Ctrl+C)
                continue
                
    except KeyboardInterrupt:
        print("\n[!] Apagando servidor de forma segura...")
    except socket.error as e:
        print(f"Error en el socket del servidor: {e}")
    finally:
        servidor.close()
        sys.exit(0)

if __name__ == "__main__":
    iniciar_servidor()