#include <Wire.h>
#define DEVICE_ADDRESS 0x15
#define BUFFER_LENGTH 32

int recvd_length = 0;
boolean recvd;
char recv_buffer[BUFFER_LENGTH];

void setup() {
  Wire.begin(DEVICE_ADDRESS);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  recvd = false;  
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
  Wire.write("hello "); // respond with test message of 6 bytes
}

void loop() {
  if (recvd) {
    Serial.print("recvd: ");
    Serial.println(recvd_length);
    recvd = false;
  }
}
