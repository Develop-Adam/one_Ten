const unsigned long PERIOD_MS = 250;
unsigned long lastPrint = 0;

static int highIs0(int pin) {
  return (digitalRead(pin) == HIGH) ? 0 : 1;  // HIGH->0, LOW->1
}

void setup() {
  Serial.begin(115200);
  for (int pin = 4; pin <= 7; pin++) pinMode(pin, INPUT_PULLUP);
}

void loop() {
  if (millis() - lastPrint < PERIOD_MS) return;
  lastPrint = millis();

  // CSV pairs: pin,value,pin,value,...
  Serial.print("4,"); Serial.print(highIs0(4)); Serial.print(",");
  Serial.print("5,"); Serial.print(highIs0(5)); Serial.print(",");
  Serial.print("6,"); Serial.print(highIs0(6)); Serial.print(",");
  Serial.print("7,"); Serial.print(highIs0(7));
  Serial.println();
}
