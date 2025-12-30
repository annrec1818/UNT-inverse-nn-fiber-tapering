import serial
import threading
import time

class SerialCom:
    _instancia = None  # Instancia única (Singleton)
    _puerto_abierto = None

    def __new__(cls, puerto="COM9", baudrate=9600, timeout=1):
        """Evita crear múltiples conexiones al mismo puerto."""
        if cls._instancia is None:
            cls._instancia = super(SerialCom, cls).__new__(cls)
        return cls._instancia

    def __init__(self, puerto="COM9", baudrate=9600, timeout=1):
        # Solo inicializar si el puerto no está abierto
        if SerialCom._puerto_abierto != puerto:
            try:
                self.ser = serial.Serial(puerto, baudrate=baudrate, timeout=timeout)
                time.sleep(2)  # Esperar que Arduino se reinicie
                self.lock = threading.Lock()
                SerialCom._puerto_abierto = puerto
                print(f"[Serial] Conectado a {puerto}")
            except Exception as e:
                print(f"[Serial] Error de conexión: {e}")
                self.ser = None
        else:
            print(f"[Serial] Conectado a {puerto}")

    def enviar_comando(self, comando):
        if self.ser and self.ser.is_open:
            try:
                with self.lock:
                    comando_limpio = comando.strip() + "\n"
                    self.ser.write(comando_limpio.encode('utf-8'))
                    print(f"[Serial] Enviado: {comando.strip()}")

                    time.sleep(0.1)
                    while self.ser.in_waiting > 0:
                        respuesta = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        print(f"[Arduino] {respuesta}")

            except Exception as e:
                print(f"[Serial] Error al enviar: {e}")
        else:
            print("[Serial] Puerto no abierto.")

    def cerrar(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[Serial] Puerto {SerialCom._puerto_abierto} cerrado.")
            SerialCom._puerto_abierto = None
