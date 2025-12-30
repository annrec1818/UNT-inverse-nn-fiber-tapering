# widgets/consola.py
# Visualizacion del serial de python en la GUI
import io

class TextRedirector(io.StringIO):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, message):
        self.widget.insert("end", message)
        self.widget.see("end")
