from customtkinter import CTk, CTkTextbox
from tkinter import messagebox
import tensorflow as tf
import numpy as np
import sys

from modos.seleccion_modo import SeleccionModo
from modos.modo_manual import ModoManualFrame
from modos.modo_pruebas import ModoPruebasFrame
from modos.modo_automatico import ModoAutomatico
from comunicacion.serial_com import SerialCom

from backend.sistema import (
    ConfiguracionParametros,
    Sistema,
    AlimentacionFibraAutomatica,
    CalentamientoMLX90614,
    EstiramientoMotorPAP,
    Enfriamiento,
    CorteRecepcion,
    MonitoreoDiametro,
    ReporteEstado
)
from backend.estaciones import crear_estaciones
from widgets.consola import TextRedirector



class FiberTaperApp(CTk):
    def __init__(self):
        super().__init__()
        self.title("Control de Tapers de Fibra")
        self.geometry("805x450")
        #self.serial = SerialCom(puerto="COM9") 

        self.configuracion = ConfiguracionParametros()
        self.sistema = Sistema()
        self.alimentacion = AlimentacionFibraAutomatica()
        self.calentamiento = CalentamientoMLX90614()
        self.estiramiento = EstiramientoMotorPAP()
        self.enfriamiento = Enfriamiento()
        self.corte = CorteRecepcion()
        self.monitoreo = MonitoreoDiametro()
        self.reporte = ReporteEstado()

        self.frames_estaciones = []
        self.indice_estacion_actual = 0

        self.consola_texto = CTkTextbox(self, height=60)
        self.consola_texto.pack(side="bottom", fill="x")
        sys.stdout = TextRedirector(self.consola_texto)

        self.seleccion_modo = SeleccionModo(
            self,
            iniciar_manu=self.iniciar_modo_manual,
            iniciar_pruebas=self.iniciar_modo_pruebas,  # Modo pruebas
            iniciar_auto=self.iniciar_modo_automatico,
            config=self.configuracion
        )
        self.seleccion_modo.pack(fill="both", expand=True)

    def iniciar_modo_manual(self):
        self.seleccion_modo.pack_forget()
        self.manual_frame = ModoManualFrame(self, self.reiniciar)
        self.manual_frame.pack(fill="both", expand=True)

    def iniciar_modo_pruebas(self):
        self.seleccion_modo.pack_forget()
        self.pruebas_frame = ModoPruebasFrame(self, self.reiniciar)
        self.pruebas_frame.pack(fill="both", expand=True)

    def iniciar_modo_semiautomatico(self):
        self.seleccion_modo.pack_forget()
        self.frames_estaciones = crear_estaciones(self, self.configuracion, self.avanzar_estacion)
        self.mostrar_estacion_actual()

    def mostrar_estacion_actual(self):
        self.consola_texto.delete("1.0", "end")
        for frame in self.frames_estaciones:
            frame.pack_forget()
        self.frames_estaciones[self.indice_estacion_actual].pack(fill="both", expand=True)

    def avanzar_estacion(self):
        if self.indice_estacion_actual < len(self.frames_estaciones):
            self.frames_estaciones[self.indice_estacion_actual].pack_forget()
            self.indice_estacion_actual += 1

        if self.indice_estacion_actual < len(self.frames_estaciones):
            self.mostrar_estacion_actual()
        else:
            messagebox.showinfo("Proceso completo", "Todas las estaciones fueron ejecutadas.")
            self.reiniciar()

    def iniciar_modo_automatico(self):
        try:
                     
            # 1. Leer parámetros desde config
            longitud = float(self.configuracion.longitud)
            diametro = float(self.configuracion.diametro)
            modo_auto = ModoAutomatico(self, self.reiniciar)
            comando = modo_auto.ejecutar(longitud, diametro)
            print("Comando enviado al Arduino:", comando)

        except Exception as e:
            messagebox.showerror("Error en modo automático", f"No se pudo iniciar el proceso automático:\n{str(e)}")

    def reiniciar(self):
        for frame in self.frames_estaciones:
            frame.pack_forget()
        self.frames_estaciones = []

        if hasattr(self, "manual_frame"):
            self.manual_frame.destroy()

        if hasattr(self, "pruebas_frame"):
            self.pruebas_frame.destroy()

        self.indice_estacion_actual = 0
        self.seleccion_modo.pack(fill="both", expand=True)


if __name__ == "__main__":
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")  # "light", "dark", or "system"
    ctk.set_default_color_theme("dark-blue")  # "blue", "dark-blue", or custom
    app = FiberTaperApp()
    app.mainloop()
