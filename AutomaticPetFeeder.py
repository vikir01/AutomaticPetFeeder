import BlynkLib
import RPi.GPIO as GPIO
from time import sleep, localtime
from threading import Timer

BLYNK_AUTH = 'fj4HwAQ1FMCqDW49H2DcHPyZCBO_pn-x' 

GPIO_SERVO_CONTROL_PIN = 11
GPIO_SERVO_FREQ = 50
GPIO_SERVO_OPEN = 9
GPIO_SERVO_CLOSE = 15

servoOpenTime = 1.5

TIMER_MIN_INTERVAL = 10
TIMER_MAX_INTERVAL = 60 * 60

BLYNK_OPERATION_MODE_VPIN = 0
BLYNK_MANUAL_FEED_VPIN = 1
BLYNK_MORNING_HOUR_VPIN = 2
BLYNK_EVENING_HOUR_VPIN = 3
BLYNK_FEED_RATE_VPIN = 4

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
    sleep(servoOpenTime)             
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
    
  createTimer(TIMER_MAX_INTERVAL if hasFed else TIMER_MIN_INTERVAL)
    
def createTimer(sleepTime = TIMER_MIN_INTERVAL):
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
        BLYNK_FEED_RATE_VPIN
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
    if operationMode == 'automatic':
      clearTimer()
      createTimer()

@blynk.VIRTUAL_WRITE(BLYNK_EVENING_HOUR_VPIN)
def on_evening_schedule_change(value):   
    global eveningScheduleHour
    eveningScheduleHour = int(value[0])
    if operationMode == 'automatic':
      clearTimer()
      createTimer()
    
@blynk.VIRTUAL_WRITE(BLYNK_FEED_RATE_VPIN)
def on_feed_rate_change(value):   
  global servoOpenTime
  
  servoOpenTime = int(value[0]) * 0.5
  
  print('servoOpenTime changed to {}'.format(servoOpenTime))

try:
  while True:
    blynk.run()
except:
  print("An exception occurred. Shutting down ...") 
  servoControl.stop()         
  GPIO.cleanup() 
  clearTimer()

