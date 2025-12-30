from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton
import customtkinter as ctk
from tkinter import messagebox, PhotoImage, Label
import os

class SeleccionModo(CTkFrame):
    def __init__(self, master, iniciar_manu, iniciar_pruebas, iniciar_auto, config):
        super().__init__(master)
        self.config = config
        self.teclado = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        self.panel_izquierdo = ctk.CTkFrame(self)
        self.panel_izquierdo.grid(row=1, column=0, sticky="n", padx=10, pady=10)

        ctk.CTkLabel(self.panel_izquierdo, text="Parámetros del proceso", font=("Arial", 18)).grid(row=0, column=0, columnspan=2, padx=(50,50),pady=5)
        #self.temp_entry = self.crear_entrada(self.panel_izquierdo, "Temperatura (°C)", 1, 0)
        #self.vel_entry = self.crear_entrada(self.panel_izquierdo, "Velocidad (mm/s)", 1, 1)
        self.long_entry = self.crear_entrada(self.panel_izquierdo, "Longitud (mm)", 1, 0)
        self.diam_entry = self.crear_entrada(self.panel_izquierdo, "Diámetro (mm)", 2, 0)

        from widgets.teclados import TecladoNumerico
        self.teclado = TecladoNumerico(self.panel_izquierdo, self)
        self.teclado.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        self.panel_derecho = ctk.CTkFrame(self)
        self.panel_derecho.grid(row=1, column=1, sticky="n", padx=5, pady=10)

        ctk.CTkLabel(self.panel_derecho, text="Taper Fibra", font=("Times New Roman", 25, "bold")).pack(pady=(5, 15))

        # Mostrar imagen dentro del panel usando PhotoImage (sin Pillow)
        imagen_path = r"C:\Users\tangi\OneDrive\Documentos\UNT\TESIS II\DESARROLLO\GUI\GUI_FiberTaperv4\assets\i3.png"
        if os.path.exists(imagen_path):
            try:
                self.tk_img = PhotoImage(file=imagen_path)
                self.tk_img = self.tk_img.subsample(2, 2)  # Descomenta si quieres escalar

                label_img = Label(master=self.panel_derecho, image=self.tk_img, bg="#242424")
                label_img.pack(pady=(0, 5))
            except Exception as e:
                ctk.CTkLabel(self.panel_derecho, text="(Error al cargar imagen)").pack(pady=(0, 5))
        else:
            ctk.CTkLabel(self.panel_derecho, text="(Imagen no encontrada)").pack(pady=(0, 5))

        botones_frame = ctk.CTkFrame(self.panel_derecho)
        ctk.CTkLabel(self.panel_derecho, text="Modos:", font=("Times New Roman", 20, "bold")).pack(pady=(10, 5))
        botones_frame.pack(pady=(0, 0))

        ctk.CTkButton(botones_frame, fg_color="#1E2BDD", hover_color="#1E2BDD", text="Manual", width=100, command=iniciar_manu).grid(row=0, column=0, padx=5, pady=10)
        ctk.CTkButton(botones_frame, fg_color="#1E2BDD", hover_color="#1E2BDD", text="Pruebas", width=100, command=iniciar_pruebas).grid(row=0, column=1, padx=5, pady=10)
        ctk.CTkButton(botones_frame, fg_color="#1E2BDD", hover_color="#1E2BDD", text="Automático", width=100, command=lambda: self.validar_y_continuar(iniciar_auto)).grid(row=0, column=2, padx=5, pady=10)

    def crear_entrada(self, frame, texto, fila, columna):
        ctk.CTkLabel(frame, text=texto).grid(row=fila*2-1, column=columna, padx=25, pady=2, sticky="w")

        rango_placeholder = {
            "Longitud (mm)": "[4 - 38]",
            "Diámetro (mm)": "[0.1 - 0.8]"
        }

        entry = ctk.CTkEntry(frame, width=140, placeholder_text=rango_placeholder.get(texto, ""))
        entry.grid(row=fila*2, column=columna, pady=2)
        entry.bind("<FocusIn>", lambda e, ent=entry: self.actualizar_teclado(ent))
        return entry

    def actualizar_teclado(self, entrada_objetivo):
        self.teclado.entrada = entrada_objetivo

    def validar_y_continuar(self, callback):
        try:
            longitud = float(self.long_entry.get())
            diametro = float(self.diam_entry.get())

            # Validar rango
            if not (4 <= longitud <= 38):
                messagebox.showerror("Error", "La longitud debe estar entre 4 y 38 mm.")
                return

            if not (0.2 <= diametro <= 1.2):
                messagebox.showerror("Error", "El diámetro debe estar entre 0.2 y 1.2 mm.")
                return

            # Si todo es válido, se guarda en la configuración
            self.config.longitud = longitud
            self.config.diametro = diametro

            print(f"Configuración almacenada: Longitud={longitud}, Diametro={diametro}")
            callback()  # Continuar con el flujo

        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numéricos válidos.")


