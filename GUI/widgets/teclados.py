from customtkinter import CTkFrame, CTkButton
import customtkinter as ctk

# ================== TECLADO NUMÉRICO PRINCIPAL ==================
class TecladoNumerico(ctk.CTkFrame):
    def __init__(self, master, entrada_objetivo):
        super().__init__(master)
        self.entrada = entrada_objetivo
        self.crear_teclado()

    def crear_teclado(self):
        teclas = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['0', '.', '←']  # Flecha para borrar
        ]
        for fila_idx, fila in enumerate(teclas):
            for col_idx, tecla in enumerate(fila):
                if tecla == '←':
                    btn = CTkButton(self, fg_color="#C23333", hover_color="#990000", text=tecla,
                                    width=40, height=40, font=("Arial", 16, "bold"), command=self.borrar)
                else:
                    btn = CTkButton(self, fg_color="#0D8F6E", hover_color="#0F4604", text=tecla,
                                    width=40, height=40, font=("Arial", 16, "bold"), command=lambda t=tecla: self.insertar(t))
                btn.grid(row=fila_idx, column=col_idx, padx=3, pady=3)

    def insertar(self, valor):
        self.entrada.insert("end", valor)

    def borrar(self):
        actual = self.entrada.get()
        self.entrada.delete(0, "end")
        self.entrada.insert(0, actual[:-1])


# ================== TECLADO NUMÉRICO PARA MODO MANUAL ==================
class TecladoNumerico_Man(ctk.CTkFrame):
    def __init__(self, master, entrada_objetivo):
        super().__init__(master)
        self.entrada = entrada_objetivo
        self.crear_teclado()

    def crear_teclado(self):
        teclas = [
            ['7', '8', '9', 'ON'],
            ['4', '5', '6', 'OFF'],
            ['1', '2', '3', 'E'],
            ['0', '.', '←', ','],
            ['M', 'S', 'R', ':']
        ]
        for fila_idx, fila in enumerate(teclas):
            for col_idx, tecla in enumerate(fila):
                if tecla == '←':
                    btn = CTkButton(self, fg_color="#C23333", hover_color="#990000", text=tecla,
                                    width=40, height=40, font=("Arial", 13, "bold"), command=self.borrar)
                else:
                    btn = CTkButton(self, fg_color="#0D8F6E", hover_color="#0F4604", text=tecla,
                                    width=40, height=40, font=("Arial", 13, "bold"), command=lambda t=tecla: self.insertar(t))
                btn.grid(row=fila_idx, column=col_idx, padx=3, pady=3)

    def insertar(self, valor):
        self.entrada.insert("end", valor)

    def borrar(self):
        actual = self.entrada.get()
        self.entrada.delete(0, "end")
        self.entrada.insert(0, actual[:-1])
