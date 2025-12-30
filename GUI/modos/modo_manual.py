from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton
from widgets.teclados import TecladoNumerico_Man
from comunicacion.serial_com import SerialCom

class ModoManualFrame(CTkFrame):
    def __init__(self, master, reiniciar_callback):
        super().__init__(master)
        self.reiniciar_callback = reiniciar_callback
        self.teclado = None
        self.serial = SerialCom(puerto="COM9")  # COM3  puerto correcto


        self.grid_columnconfigure((0, 1, 2), weight=1)
        CTkLabel(self, text="Control Manual de Actuadores", font=("Times New Roman", 20, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

        # ----------------- Panel Izquierdo: Teclado + Reiniciar -----------------
        panel_izq = CTkFrame(self)
        panel_izq.grid(row=1, column=0, padx=(5,0), pady=10, sticky="n")

        self.teclado = TecladoNumerico_Man(panel_izq, None)
        self.teclado.pack(padx=10, pady=10)

        CTkButton(panel_izq, text="Selección de Modos", fg_color="#1E2BDD", hover_color="#1E2BDD", command=self.reiniciar_callback).pack(pady=10)

        # ----------------- Panel Central: Leyenda + Entrada general -----------------
        panel_centro = CTkFrame(self)
        panel_centro.grid(row=1, column=1, padx=10, pady=10, sticky="n")

        CTkLabel(panel_centro, text="Actuadores disponibles:",font=("Times New Roman", 15, "bold")).pack(padx=(50, 50),pady=(0, 5))
        CTkLabel(panel_centro, text="M1: Motor Alimentacion\nM2: Motor Cremallera\nM3: Motor Estiramiento A\nM4: Motor Estiramiento B\nS1-3: Servos\nR1-3: Reles", justify="left").pack()
       
        CTkLabel(panel_centro, text="Comandos Manuales:",font=("Times New Roman", 15, "bold")).pack(padx=(50, 50),pady=(5, 5))
        CTkLabel(panel_centro, text="M1-M4:delay_us,pasos\nS1-S3:angulo_gradosSex\nR1-R3:ON/OFF",justify="left").pack()
        self.entrada_manual = CTkEntry(panel_centro, width=200, placeholder_text="Ej: M1:500,2000 / S1:45 / R1:ON")
        self.entrada_manual.pack(pady=2)
        self.entrada_manual.bind("<FocusIn>", lambda e: self.actualizar_teclado(self.entrada_manual))

        CTkButton(panel_centro, text="Enviar", width=100, command=self.enviar_comando_manual).pack(pady=(5, 10))

        # ----------------- Panel Derecho: Comandos Especiales -----------------
        panel_der = CTkFrame(self)
        panel_der.grid(row=1, column=2, padx=(0,10), pady=10, sticky="n")

        CTkLabel(panel_der, text="Comandos Especiales:",font=("Times New Roman", 15, "bold")).pack(padx=(50, 50),pady=(0, 5))
        CTkLabel(panel_der, text="E1: Sujetar servos\nE2: Liberar servos\nE3: Estiramiento\nE4: Empuje\nE6: Reles\nE7: Reles\nE8: Reles", justify="left").pack()

        CTkLabel(panel_der, text="\nEnviar comando especial:",font=("Times New Roman", 15, "bold")).pack(pady=(10, 2))
        self.entrada_esp = CTkEntry(panel_der, width=160, placeholder_text="Ej: E3")
        self.entrada_esp.pack(pady=2)
        self.entrada_esp.bind("<FocusIn>", lambda e: self.actualizar_teclado(self.entrada_esp))

        CTkButton(panel_der, text="Enviar", width=100, command=self.enviar_comando_especial).pack(pady=(5, 10))

    def enviar_comando_manual(self):
        comando = self.entrada_manual.get()
        print(comando)
        self.serial.enviar_comando(comando)

    def enviar_comando_especial(self):
        comando = self.entrada_esp.get()
        print(comando)
        self.serial.enviar_comando(comando)

    def actualizar_teclado(self, entrada_objetivo):
        self.teclado.entrada = entrada_objetivo
