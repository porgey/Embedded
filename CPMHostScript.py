import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import json
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import board
from datetime import datetime

#initialise LCD
lcd_columns = 16
lcd_rows = 2
lcd_rs = digitalio.DigitalInOut(board.D17)
lcd_en = digitalio.DigitalInOut(board.D27)
lcd_d4 = digitalio.DigitalInOut(board.D22)
lcd_d5 = digitalio.DigitalInOut(board.D23)
lcd_d6 = digitalio.DigitalInOut(board.D24)
lcd_d7 = digitalio.DigitalInOut(board.D10)
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
lcd.clear()
lcd.message = "Hello World!\nCounts/sec: -.-"

#initialise MQTT
client = mqtt.Client()
connect=client.connect("broker.hivemq.com",port=1883)           #connect to hiveMQ broker, encryption not supported on this broker
#connect=client.connect("ee-estott-octo.ee.ic.ac.uk",port=1883) #encryption working previously on mosquitto broker

if connect == 0:				#ensure conection to broker is made
	print("Connected!")
while connect != 0:
	print("Not Connected!")

def on_message(client, userdata, message):	#flash LED when emergency message received
	LEDState = False
	for i in range(1,7):
		GPIO.output(LEDPin,LEDState)
		LEDState = not LEDState
		time.sleep(0.3)

client.on_message = on_message
client.subscribe("IC.embedded/Embedded/Emergency")	#subscribe to emergency message topic
client.loop_start()				                    #start loop, handles reconnects automatically

#initialise GPIO
signalPin = 4
noisePin  = 18
LEDPin = 9
GPIO.setmode(GPIO.BCM)
GPIO.setup(signalPin,GPIO.IN)
GPIO.setup(noisePin,GPIO.IN)
GPIO.setup(LEDPin,GPIO.OUT)
GPIO.output(LEDPin,GPIO.HIGH)

signCount = 0					#count for signal pulses
noiseCount = 0					#count for noise pulses
signFlag = 0					#flag for signal pulses
noiseFlag = 0					#flag for noise pulses
loopIndex = 0					#index to measure interval for noise check
runSec = 0					    #seconds elapsed running program
counts = 0					    #counts measured over sampling interval
dupCountFlag = 0				#flag to prevent duplicate counting
recordIndex = 0					#index for cpmRecord
prevTime = time.time()			#initialise starting time
secondCheck = 0					#used to check whether second has elapsed
sampleSec = 0					#seconds in CPM sampling interval
currentCpm = 0					#current counts per minute
maxSampleMins = 20				#up to maxSampleMins of data will be used in CPM average
maxSampleSecs = int(maxSampleMins*60)
recordSize = int(maxSampleSecs/5)
cpmRecord = [0] * recordSize			#track of 5-second intervals added to variable cpm

while True:                             #infinite loop

	signal = GPIO.input(signalPin)
	noise = GPIO.input(noisePin)

	if signal == 0  and signFlag == 0:	#signal is held low for approx. 100us
		signFlag = 1			        #set flag to prevent counting long pulse as multiple counts
		signCount += 1
	elif signal == 1 and signFlag == 1:	#reset flag once signal returns high
		signFlag = 0

	if noise == 1 and noiseFlag == 0:	#noise is held high for approx. 100us
		noiseFlag = 1	        		#set flag to prevent counting long pulse as multiple noise counts
		noiseCount += 1
	elif noise == 0 and noiseFlag == 1:	#reset flag once noise returns low
		noiseFlag = 0

	if loopIndex == 100:			    #loopIndex reaches 100 approx. every 200ms

		currTime = time.time()

		if noiseCount == 0:		        #if noise in last 200ms, discard signal data for this interval

			if (runSec % 5 == 0) and dupCountFlag != runSec:	#move onto next element of cpmRecord every 5 seconds

				dupCountFlag = runSec
				recordIndex += 1						#move onto next element of cpmRecord
				#print('\t\t\t\t\t{}'.format(recordIndex))
				if recordIndex >= 240:						#reset to start of cpmRecord if max sample time is reached
					recordIndex = 0

				if cpmRecord[recordIndex] > 0:
					counts -= cpmRecord[recordIndex]			#remove data from current element from counts

				cpmRecord[recordIndex] = 0					    #remove data for current element from cpmRecord

			cpmRecord[recordIndex] += signCount					#add current signCount to current cpmRecord element
			counts += signCount							        #add current signCount to counts
			#print("Current History: {}".format(cpmRecord[recordIndex]))

			secondCheck += abs(currTime-prevTime)				#check whether second has elapsed
			if secondCheck >= 1:
				secondCheck -= 1
				if sampleSec >= maxSampleSecs:					#if 20 mins has elapsed do not increment cpm time
					sampleSec = maxSampleSecs				    #20 mins is max sampling window
				else:
					sampleSec += 1						        #increment cpm window time if less than 20 mins
				runSec += 1							            #increment total time
				sendArray = [{"time":datetime.now().strftime('%H:%M:%S'), "currentCPM":currentCpm}] #array of CPM and timestamp
				payload = json.dumps({"CPMData":sendArray})		#create JSON array with counts and timestamp
				publish = client.publish("IC.embedded/Embedded/user1",payload,qos=0)     #publish payload to broker
				if publish.rc != 0:
					print(mqtt.error_string(publish.rc))        #notify if error in publishing

			sampleMins = sampleSec / 60.0						#calculate minutes elapsed
			#print(sampleMins)
			if sampleMins != 0:
				currentCpm = counts/sampleMins					#calculate current CPM
			else:
				currentCpm = 0							        #avoid division by zero
			#print("Current CPM: {}".format(counts))

		lcd_line_1 = datetime.now().strftime('%b %d  %H:%M:%S\n')               	#display current date and time
		lcd_line_2 = "Counts/min: " + str(currentCpm)                           	#display current count average
		lcd.message = lcd_line_1 + lcd_line_2                                   	#write date, time and counts to LCD

		prevTime = currTime						        		#reset all external loop variables for next iteration
		signCount = 0
		noiseCount = 0
		loopIndex = 0

	loopIndex += 1
