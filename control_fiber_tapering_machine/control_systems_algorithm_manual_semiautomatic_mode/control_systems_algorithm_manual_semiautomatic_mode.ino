// Algoritmo de control de motores NEMA 17, arco eléctrico y Servos en modo manual y semiautomátio


#include <Servo.h>

const int NUM_MOTORES = 4;
const int NUM_SERVOS = 3;

const int stepPin[NUM_MOTORES] = {2, 5, 8, A2};
const int dirPin[NUM_MOTORES]  = {3, 6, 12, A1};
const int enPin[NUM_MOTORES]   = {4, 7, 13, A0};

const int relayPins[3] = {A3, A4, A5};
bool estadoRelay[3] = {true, true, true}; // Estado inicial apagado

const int servoPin[NUM_SERVOS] = {9, 10, 11};

const int pasoServo = 4;
const int delayTransicion = 30;

const int anguloSujecion[NUM_SERVOS]    = {25, 88 ,35}; // Personaliza aquí
const int anguloNoSujecion[NUM_SERVOS]  = {81, 24 ,124}; // Personaliza aquí
const int anguloInicial[NUM_SERVOS] = {81,24,124};

int numOscilaciones = 8;
int umbralEstiramiento = 2;
float delayEstiramiento = 2.5;  
float delayOscilacion = 5; 
int longitudOscilacion = 5; // longitud de oscilacion en mm
int longitudEstiramiento = 15; //longitud de estiramiento por ambos motores en mm

struct Motor {
  float delay_us = 1000;
  int pasosObjetivo = 0;
  int pasosDados = 0;
  bool activo = false;
  bool stepHigh = false;
  unsigned long ultimaMicros = 0;
};

struct ServoControl {
  int actual = 30;
  int objetivo = 30;
  bool enTransicion = false;
  unsigned long ultimoCambio = 0;
};

Motor motores[NUM_MOTORES];
Servo servos[NUM_SERVOS];
ServoControl servoCtrl[NUM_SERVOS];

void manejarMotores();
void manejarServos();
void manejarSerial();

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_MOTORES; i++) {
    pinMode(stepPin[i], OUTPUT);
    pinMode(dirPin[i], OUTPUT);
    pinMode(enPin[i], OUTPUT);
    digitalWrite(enPin[i], HIGH);
    digitalWrite(dirPin[i], HIGH);
    digitalWrite(stepPin[i], LOW);
  }

  for (int i = 0; i < 3; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], HIGH); // Inicialmente apagado
  }

  
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(servoPin[i]);
    servos[i].write(servoCtrl[i].actual);
  }

  for (int i = 0; i < NUM_SERVOS; i++) {
    if (servoCtrl[i].objetivo != anguloInicial[i]) {
      servoCtrl[i].objetivo = anguloInicial[i];
      servoCtrl[i].enTransicion = true;
      servoCtrl[i].ultimoCambio = millis();
    }
  }

  Serial.println("Sistema listo.");
}

void loop() {
  manejarSerial();
  manejarMotores();
  manejarServos();
}

void manejarSerial() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.replace("\r", "");
    input.trim();

    if (input.startsWith("S")) {
      int servoIndex = input.substring(1, input.indexOf(':')).toInt() - 1;
      String comando = input.substring(input.indexOf(':') + 1);
      comando.trim();
      comando.toUpperCase();

      int nuevoObjetivo = -1;

      if (comando == "S") nuevoObjetivo = anguloSujecion[servoIndex];
      else if (comando == "NS") nuevoObjetivo = anguloNoSujecion[servoIndex];
      else nuevoObjetivo = comando.toInt();

      if (servoIndex >= 0 && servoIndex < NUM_SERVOS && nuevoObjetivo >= 0) {
        if (servoCtrl[servoIndex].objetivo != nuevoObjetivo) {
          servoCtrl[servoIndex].objetivo = nuevoObjetivo;
          servoCtrl[servoIndex].enTransicion = true;
          servoCtrl[servoIndex].ultimoCambio = millis();

          Serial.print("Servo S");
          Serial.print(servoIndex + 1);
          Serial.print(" → transición a ");
          Serial.println(nuevoObjetivo);
        } else {
          Serial.print("Servo S");
          Serial.print(servoIndex + 1);
          Serial.println(" ya está en esa posición.");
        }
      } else {
        Serial.println("Error: comando de servo inválido.");
      }
    }

    else if (input == "E1") {
      for (int i = 0; i < NUM_SERVOS; i++) {
        if (servoCtrl[i].objetivo != anguloSujecion[i]) {
          servoCtrl[i].objetivo = anguloSujecion[i];
          servoCtrl[i].enTransicion = true;
          servoCtrl[i].ultimoCambio = millis();
        }
      }
      Serial.println("Ejecutando E1: sujeción de ambos servos.");
    }

    else if (input == "E2") {
      for (int i = 0; i < NUM_SERVOS; i++) {
        if (servoCtrl[i].objetivo != anguloNoSujecion[i]) {
          servoCtrl[i].objetivo = anguloNoSujecion[i];
          servoCtrl[i].enTransicion = true;
          servoCtrl[i].ultimoCambio = millis();
        }
      }
      Serial.println("Ejecutando E2: liberación de ambos servos.");
    }

    else if (input == "E3") {
      digitalWrite(dirPin[3], LOW);  // M4 estira
      digitalWrite(dirPin[0], HIGH); // M1 acompaña
    
      int motoresE3[] = {3, 0};
      for (int j = 0; j < 2; j++) {
        int i = motoresE3[j];
        motores[i].delay_us = 500;
        motores[i].pasosObjetivo = 2000;
        motores[i].pasosDados = 0;
        motores[i].activo = true;
        motores[i].stepHigh = false;
        motores[i].ultimaMicros = micros();
      }
    
      Serial.println("E3: Estiramiento → M4(DIR=LOW), M1(DIR=HIGH)");
    }

    else if (input == "E4") {
      digitalWrite(dirPin[3], HIGH); // M4 empuja
      digitalWrite(dirPin[0], LOW);  // M1 regresa

      int motoresE4[] = {3, 0};
      for (int j = 0; j < 2; j++) {
        int i = motoresE4[j];
        motores[i].delay_us = 500;
        motores[i].pasosObjetivo = 2000;
        motores[i].pasosDados = 0;
        motores[i].activo = true;
        motores[i].stepHigh = false;
        motores[i].ultimaMicros = micros();
      }

      Serial.println("E4: Empuje → M4(DIR=HIGH), M1(DIR=LOW)");
    }
        
    else if (input == "E5") {
      int oscilaciones = 40;
      bool direccion = true;

      // Activar relé A3 (arco eléctrico)
      estadoRelay[0] = true;
      digitalWrite(relayPins[0], LOW); // LOW = encendido si el relé es activo en LOW
      Serial.println("Relay A3 ENCENDIDO (Arco eléctrico activado)");

      for (int j = 0; j < oscilaciones; j++) {
        // Establece dirección para motor M2 (índice 1)
        digitalWrite(dirPin[1], direccion ? HIGH : LOW);

        // Configura el motor M2
        motores[1].delay_us = delayOscilacion;
        motores[1].pasosObjetivo = 300;
        motores[1].pasosDados = 0;
        motores[1].activo = true;
        motores[1].stepHigh = false;
        motores[1].ultimaMicros = micros();

        // Espera a que termine el movimiento
        while (motores[1].activo) {
          manejarMotores();
        }

        // Cambia dirección para la próxima oscilación
        direccion = !direccion;
      }

      // Apagar relé A3 al finalizar
      estadoRelay[0] = false;
      digitalWrite(relayPins[0], HIGH); // HIGH = apagado si el relé es activo en LOW
      Serial.println("Relay A3 APAGADO (Arco eléctrico desactivado)");

      Serial.println("E5: Oscilación del motor M2 completada.");
    }

    else if (input == "E6") {
      estadoRelay[0] = !estadoRelay[0];
      digitalWrite(relayPins[0], estadoRelay[0] ? HIGH : LOW);
      Serial.print("Relay A3 ");
      Serial.println(estadoRelay[0] ? "ENCENDIDO" : "APAGADO");
    }
    
    else if (input == "E7") {
      estadoRelay[1] = !estadoRelay[1];
      digitalWrite(relayPins[1], estadoRelay[1] ? HIGH : LOW);
      Serial.print("Relay A4 ");
      Serial.println(estadoRelay[1] ? "ENCENDIDO" : "APAGADO");
    }
    
    else if (input == "E8") {
      estadoRelay[2] = !estadoRelay[2];
      digitalWrite(relayPins[2], estadoRelay[2] ? HIGH : LOW);
      Serial.print("Relay A5 ");
      Serial.println(estadoRelay[2] ? "ENCENDIDO" : "APAGADO");
    }

    else if (input == "A1") {
      Serial.println("Iniciando modo automático A1: sujeción → oscilación → estiramiento → retiro de taper.");

      // Paso 1: Sujeción
      for (int i = 0; i < 2; i++) {
        servoCtrl[i].objetivo = anguloSujecion[i];
        servoCtrl[i].enTransicion = true;
        servoCtrl[i].ultimoCambio = millis();
      }

      // Esperar sujeción
      bool esperando = true;
      while (esperando) {
        manejarServos();
        esperando = false;
        for (int i = 0; i < 2; i++) {
          if (servoCtrl[i].enTransicion) esperando = true;
        }
      }
      Serial.println("✔ Sujeción completada.");

      // Paso 2: Activar arco
      estadoRelay[0] = true;
      digitalWrite(relayPins[0], LOW);
      Serial.println("✔ Arco eléctrico activado (Relay A3)");

      bool direccion = true;
      digitalWrite(enPin[2], HIGH); // Asegura que M3 esté apagado antes del ciclo
      bool estiramientoIniciado = false;

      for (int j = 0; j < numOscilaciones; j++) {
        digitalWrite(dirPin[1], direccion ? HIGH : LOW); // M2 dirección

        motores[1].delay_us = 2500 / delayOscilacion;
        motores[1].pasosObjetivo = longitudOscilacion * 26;
        motores[1].pasosDados = 0;
        motores[1].activo = true;
        motores[1].stepHigh = false;
        motores[1].ultimaMicros = micros();

        while (motores[1].activo) {
          manejarMotores();

          if (j >= umbralEstiramiento && !estiramientoIniciado) {
            estiramientoIniciado = true;
            Serial.println("⚙ Estiramiento iniciado con extrusora sincronizada.");

            // Dirección de estiramiento
            digitalWrite(dirPin[3], LOW);  // M4 estira
            digitalWrite(dirPin[0], HIGH); // M1 acompaña
            digitalWrite(dirPin[2], LOW); // M3 dirección de extrusión

            // M1 y M4
            int motoresEstiramiento[] = {3, 0};
            for (int i = 0; i < 2; i++) {
              int k = motoresEstiramiento[i];
              motores[k].delay_us = 2500 / delayEstiramiento;
              motores[k].pasosObjetivo = longitudEstiramiento * 200;
              motores[k].pasosDados = 0;
              motores[k].activo = true;
              motores[k].stepHigh = false;
              motores[k].ultimaMicros = micros();
            }

            // M3 (extrusora sincronizada)
            motores[2].delay_us = (2500 / delayEstiramiento) * (200.0 / 6.0); // sincronizado
            motores[2].pasosObjetivo = longitudEstiramiento * 6; // calibrado por pasos
            motores[2].pasosDados = 0;
            motores[2].activo = true;
            motores[2].stepHigh = false;
            motores[2].ultimaMicros = micros();
          }
        }

        direccion = !direccion;
      }

      // Paso 3: Apagar arco
      estadoRelay[0] = false;
      digitalWrite(relayPins[0], HIGH);
      Serial.println("✔ Arco eléctrico desactivado (Relay A3)");

      // Paso 4: Esperar finalización de M1, M3 y M4
      bool esperandoEstiramiento = true;
      while (esperandoEstiramiento) {
        manejarMotores();
        esperandoEstiramiento = false;
        if (motores[0].activo || motores[3].activo || motores[2].activo) {
          esperandoEstiramiento = true;
        }
      }
      Serial.println("✔ Estiramiento y extrusión completados.");

      // Paso 5: Enfriamiento (Relay A5 → ventilador)
      estadoRelay[2] = true;
      digitalWrite(relayPins[2], LOW);
      Serial.println("✔ Enfriamiento iniciado (Relay A5)");

      delay(4000); // tiempo de enfriamiento

      estadoRelay[2] = false;
      digitalWrite(relayPins[2], HIGH);
      Serial.println("✔ Enfriamiento terminado.");

      // Paso 6: Liberación
      for (int i = 0; i < NUM_SERVOS; i++) {
        servoCtrl[i].objetivo = anguloNoSujecion[i];
        servoCtrl[i].enTransicion = true;
        servoCtrl[i].ultimoCambio = millis();
      }

      esperando = true;
      while (esperando) {
        manejarServos();
        esperando = false;
        for (int i = 0; i < 2; i++) {
          if (servoCtrl[i].enTransicion) esperando = true;
        }
      }
      Serial.println("✔ Sujetadores liberados.");

      // Paso 7: Apagar motores M1, M2 y M4
      for (int i = 0; i < NUM_MOTORES; i++) {
        if (i != 2) {
          digitalWrite(enPin[i], HIGH);
          motores[i].activo = false;
        }
      }

      // Paso 8: Retiro de taper con extrusora (M3)
      digitalWrite(dirPin[2], HIGH); // dirección para retiro
      motores[2].delay_us = 600;
      motores[2].pasosObjetivo = 2900;
      motores[2].pasosDados = 0;
      motores[2].activo = true;
      motores[2].stepHigh = false;
      motores[2].ultimaMicros = micros();

      while (motores[2].activo) {
        manejarMotores();
      }

      //CORTE
      servoCtrl[2].objetivo = anguloSujecion[2];
      servoCtrl[2].enTransicion = true;
      servoCtrl[2].ultimoCambio = millis();
      esperando = true;
      while (esperando) {
        manejarServos();
        esperando = false;
        if (servoCtrl[2].enTransicion) esperando = true;
      }

      // Liberar servo 3
      servoCtrl[2].objetivo = anguloNoSujecion[2];
      servoCtrl[2].enTransicion = true;
      servoCtrl[2].ultimoCambio = millis();
      esperando = true;
      while (esperando) {
        manejarServos();
        esperando = false;
        if (servoCtrl[2].enTransicion) esperando = true;
      }

            // Paso 9: Retorno de estiramiento (M1 y M4 regresan)
      Serial.println(" Retornando motores de estiramiento a su posición inicial...");

      // Dirección inversa
      digitalWrite(dirPin[3], HIGH); // M4 dirección inversa
      digitalWrite(dirPin[0], LOW);  // M1 dirección inversa

      int motoresRetorno[] = {3, 0};
      for (int i = 0; i < 2; i++) {
        int k = motoresRetorno[i];
        motores[k].delay_us = 900;
        motores[k].pasosObjetivo = longitudEstiramiento * 200;
        motores[k].pasosDados = 0;
        motores[k].activo = true;
        motores[k].stepHigh = false;
        motores[k].ultimaMicros = micros();
      }

      // Esperar a que terminen de regresar
      bool esperandoRetorno = true;
      while (esperandoRetorno) {
        manejarMotores();
        esperandoRetorno = false;
        if (motores[0].activo || motores[3].activo) {
          esperandoRetorno = true;
        }
      }
      Serial.println("✔ Motores de estiramiento retornaron a su posición inicial.");
      Serial.println("Taper retirado. Modo A1 finalizado.");

    }

    else if (input.startsWith("M:")) {
      input.remove(0, 2); // elimina "M:"

      float dO = delayOscilacion;
      int nO = numOscilaciones;
      int uE = umbralEstiramiento;
      float dE = delayEstiramiento;
      int lO = longitudOscilacion;
      int lE = longitudEstiramiento;

      int idx_DO = input.indexOf("DO=");
      int idx_NO = input.indexOf("NO=");
      int idx_UE = input.indexOf("UE=");
      int idx_DE = input.indexOf("DE=");
      int idx_LO = input.indexOf("LO=");
      int idx_LE = input.indexOf("LE=");

      if (idx_DO != -1) {
        int end = input.indexOf(',', idx_DO);
        dO = input.substring(idx_DO + 3, end != -1 ? end : input.length()).toFloat();
      }

      if (idx_NO != -1) {
        int end = input.indexOf(',', idx_NO);
        nO = input.substring(idx_NO + 3, end != -1 ? end : input.length()).toInt();
      }

      if (idx_UE != -1) {
        int end = input.indexOf(',', idx_UE);
        uE = input.substring(idx_UE + 3, end != -1 ? end : input.length()).toInt();
      }

      if (idx_DE != -1) {
        int end = input.indexOf(',', idx_DE);
        dE = input.substring(idx_DE + 3, end != -1 ? end : input.length()).toFloat();
      }

      if (idx_LO != -1) {
        int end = input.indexOf(',', idx_LO);
        lO = input.substring(idx_LO + 3, end != -1 ? end : input.length()).toInt();
      }

      if (idx_LE != -1) {
        int end = input.indexOf(',', idx_LE);
        lE = input.substring(idx_LE + 3, end != -1 ? end : input.length()).toInt();
      }

      // Asignación
      delayOscilacion = dO;
      numOscilaciones = nO;
      umbralEstiramiento = uE;
      delayEstiramiento = dE;
      longitudOscilacion = lO;
      longitudEstiramiento = lE;

      Serial.println("📦 Parámetros actualizados:");
      Serial.print(" delayOscilacion = "); Serial.println(delayOscilacion);
      Serial.print(" numOscilaciones = "); Serial.println(numOscilaciones);
      Serial.print(" umbralEstiramiento = "); Serial.println(umbralEstiramiento);
      Serial.print(" delayEstiramiento = "); Serial.println(delayEstiramiento);
      Serial.print(" longitudOscilacion = "); Serial.println(longitudOscilacion);
      Serial.print(" longitudEstiramiento = "); Serial.println(longitudEstiramiento);
    }

    

    else if (input == "D") {
      Serial.println("Moviendo motor índice 2...");

      // Configura la dirección deseada
      digitalWrite(dirPin[2], HIGH); // Cambia a LOW si quieres dirección opuesta

      // Configura los parámetros del motor
      motores[2].delay_us = 900;            // Velocidad (microsegundos entre pasos)
      motores[2].pasosObjetivo = 500;       // Número de pasos (ajusta a lo que necesites)
      motores[2].pasosDados = 0;
      motores[2].activo = true;
      motores[2].stepHigh = false;
      motores[2].ultimaMicros = micros();

      // Ejecutar el movimiento de forma bloqueante
      while (motores[2].activo) {
        manejarMotores(); // Esta función debe controlar el pulso de pasos
      }

      Serial.println("Movimiento del motor 2 completado.");
    }

  }
}    

void manejarMotores() {
  unsigned long ahora = micros();

  for (int i = 0; i < NUM_MOTORES; i++) {

    if (!motores[i].activo) {
      digitalWrite(enPin[i], HIGH); // Desactiva driver si no se usa
    }

    if (motores[i].activo) {
      // Activar motor
      digitalWrite(enPin[i], LOW);

      if (ahora - motores[i].ultimaMicros >= motores[i].delay_us) {
        motores[i].ultimaMicros = ahora;

        if (motores[i].stepHigh) {
          digitalWrite(stepPin[i], LOW);
          motores[i].pasosDados++;

          if (motores[i].pasosDados >= motores[i].pasosObjetivo) {
            motores[i].activo = false;

            // Desactivar motor al finalizar
            digitalWrite(enPin[i], HIGH);

            Serial.print("Motor M");
            Serial.print(i + 1);
            Serial.println(" terminado.");
          }
        } else {
          digitalWrite(stepPin[i], HIGH);
        }

        motores[i].stepHigh = !motores[i].stepHigh;
      }
    }
  }
}

void manejarServos() {
  unsigned long ahora = millis();
  for (int i = 0; i < NUM_SERVOS; i++) {
    if (servoCtrl[i].enTransicion && (ahora - servoCtrl[i].ultimoCambio >= delayTransicion)) {
      servoCtrl[i].ultimoCambio = ahora;
      int actual = servoCtrl[i].actual;
      int objetivo = servoCtrl[i].objetivo;

      if (actual < objetivo) actual = min(actual + pasoServo, objetivo);
      else if (actual > objetivo) actual = max(actual - pasoServo, objetivo);

      servos[i].write(actual);
      servoCtrl[i].actual = actual;

      if (actual == objetivo) {
        servoCtrl[i].enTransicion = false;
        Serial.print("Servo S");
        Serial.print(i + 1);
        Serial.println(" completó transición.");
      }
    }
  }
}

