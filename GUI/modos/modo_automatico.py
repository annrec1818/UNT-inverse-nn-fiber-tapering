from comunicacion.serial_com import SerialCom
import tensorflow as tf
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler

model = tf.keras.models.load_model(r'C:\Users\tangi\OneDrive\Documentos\UNT\TESIS II\DESARROLLO\GUI\GUI_FiberTaperv4\modos\inverse_nn_fijo.keras') #cargar la red neuronal

# En tu caso, carga los .pkl generados desde el notebook:
scaler_X_inv = joblib.load(
    r'C:\Users\tangi\OneDrive\Documentos\UNT\TESIS II\DESARROLLO\GUI\GUI_FiberTaperv4\modos\scaler_X_inv_fijo.pkl'
)
scaler_y_inv = joblib.load(
    r'C:\Users\tangi\OneDrive\Documentos\UNT\TESIS II\DESARROLLO\GUI\GUI_FiberTaperv4\modos\scaler_y_inv_fijo.pkl'
)


class ModoAutomatico:
    
    def __init__(self, master, reiniciar_callback):
        self.master = master
        self.reiniciar_callback = reiniciar_callback
        self.teclado = None
        self.serial = SerialCom()  # Reutiliza el puerto existente

    def ejecutar(self, longitud, diametro):
        
        #Prepara entrada y normaliza
        y_d = np.array([[longitud, diametro]])
        y_d_scaled = scaler_X_inv.transform(y_d)
        
        #Predicción de la red inversa
        u_scaled = model.predict(y_d_scaled)
        
        #Revertir la normalización
        u = scaler_y_inv.inverse_transform(u_scaled)[0]
        
        #Desepaquetar variables
        #DO, NO, UE, DE, LO, LE = u  #RNI con 6 salidas
        
        DE, LE = u   #RNI con 2 salidas
        
        u = model.predict(y_d)
        u = u.flatten()
        
        comando = f"M:DO={6.5},NO={int(8)},UE={int(2)},DE={DE:.3f},LO={15},LE={LE:.3f}"   #para RNNI con solo 2 salidas
        #comando = f"M:DO={DO:.3f},NO={int(NO)},UE={int(UE)},DE={DE:.3f},LO={LO:.3f},LE={LE:.3f}"       #RNI con 6 salidas
        #comando = f"M:DO={u[0]},NO={int(u[1])},UE={int(u[2])},DE={u[3]},LO={u[4]},LE={u[5]}"
        print(f"Enviando: {comando}")
        self.serial.enviar_comando(comando)
        self.serial.enviar_comando("A1")
        return comando
