#include <RgbLed.h>

class BiDirectionalMotor {
  /* ***
     This class encapsulates a bi-directional variable speed DC motor using a
     dual H bridge.
   * ***/
  public:
    BiDirectionalMotor(int speed_pin, int fwd_pin, int bwd_pin, RgbLed_ *indicator_led); 
    void driveFwd(int target_speed);    
    void driveBwd(int target_speed);    
    void stop();
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
    BiDirectionalMotorWithEncoders(int speed_pin, int fwd_pin, int bwd_pin, int encoder_interrupt_number, int encoder_pin, RgbLed_ *indicator_led);
    int tick_count;
protected:
    int encoder_interrupt_number;
    int encoder_pin;
private:
    void incrementEncoderCount();
};

void interruptService() {
  // figure out how to associate with the correct motor instance later - see C++ language recommendations
}

BiDirectionalMotorWithEncoders::BiDirectionalMotorWithEncoders(int speed_pin, int fwd_pin, int bwd_pin, int encoder_interrupt_number, int encoder_pin, RgbLed_ *indicator_led)
:BiDirectionalMotor(speed_pin, fwd_pin, bwd_pin, indicator_led) {
  this->encoder_interrupt_number = encoder_interrupt_number;
  this->encoder_pin = encoder_pin;
  this->tick_count = 0;
  attachInterrupt(this->encoder_interrupt_number, interruptService, CHANGE);
}

void BiDirectionalMotorWithEncoders::incrementEncoderCount() {
  this->tick_count+=1;
}

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
  right_led = new RgbLedCommonAnode(2, 3, 3);
  left_led = new RgbLedCommonAnode(4, 5, 5);

  right_motor = new BiDirectionalMotor(9, 11, 12, right_led);
  left_motor = new BiDirectionalMotor(10, 7, 8, right_led);

  delay(2000);
}

void loop() {
  left_motor->driveFwd(5);
  right_motor->driveFwd(5);
  delay(2000);  

  right_motor->driveBwd(10);
  delay(2000);  

  left_motor->driveBwd(5);
  delay(2000);  

  right_motor->driveFwd(10);
  delay(2000);  
}
