from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton
from widgets.teclados import TecladoNumerico
from comunicacion.serial_com import SerialCom
from tkinter import messagebox

class ModoPruebasFrame(CTkFrame):
    def __init__(self, master, reiniciar_callback):
        super().__init__(master)
        self.reiniciar_callback = reiniciar_callback
        self.teclado = None
        self.serial = SerialCom()  

        self.grid_columnconfigure((0, 1), weight=1)
        CTkLabel(self, text="Modo Pruebas (Envío de Parámetros)", font=("Times New Roman", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        # ----------- Panel Izquierdo: Teclado Numérico y Bot-----------
        panel_izq = CTkFrame(self)
        panel_izq.grid(row=1, column=0, padx=(20, 20), pady=20, sticky="n")

        self.teclado = TecladoNumerico(panel_izq, None)
        self.teclado.pack(padx=10, pady=10)

        CTkButton(panel_izq, text="Selección de Modos", fg_color="#1E2BDD", hover_color="#1E2BDD", command=self.reiniciar_callback).pack(pady=10)

        # ----------- Panel Derecho: Entradas de Parámetros -----------
        panel_der = CTkFrame(self)
        panel_der.grid(row=1, column=1, padx=10, pady=10, sticky="n")

        CTkLabel(panel_der, text="Parámetros del Proceso:", font=("Times New Roman", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10))

        self.entries = {}

        parametros = [
            ("DO [5 - 7.5]", "Vel. Oscilación (mm/s)"),
            ("NO [8 - 9]", "N° Oscilaciones"),
            ("UE [1 - 2]", "Umbral Estiramiento"),
            ("DE [2.5 - 4]", "Vel. Estiramiento (mm/s)"),
            ("LO [12 - 18]", "Longitud Oscilación (mm)"),
            ("LE [7 - 16]", "Longitud de pasos (mm)")
        ]

        for i, (clave, texto) in enumerate(parametros):
            col = i % 2
            row = i // 2 + 1  # +1 porque la fila 0 es el título
            CTkLabel(panel_der, text=texto).grid(row=row*2-1, column=col, padx=10, pady=(0, 2), sticky="w")
            entry = CTkEntry(panel_der, width=140, placeholder_text=clave)
            entry.grid(row=row*2, column=col, padx=10, pady=(0, 8))
            entry.bind("<FocusIn>", lambda e, ent=entry: self.actualizar_teclado(ent))
            self.entries[clave] = entry

        # Botón Enviar debajo de todo, centrado
        CTkButton(panel_der, text="Enviar", width=120, command=self.enviar_parametros).grid(
            row=(len(parametros)//2 + 1) * 2, column=0, columnspan=2, pady=(10, 5)
        )

    def actualizar_teclado(self, entrada_objetivo):
        self.teclado.entrada = entrada_objetivo


    def enviar_parametros(self):
        try:
            valores = {}

            # Diccionario de rangos válidos para cada parámetro
            rangos = {
                "DO [5 - 7.5]": (5.0, 7.5),
                "NO [8 - 9]": (8, 9),
                "UE [1 - 2]": (1, 2),
                "DE [2.5 - 4]": (2.5, 4.0),
                "LO [12 - 18]": (12, 18),
                "LE [7 - 16]": (7, 16)
            }

            for clave in self.entries:
                valor_str = self.entries[clave].get()
                if not valor_str:
                    messagebox.showerror("Error", f"El campo '{clave}' está vacío.")
                    return

                try:
                    valor = float(valor_str)
                except ValueError:
                    messagebox.showerror("Error", f"El valor ingresado en '{clave}' no es numérico.")
                    return

                min_val, max_val = rangos[clave]
                if not (min_val <= valor <= max_val):
                    messagebox.showerror("Error", f"'{clave}' debe estar entre {min_val} y {max_val}.")
                    return

                valores[clave[:2]] = valor  # Extraer clave tipo 'DO', 'NO', etc.

            # Construir y enviar el comando
            comando = f"M:DO={valores['DO']},NO={int(valores['NO'])},UE={int(valores['UE'])},DE={valores['DE']},LO={valores['LO']},LE={valores['LE']}"
            print(f"Enviando: {comando}")
            self.serial.enviar_comando(comando)
            comando = "A1"
            self.serial.enviar_comando(comando)

        except Exception as e:
            print("Error inesperado:", e)
            messagebox.showerror("Error", "Ocurrió un error inesperado.")

