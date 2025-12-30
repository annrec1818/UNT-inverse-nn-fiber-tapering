# backend/sistema.py

class ConfiguracionParametros:
    def __init__(self, temperatura=0.0, velocidad=0.0, longitud=0.0, diametro=0.0):
        self.temperatura = temperatura
        self.velocidad = velocidad
        self.longitud = longitud
        self.diametro = diametro


class Sistema:
    def __init__(self):
        self.encendido = False

    def iniciar(self):
        self.encendido = True
        print("Sistema encendido")

    def detener(self):
        self.encendido = False
        print("Sistema apagado")


class AlimentacionFibraAutomatica:
    def alimentar(self):
        print("Fibra alimentada desde el carrete")

    def sujetar(self):
        print("Fibra sujeta con servos de sujeción")

    def alinear(self):
        print("Fibra alineada con eje de proceso")


class CalentamientoMLX90614:
    def activar_calentador(self):
        print("Calentador activado ")

    def medir_temperatura(self):
        temperatura_actual = 100.0
        print(f"Temperatura medida: {temperatura_actual}°C")
        return temperatura_actual

    def controlar_potencia(self, temperatura_objetivo):
        print(f"Ajustando potencia para mantener {temperatura_objetivo}°C")


class EstiramientoMotorPAP:
    def mover_motores(self, velocidad, pasos_micro):
        print(f"Estiramiento con velocidad {velocidad}, pasos {pasos_micro}")


class Enfriamiento:
    def activar(self):
        print("Enfriamiento activado")


class CorteRecepcion:
    def cortar(self):
        print("Fibra cortada")

    def recolectar(self):
        print("Fibra recolectada")


class MonitoreoDiametro:
    def medir_diametro(self):
        diametro = 50.0
        print(f"Diámetro medido: {diametro} µm")
        return diametro


class ReporteEstado:
    def mostrar_estado(self, configuracion, encendido, diametro_final):
        print("---- Estado del Sistema ----")
        print(f"Temp: {configuracion.temperatura} °C")
        print(f"Velocidad: {configuracion.velocidad} mm/s")
        print(f"Longitud: {configuracion.longitud} mm")
        print(f"Diametro objetivo: {configuracion.diametro} µm")
        print(f"Diametro final: {diametro_final} mm")
        print(f"Estado: {'Encendido' if encendido else 'Apagado'}")
        print("----------------------------")
