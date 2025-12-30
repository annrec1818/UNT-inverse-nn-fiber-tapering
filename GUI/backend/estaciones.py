from widgets.estacion_frame import EstacionFrame  

def estacion_inicializacion(sistema, alimentacion):
    sistema.iniciar()
    alimentacion.alimentar()
    alimentacion.sujetar()
    alimentacion.alinear()

def estacion_calentamiento(calentamiento, temperatura_objetivo):
    calentamiento.activar_calentador()
    calentamiento.controlar_potencia(temperatura_objetivo)
    calentamiento.medir_temperatura()

def estacion_estiramiento(estiramiento, velocidad, pasos_micro):
    estiramiento.mover_motores(velocidad, pasos_micro)

def estacion_enfriamiento(enfriamiento):
    enfriamiento.activar()

def estacion_corte(corte):
    corte.cortar()
    corte.recolectar()

def estacion_reporte(reporte, configuracion, encendido, monitoreo):
    diametro_final = monitoreo.medir_diametro()
    reporte.mostrar_estado(configuracion, encendido, diametro_final)

# ✅ AGREGA ESTA FUNCIÓN ABAJO
def crear_estaciones(master, config, avanzar_callback):
    estaciones = []

    estaciones.append(EstacionFrame(master, "Inicialización",
        lambda: estacion_inicializacion(master.sistema, master.alimentacion), avanzar_callback))

    estaciones.append(EstacionFrame(master, "Calentamiento",
        lambda: estacion_calentamiento(master.calentamiento, config.temperatura), avanzar_callback))

    estaciones.append(EstacionFrame(master, "Estiramiento",
        lambda: estacion_estiramiento(master.estiramiento, config.velocidad, pasos_micro=1000), avanzar_callback))

    estaciones.append(EstacionFrame(master, "Enfriamiento",
        lambda: estacion_enfriamiento(master.enfriamiento), avanzar_callback))

    estaciones.append(EstacionFrame(master, "Corte",
        lambda: estacion_corte(master.corte), avanzar_callback))

    estaciones.append(EstacionFrame(master, "Reporte",
        lambda: estacion_reporte(master.reporte, config, master.sistema.encendido, master.monitoreo), avanzar_callback))

    return estaciones
