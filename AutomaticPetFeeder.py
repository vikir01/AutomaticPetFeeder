import BlynkLib
import RPi.GPIO as GPIO
from time import sleep, localtime
from threading import Timer

BLYNK_AUTH = 'fj4HwAQ1FMCqDW49H2DcHPyZCBO_pn-x' 

GPIO_SERVO_CONTROL_PIN = 11
GPIO_SERVO_FREQ = 50
GPIO_SERVO_OPEN = 9
GPIO_SERVO_CLOSE = 15

SERVO_OPEN_TIME = 1.5

BLYNK_OPERATION_MODE_VPIN = 0
BLYNK_MANUAL_FEED_VPIN = 1
BLYNK_MORNING_HOUR_VPIN = 2
BLYNK_EVENING_HOUR_VPIN = 3

operationMode = 'manual'
morningScheduleHour = 0
eveningScheduleHour = 13
feedTimer = None

def initialize_gpio():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(GPIO_SERVO_CONTROL_PIN, GPIO.OUT) 
    servoControl = GPIO.PWM(GPIO_SERVO_CONTROL_PIN, GPIO_SERVO_FREQ) 
    servoControl.start(0)
    return servoControl

def run_feed_procedure():
    servoControl.ChangeDutyCycle(GPIO_SERVO_OPEN)   
    sleep(SERVO_OPEN_TIME)             
    servoControl.ChangeDutyCycle(GPIO_SERVO_CLOSE) 
    sleep(1)
    servoControl.ChangeDutyCycle(0)
    blynk.log_event('pet_has_been_fed')

def check_feed_schedule():
  print('Check feed schedule')
  global morningScheduleHour
  global eveningScheduleHour
  
  currTime = localtime()
  
  hasFed = False
  
  print('Check morning time {} == {}'.format(currTime.tm_hour, morningScheduleHour))
  if currTime.tm_hour == morningScheduleHour:
    print('Trigger morning feed time at {}:{}'.format(currTime.tm_hour, currTime.tm_min))
    run_feed_procedure()
    hasFed = True
    
  print('Check evening time {} == {}'.format(currTime.tm_hour, eveningScheduleHour))
  if currTime.tm_hour == eveningScheduleHour:
    print('Trigger evening feed time at {}:{}'.format(currTime.tm_hour, currTime.tm_min))
    run_feed_procedure()
    hasFed = True
    
  createTimer(60 * 60 if hasFed else 5)
    

def createTimer(sleepTime = 5):
  print('Create feed timer in {} seconds'.format(sleepTime))
  global feedTimer
  
  feedTimer = Timer(sleepTime, check_feed_schedule)
  feedTimer.start()
    
def clearTimer():
    print('Clear feed timer')
    global feedTimer
    
    if feedTimer is not None:
      feedTimer.cancel()
      feedTimer = None
    
servoControl = initialize_gpio()
blynk = BlynkLib.Blynk(BLYNK_AUTH, server='blynk.cloud', log=print)

@blynk.ON("connected")
def blynk_connected():
    print("Syncing virtual pin values from cloud...")
    blynk.sync_virtual(
        BLYNK_OPERATION_MODE_VPIN,
        BLYNK_MORNING_HOUR_VPIN,
        BLYNK_EVENING_HOUR_VPIN,
    )

# Tells Blynk to call the below function when a new value is written for this virtul pin
@blynk.VIRTUAL_WRITE(BLYNK_OPERATION_MODE_VPIN)
def on_operation_mode_change(value):
  global operationMode

  if int(value[0]) == 1:
    operationMode = 'automatic'
    createTimer()
  else:
    operationMode = 'manual'
    clearTimer()
      
  print('Operation mode changed to {}'.format(operationMode))

@blynk.VIRTUAL_WRITE(BLYNK_MANUAL_FEED_VPIN)
def on_manual_feed(value): 
    if int(value[0]) == 1 and operationMode == 'manual':
        print('Performing manual feed...')
        run_feed_procedure()
        
@blynk.VIRTUAL_WRITE(BLYNK_MORNING_HOUR_VPIN)
def on_morning_schedule_change(value):   
    global morningScheduleHour
    morningScheduleHour = int(value[0])
    clearTimer()
    createTimer()

@blynk.VIRTUAL_WRITE(BLYNK_EVENING_HOUR_VPIN)
def on_evening_schedule_change(value):   
    global eveningScheduleHour
    eveningScheduleHour = int(value[0])
    clearTimer()
    createTimer()

# async def main():
try:
  while True:
    blynk.run()
except err:
  print("An exception occurred. Shutting down ...") 
  print(err)
  servoControl.stop()         
  GPIO.cleanup() 

# if __name__ == "__main__":
    # asyncio.run(main())
