// Algoritmo de control de motores NEMA 17, arco eléctrico y servos en modo automático

const int STEP_PIN = A2;
const int DIR_PIN = A1;
const int EN_PIN = A0;

void setup() {
  Serial.begin(9600);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);

  digitalWrite(EN_PIN, LOW);   // habilita driver
  digitalWrite(DIR_PIN, HIGH); // sentido por defecto

  Serial.println("Formato: delay,pasos (ej: 200,300)");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    int comaIndex = input.indexOf(',');
    if (comaIndex != -1) {
      int delay_us = input.substring(0, comaIndex).toInt();
      int pasos = input.substring(comaIndex + 1).toInt();

      if (delay_us > 0 && pasos > 0) {
        Serial.print("Moviendo ");
        Serial.print(pasos);
        Serial.print(" pasos con delay ");
        Serial.print(delay_us);
        Serial.println(" us");

        moverMotor(pasos, delay_us);
      } else {
        Serial.println("Error: valores inválidos");
      }
    } else {
      Serial.println("Formato inválido. Usa: delay,pasos");
    }

    // Limpia buffer serial
    while (Serial.available()) Serial.read();
  }
}

void moverMotor(int pasos, int delay_us) {
  for (int i = 0; i < pasos; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(delay_us);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(delay_us);
  }
}
