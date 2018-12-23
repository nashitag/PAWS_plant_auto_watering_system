import time
import os
import glob
import RPi.GPIO as GPIO
from time import sleep
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
GPIO.setmode(GPIO.BCM)

mpin = 17                                                                                       # GPIO pin for capacitor in LIGHT DEPENDENT RESISTOR circuit
tpin = 27                                                                                       # GPIO pin for LDR


GPIO.setup(13, GPIO.IN)                                                                         # GPIO pin for MOISTURE sensor
channel = 13


GPIO.setup(22, GPIO.OUT)                                                                        # GPIO pin for SERVO MOTOR
pwm=GPIO.PWM(22, 50)                                                                            # instantiate PWM instance associated with GPIO pin 
pwm.start(0)                                                                                    # start sending pulse


os.system('modprobe w1-gpio')                                                                   # execute shell command for TEMPERATURE sensor reading
os.system('modprobe w1-therm')                                                                  # execute shell command for TEMPERATURE sensor reading
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'                                                       # extract temperature reading from given file

cred = credentials.Certificate("telepotplant-firebase-adminsdk-volhf-7becc138ca.json")          # connect to firebase 
firebase_admin.initialize_app(cred, {
                              'databaseURL' : 'https://telepotplant.firebaseio.com'
                              		})                                                              

root = db.reference()
settings = root.child('settings')
temperature = root.child('temperature')
moisture = root.child('moisture')
light = root.child('light')



def getLight():                                                                                 # get reading from LDR  
    ans = 0
    cap = 0.000001                                                                              # capacitance of capacitor used in circuit
    adj = 2.130620985
    i = 0
    t = 0
    while ans == 0:
        GPIO.setup(mpin, GPIO.OUT)
        GPIO.setup(tpin, GPIO.OUT)
        GPIO.output(mpin, False)
        GPIO.output(tpin, False)
        time.sleep(0.1)
        GPIO.setup(mpin, GPIO.IN)
        time.sleep(0.1)
        GPIO.output(tpin, True)
        starttime = time.time()
        endtime = time.time()
        while (GPIO.input(mpin) == GPIO.LOW):
            endtime = time.time()
        measurer = endtime-starttime
        res = (measurer/cap)*adj
        i = i+1
        t = t+res
        if i == 10:
            t = t/i
            ans= t
            i=0
            t=0
    return ans




def read_temp_raw():                                                                            # read temperature from file storing values
    with open(device_file) as file:
        f = file.readlines()
    return f
def read_temp():                                                                                # return surrounding temperature value
    lines = read_temp_raw()                                                                     # extract temperature readings from file
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0                                                    # calculate temperature in Celsius
        #temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c                                                                           # return temperature in Celsius
def getTemp():                                                                                  # calls temperature function when needed
    return read_temp()



def getMoisture():                                                                              # get status of soil as moist or dry
    state = GPIO.input(channel)                                                                 # set input as hygrometer
    if state ==True:
        return 0                                                                                # return 0 if soil is Dry
    elif state == False:
        return 1                                                                                # return 1 if soil is Moist



def SetAngle(angle):                                                                            # initializes the angle of turn for servo motos
    duty = angle/18 +2                                                                          # duty cycle = length/period = proportion of 'on' time to the regular interval or 'period' of time
    GPIO.output(22, True)
    pwm.ChangeDutyCycle(duty)                                                                   #changes duty cycle to required angle
    sleep(1)
    GPIO.output(22, False)
    pwm.ChangeDutyCycle(duty)
def waterPlant():                                                                               # executes series of motions for servo motor to water the plant
    SetAngle(70)
    SetAngle(0)
    sleep(2)
    SetAngle(70)
 
    

"""
Function to analyse the relation of the rate of evaporation of moisture with temperature difference.
The below function constitues a state machine that oscillates between the states DRY and WET.
    If state DRY --> DRY:
        start = current time
    If state WET --> WET:
        now = current time
    If WET --> DRY:
        time_difference = now-start
    If DRY --> WET:
        now = current time

This helps us build a linear regression model.

"""
ml_start = 0
ml_now = 0
ml_state = 0

def getMoistureRelation(ml_start, ml_now, ml_state):
    snapshot_moisture = moisture.child('raw').order_by_key().limit_to_last(1).get()
    snapshot_temp = temperature.child('raw').order_by_key().limit_to_last(1).get()
    
    for k,v in snapshot_moisture.items():
        if v['moisture'] == 0:
            if ml_state == 0:
                ml_start = v['time']
                ml_now = 0
                ml_state = 0
            elif ml_state == 1:
                tDiff = ml_now - ml_start
                for k,v in snapshot_temp.items():
                    temp = v['temp']
                    wtime = v['time']
                print('pushing: temp: '+str(temp)+' , timeDiff: '+str(tDiff) )
                temperature.child('summary').push({'temp': temp, 'timeDiff': tDiff})
                temperature.child('analytics').update({0: temp, 1: wtime})                      # current temperature value to predict analytics
                ml_state = 0

        elif v['moisture'] == 1:
            ml_now = v['time']
            ml_state = 1



refresh_rate = 60*15

start = time.time()
while True:                                                                                     # loop calls the above functions at regular intervals of 30 minutes and pushes the data collected into the firebase
    now = time.time()
    if abs(start - now) > (refresh_rate):
        print(getTemp())
        print(getMoisture())
        print(getLight())
        temperature.child('raw').push({'temp': getTemp(), 'time': time.time()})
        moisture.child('raw').push({'moisture': getMoisture(), 'time': time.time()})
        light.child('raw').push({'light': getLight(), 'time': time.time()})
        getMoistureRelation(ml_start, ml_now, ml_state)

        gtmode = settings.child('greenthumbMode').get()
        if getMoisture() == 0:                                                                   # water plant if GREEN THUMB MODE is switched OFF
            if gtmode == False:
                waterPlant()

        start = time.time()
    time.sleep(60)

pwm.stop()
