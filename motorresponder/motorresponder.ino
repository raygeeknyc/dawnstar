#include <Wire.h>
#define DEVICE_ADDRESS 0x15
#define BUFFER_LENGTH 32

#define LED_PIN 13

int buffer_length = 0;
boolean recvd;
char recv_buffer[BUFFER_LENGTH];
int left_speed = 0, right_speed = 0;
#define LEFT_COMMAND 'L'
#define RIGHT_COMMAND 'R'

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
  char command = ' ';
  if (msgLength) {
    command = (char)Wire.read();
  }

  if (command == LEFT_COMMAND) {
    left_speed = Wire.available()?Wire.read():0;
    left_speed += (Wire.available()?Wire.read():0) * 256;
  } else if (command == RIGHT_COMMAND) {
    right_speed = Wire.available()?Wire.read():0;
    right_speed += (Wire.available()?Wire.read():0) * 256;
  }
  while (Wire.available()) {
    Wire.read();
  }
  recvd = true;
}

void requestEvent()
{
  Wire.write(right_speed  & 0xFF);
  Wire.write((right_speed >> 8) & 0xFF);
  Wire.write(left_speed  & 0xFF);
  Wire.write((left_speed >> 8) & 0xFF);
}

void loop() {
  if (recvd) {
    digitalWrite(LED_PIN, HIGH);
    Serial.print("left: ");
    Serial.print(left_speed);
    Serial.print(" right: ");
    Serial.println(right_speed);
    recvd = false;
    delay(500);
    digitalWrite(LED_PIN, LOW);
  }
}
