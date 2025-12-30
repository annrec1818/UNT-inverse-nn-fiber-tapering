# widgets/estacion_frame.py
from customtkinter import CTkFrame, CTkLabel, CTkButton

class EstacionFrame(CTkFrame):
    def __init__(self, master, texto_titulo, funcion, avanzar_callback):
        super().__init__(master)
        self.funcion = funcion
        self.avanzar_callback = avanzar_callback
        self.master = master

        CTkLabel(self, text=texto_titulo, font=("Arial", 18)).pack(pady=10)
        CTkButton(self, text="Ejecutar estación", command=self.ejecutar).pack(pady=10)
        CTkButton(self, text="Siguiente estación", command=self.avanzar_callback).pack(pady=5)

    def ejecutar(self):
        self.funcion()
        #self.master.after(1500, self.avanzar_callback)  # Espera 1.5s y pasa a la siguiente estación
