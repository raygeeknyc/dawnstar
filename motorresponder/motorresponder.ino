#include <Wire.h>
#define DEVICE_ADDRESS 0x15
#define BUFFER_LENGTH 32

#define LED_PIN 13

int recvd_length = 0;
boolean recvd;
char recv_buffer[BUFFER_LENGTH];

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  Serial.begin(9600);
  Serial.println("setup");
  Wire.begin(DEVICE_ADDRESS);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  recvd = false;  
  delay(100);
  digitalWrite(LED_PIN, LOW);
  Serial.println("/setup");
}

void receiveEvent(int msgLength)
{
  if (! recvd) {
  recvd_length = msgLength;
  for (int i=0; i<min(recvd_length, BUFFER_LENGTH); i++) {
    recv_buffer[i] = (char)Wire.read();
  }
  int extra = msgLength - BUFFER_LENGTH;
  while (extra-- > 0) {
    Wire.read();
  }
  recvd = true;
  }
}

void requestEvent()
{
  Wire.write(recv_buffer);
}

void loop() {
  if (recvd) {
    digitalWrite(LED_PIN, HIGH);
    Serial.print("recvd: ");
    Serial.println(recvd_length);
    recvd = false;
    delay(100);
    digitalWrite(LED_PIN, LOW);
  }
}
