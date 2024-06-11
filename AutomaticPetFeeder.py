import asyncio
import BlynkLib
import RPi.GPIO as GPIO
from time import sleep, localtime

BLYNK_AUTH = 'fj4HwAQ1FMCqDW49H2DcHPyZCBO_pn-x' 

GPIO_SERVO_CONTROL_PIN = 11
GPIO_SERVO_FREQ = 50
GPIO_SERVO_OPEN = 3
GPIO_SERVO_CLOSE = 12

BLYNK_OPERATION_MODE_VPIN = 0
BLYNK_MANUAL_FEED_VPIN = 1
BLYNK_MORNING_HOUR_VPIN = 2
BLYNK_EVENING_HOUR_VPIN = 3

operationMode = 'manual'
morningScheduleHour = 0
eveningScheduleHour = 13
morningFeedTask = None
eveningFeedTask = None

def initialize_gpio():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(GPIO_SERVO_CONTROL_PIN, GPIO.OUT) 
    servoControl = GPIO.PWM(GPIO_SERVO_CONTROL_PIN, GPIO_SERVO_FREQ) 
    servoControl.start(0)
    return servoControl

def run_feed_procedure():
    servoControl.ChangeDutyCycle(GPIO_SERVO_OPEN)   
    sleep(1)             
    servoControl.ChangeDutyCycle(GPIO_SERVO_CLOSE) 
    sleep(1)
    servoControl.ChangeDutyCycle(0)
    blynk.log_event('pet_has_been_fed')

def createTimers():
    morningFeedTask = asyncio.create_task(schedule_timer, 'morning')
    eveningFeedTask = asyncio.create_task(schedule_timer, 'evening')

async def schedule_timer(scheduleType):
    while True:
        currTime = localtime()
        targetHour = morningScheduleHour
        
        if scheduleType == 'evening':
            targetHour = eveningScheduleHour
            
        if currTime.tm_hour == targetHour:
            run_feed_procedure()
            await asyncio.sleep(60 * 60)
            
        await asyncio.sleep(60)
    
def clearTimers():
    morningFeedTask.cancel()
    morningFeedTask = None
    eveningFeedTask.cancel()
    eveningFeedTask = None
    
    
servoControl = initialize_gpio()
blynk = BlynkLib.Blynk(BLYNK_AUTH, server='blynk.cloud', log=print)

@blynk.ON("connected")
def blynk_connected():
    print("Syncing virtual pin values from cloud...")
    blynk.sync_virtual(
        BLYNK_OPERATION_MODE_VPIN,
        BLYNK_MANUAL_FEED_VPIN,
        BLYNK_MORNING_HOUR_VPIN,
        BLYNK_EVENING_HOUR_VPIN,
    )

# Tells Blynk to call the below function when a new value is written for this virtul pin
@blynk.VIRTUAL_WRITE(BLYNK_OPERATION_MODE_VPIN)
def on_operation_mode_change(value):
  if int(value[0]) == 1:
    operationMode = 'automatic'
    createTimers()
  else
    operationMode = 'manual'
    clearTimers()
      
  print('Operation mode changed to {}'.format(operationMode))

@blynk.VIRTUAL_WRITE(BLYNK_MANUAL_FEED_VPIN)
def on_manual_feed(value): 
    if int(value[0]) == 1 && operationMode == 'manual':
        print('Performing manual feed...')
        run_feed_procedure()
        
@blynk.VIRTUAL_WRITE(BLYNK_MORNING_HOUR_VPIN)
def on_morning_schedule_change(value):   
    morningScheduleHour = int(value[0])

@blynk.VIRTUAL_WRITE(BLYNK_EVENING_HOUR_VPIN)
def on_evening_schedule_change(value):   
    eveningScheduleHour = int(value[0])

#async def main():
try:
  while True:
    blynk.run()
except:
  print("An exception occurred. Shutting down ...") 
  servoControl.stop()         
  GPIO.cleanup() 

#if __name__ == "__main__":
#    asyncio.run(main())
