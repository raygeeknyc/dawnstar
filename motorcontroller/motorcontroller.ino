#include <RgbLed.h>
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

class BiDirectionalMotor {
  /* ***
     This class encapsulates a bi-directional variable speed DC motor using a
     dual H bridge.
   * ***/
  public:
    BiDirectionalMotor(int speed_pin, int fwd_pin, int bwd_pin);
    void driveFwd(int target_speed);    
    void driveBwd(int target_speed);    
    void fullStop();
    boolean isMovingFwd();
    boolean isMovingBwd();
    int getTargetSpeed();
  protected:
    const int FWD = 1;
    const int BWD = -1;
    const int STOPPED = 0;
    RgbLed_ *led;
    int target_speed;
    int direction_;
    int fwd_pin;
    int bwd_pin;
    int speed_pin;
};

class BiDirectionalMotorWithEncoders : public BiDirectionalMotor {
public:
    BiDirectionalMotorWithEncoders(int speed_pin, int fwd_pin, int bwd_pin, int encoder_interrupt_number, int encoder_pin, void (*interrupt_service_routine)(void));
    int tick_count;
    void incrementEncoderCount();
protected:
    int encoder_interrupt_number;
    int encoder_pin;
};

BiDirectionalMotorWithEncoders::BiDirectionalMotorWithEncoders(int speed_pin, int fwd_pin, int bwd_pin, int encoder_interrupt_number, int encoder_pin, void(*interrupt_service_routine)(void))
:BiDirectionalMotor(speed_pin, fwd_pin, bwd_pin) {
  this->encoder_interrupt_number = encoder_interrupt_number;
  this->encoder_pin = encoder_pin;
  this->tick_count = 0;
  attachInterrupt(this->encoder_interrupt_number, interrupt_service_routine, CHANGE);
}

void BiDirectionalMotorWithEncoders::incrementEncoderCount() {
  this->tick_count+=1;
}

void BiDirectionalMotor::driveFwd(int target_speed) {
  this->led->setColor(Color::GREEN);
  this->direction_ = this->FWD;
  this->target_speed = target_speed;
  pinMode(this->fwd_pin, OUTPUT);
  pinMode(this->bwd_pin, OUTPUT);
  pinMode(this->speed_pin, OUTPUT);
  digitalWrite(this->fwd_pin, HIGH);
  digitalWrite(this->bwd_pin, LOW);
  analogWrite(this->speed_pin, target_speed);
}

void BiDirectionalMotor::driveBwd(int target_speed) {
  this->led->setColor(Color::RED);
  this->direction_ = this->BWD;
  this->target_speed = target_speed;
  digitalWrite(this->fwd_pin, LOW);
  digitalWrite(this->bwd_pin, HIGH);
  analogWrite(this->speed_pin, target_speed);
}

BiDirectionalMotor::BiDirectionalMotor(int speed_pin, int fwd_pin, int bwd_pin) {
  this->speed_pin = speed_pin;
  this->fwd_pin = fwd_pin;
  this->bwd_pin = bwd_pin;
  this->fullStop();
}

void BiDirectionalMotor::fullStop() {
  this->direction_ = this->STOPPED;
  this->target_speed = 0;
  this->led->setColor(Color::NONE);
  digitalWrite(this->fwd_pin, LOW);
  digitalWrite(this->bwd_pin, LOW);
  analogWrite(this->speed_pin, 0);
}

RgbLed_ *lamp_led;
BiDirectionalMotor *right_motor, *left_motor;

BiDirectionalMotorWithEncoders *right_encoded_motor, *left_encoded_motor;

void LeftMotorInterruptService() {
  if (left_encoded_motor) {
    left_encoded_motor->incrementEncoderCount();
  }
}

void RightMotorInterruptService() {
  if (right_encoded_motor) {
    right_encoded_motor->incrementEncoderCount();
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println("setup");
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  lamp_led = new RgbLedCommonAnode(3, 4, 5);

  lamp_led->setColor(Color::NONE);
  lamp_led->delayCyclingColors(1000);

  Wire.begin(DEVICE_ADDRESS);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  recvd = false;  

  right_motor = new BiDirectionalMotor(9, 11, 12);
  left_motor = new BiDirectionalMotor(10, 7, 8);
  Serial.println("/setup");
  digitalWrite(LED_PIN, LOW);
}

void receiveEvent(int msgLength)
{  
  char command = ' ';
  if (msgLength) {
    command = (char)Wire.read();
  }

  if (command == LEFT_COMMAND) {
    int low_byte = Wire.available()?Wire.read():0;
    int high_byte = Wire.available()?Wire.read():0;
    left_speed = low_byte;
    if (high_byte&0x80) {
      high_byte = 256 - high_byte;
      high_byte *= -1;
    }
    left_speed += high_byte * 256;
  } else if (command == RIGHT_COMMAND) {
    int low_byte = Wire.available()?Wire.read():0;
    int high_byte = Wire.available()?Wire.read():0;
    right_speed = low_byte;
    if (high_byte&0x80) {
      high_byte = 256 - high_byte;
      high_byte *= -1;
    }
    right_speed += high_byte * 256;
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
  }
  if (left_speed > 0) {
    left_motor->driveFwd(left_speed);
  } else if (left_speed < 0) {
    left_motor->driveBwd(-1 * left_speed);
  } else {
    left_motor->fullStop();
  }
  
  if (right_speed > 0) {
    right_motor->driveFwd(right_speed);
  } else if (right_speed < 0) {
    right_motor->driveBwd(-1 * right_speed);
  } else {
    right_motor->fullStop();
  }
  digitalWrite(LED_PIN, LOW);
}
