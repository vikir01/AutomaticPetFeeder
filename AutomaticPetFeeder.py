import BlynkLib
import RPi.GPIO as GPIO
from time import sleep

BLYNK_AUTH = 'fj4HwAQ1FMCqDW49H2DcHPyZCBO_pn-x' 

blynk = BlynkLib.Blynk(BLYNK_AUTH, server='blynk.cloud', log=print)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11,GPIO.OUT)  # Sets up pin 11 to an output (instead of an input)
p = GPIO.PWM(11, 50)     # Sets up pin 11 as a PWM pin
p.start(0)

@blynk.VIRTUAL_WRITE(0)
def my_write_handler(value):
    print('Current V0 value: {}'.format(value))
    if int(value[0]) == 1:
      p.ChangeDutyCycle(3)     # Changes the pulse width to 3 (so moves the servo)
      sleep(1)                 # Wait 1 second
      p.ChangeDutyCycle(12)    # Changes the pulse width to 12 (so moves the servo)
      sleep(1)
      p.ChangeDutyCycle(0)
      blynk.virtual_write(0, 0)
      blynk.log_event('pet_has_been_fed')


try:
  while True:
    blynk.run()
except:
  print("An exception occurred") 
  p.stop()                 # At the end of the program, stop the PWM
  GPIO.cleanup() 
