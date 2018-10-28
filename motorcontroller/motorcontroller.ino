#include <RgbLed.h>

class BiDirectionalMotor {
  public:
    BiDirectionalMotor(int speed_pin, int fwd_pin, int bwd_pin, RgbLed_ *indicator_led); 
    void driveFwd(int target_speed);    
    void driveBwd(int target_speed);    
    void stop();
    boolean isMovingFwd();
    boolean isMovingBwd();
    int getTargetSpeed();
  private:
    const int FWD = 1;
    const int BWD = -11;
    const int STOPPED = 0;
    RgbLed_ *led;
    int target_speed;
    int direction_;
    int fwd_pin;
    int bwd_pin;
    int speed_pin;
};

void BiDirectionalMotor::driveFwd(int target_speed) {
  this->led->setColor(Color::GREEN);
  this->target_speed = target_speed;
  digitalWrite(this->fwd_pin, HIGH);
  digitalWrite(this->bwd_pin, LOW);
  analogWrite(this->speed_pin, target_speed);
}

void BiDirectionalMotor::driveBwd(int target_speed) {
  this->led->setColor(Color::RED);
  this->target_speed = target_speed;
  digitalWrite(this->fwd_pin, LOW);
  digitalWrite(this->bwd_pin, HIGH);
  analogWrite(this->speed_pin, target_speed);
}

BiDirectionalMotor::BiDirectionalMotor(int speed_pin, int fwd_pin, int bwd_pin, RgbLed_ *indicator_led) {
  this->led = indicator_led;
  this->direction_ = this->STOPPED;
  this->target_speed = 0;
  this->speed_pin = speed_pin;
  this->fwd_pin = fwd_pin;
  this->bwd_pin = bwd_pin;
}

void BiDirectionalMotor::stop() {
  this->direction_ = this->STOPPED;
  this->target_speed = 0;
  this->led->setColor(Color::NONE);
  digitalWrite(this->fwd_pin, LOW);
  digitalWrite(this->bwd_pin, LOW);
  analogWrite(this->speed_pin, 0);
}

RgbLed_ *right_led, *left_led;
BiDirectionalMotor *right_motor, *left_motor;

void setup() {
  right_led = new RgbLedCommonAnode(10, 11, 11);
  left_led = new RgbLedCommonAnode(12, 13, 13);

  right_motor = new BiDirectionalMotor(3, 8, 9, right_led);
  left_motor = new BiDirectionalMotor(5, 6, 7, right_led);
}

void loop() {

}
