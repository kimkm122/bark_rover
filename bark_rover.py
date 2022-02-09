#libraries
import RPi.GPIO as GPIO
import time
import datetime
import board
import neopixel
import pygame
import random
from hx711 import HX711

#global variables
reference_unit = -1814	#Scale Calibration
trigger_distance = 50	#Distance to trigger rover in cm
pill_taken = False	#Flag to mark if pill was taken that day
clock_in = 6		#Rover's work start time
clock_out = 16		#Rover's work end time
snooze_time = 900	#Length of snooze
light_threshold = 5000	#Threshold to detect laser
weight_threshold = 13.5	#Threshold of pill low supply in grams

#GPIO setup
GPIO_TRIGGER = 18
GPIO_ECHO = 24
GPIO_LASER = 19
GPIO_LIGHT = 16
GPIO_FOOT = 25
GPIO_TAIL = 12
GPIO_SNOOZE = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(GPIO_LASER, GPIO.OUT)
GPIO.output(GPIO_LASER, GPIO.LOW)
GPIO.setup(GPIO_FOOT, GPIO.OUT)
GPIO.setup(GPIO_TAIL, GPIO.OUT)
GPIO.setup(GPIO_SNOOZE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#LED setup
pixels = neopixel.NeoPixel(board.D21, 2)

#Load Cell setup
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(reference_unit)

def rover_working():
	pill_taken = False
	#turn on light bar
	rgb = [0, 255, 0]
	set_bar_led(rgb)
	while on_the_clock():
		if pill_taken == False:
			#wait for human in range
			dist = distance()
			print("Measured Distance = %.1f cm" % dist)
			if dist <= trigger_distance:
				print ("Detected Human")
				rover_cmd("pill")
				#turn on laser
				GPIO.output(GPIO_LASER, GPIO.HIGH)
				time.sleep(1)
				#wait for pill pick up or snooze
				waiting = True
				while waiting:
					light = light_value()
					print (light)
					if light < light_threshold:
						print("Pills Picked Up")
						#reset load cell
						tare_load_cell()
						weight = get_weight()
						while weight < 1:
							weight = get_weight()
						print("Pills Returned")
						time.sleep(0.5)
						weight = get_weight()
						print("Pill weight = %.1f g" % weight)
						if weight <= weight_threshold:
							rover_cmd("almost_empty")
						else:
							rover_cmd("happy")
						waiting = False
						pill_taken = True
						rgb = [0, 0, 0]
						set_bar_led(rgb)

					snooze_state = GPIO.input(GPIO_SNOOZE)
					if snooze_state == False:
						print("Snoozed")
						rover_cmd("oops")
						time.sleep(snooze_time)
						waiting = False

		else:
			light = light_value()
			#check if pills picked up
			if light < light_threshold:
				print("Pills Picked Up - Already Took")
				rgb = [255, 0, 0]
				set_bar_led(rgb)
				rover_cmd("no_pill")
				while light < light_threshold:
					light = light_value()
					time.sleep(0.5)
				rgb = [0, 0, 0]
				set_bar_led(rgb)
				rover_cmd("happy")
				time.sleep(1)
			button_pushed = GPIO.input(GPIO_SNOOZE)
			if button_pushed == False:
				rover_rand_msg()
	GPIO.output(GPIO_LASER, GPIO.LOW)

def rover_cmd(command):
	if command == "pill":
		rgb = [0, 0, 255]
	elif command == "no_pill":
		rgb = [255, 0, 0]
	elif command == "almost_empty":
		rgb = [0, 255, 0]
	elif command == "happy":
		rgb = [175, 0, 255]
	elif command == "oops":
		rgb = [255, 255, 255]
	press_button()
	set_button_led(rgb)
	play_sound(command)
	rgb = [0, 0, 0]
	set_button_led(rgb)
	if command == "happy" or command == "oops":
		wag_tail()

def rover_rand_msg():
	rgb = [0, 0, 255]
	set_bar_led(rgb)
	rgb = [255, 255, 255]
	x = random.randint(1,3)
	print(x)
	if x == 1:
		rand_message = "woof"
	elif x == 2:
		rand_message = "boo"
	elif x == 3:
		rand_message = "happy"
	time.sleep(1)
	press_button()
	set_button_led(rgb)
	play_sound(rand_message)
	rgb = [0, 0, 0]
	set_button_led(rgb)
	wag_tail()
	set_bar_led(rgb)

def tare_load_cell():
	hx.reset()
	hx.tare()

def get_weight():
	val = hx.get_weight(5)
	return val
	hx.power_down()
	hx.power_up()
	time.sleep(0.1)

def press_button():
	pwm_foot = GPIO.PWM(GPIO_FOOT, 50)
	pwm_foot.start(2.5)
	pwm_foot.ChangeDutyCycle(10)
	time.sleep(0.25)
	pwm_foot.ChangeDutyCycle(7)
	time.sleep(0.25)

def wag_tail():
	pwm_tail = GPIO.PWM(GPIO_TAIL, 50)
	pwm_tail.start(2.5)
	x = random.randint(2,4)
	for i in range(x):
		pwm_tail.ChangeDutyCycle(2)
		time.sleep(0.25)
		pwm_tail.ChangeDutyCycle(7)
		time.sleep(0.25)

def on_the_clock():
	# rover works from start_time to end_time
	current_time = datetime.datetime.now().time()
	start_time = datetime.time(clock_in, 0)
	end_time = datetime.time(clock_out, 0)
	if current_time >= start_time and current_time < end_time:
		return True
	else:
		return False

def play_sound(sound):
	# play sound file
	pygame.mixer.init()
	pygame.mixer.music.load("/home/pi/Music/" + sound +".mp3")
	#time.sleep(0.5)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy() == True:
		continue

def light_value():
	count = 0

	# set pin for output
	GPIO.setup(GPIO_LIGHT, GPIO.OUT)
	GPIO.output(GPIO_LIGHT, GPIO.LOW)
	time.sleep(0.1)

	# change pin to input
	GPIO.setup(GPIO_LIGHT, GPIO.IN)

	# count until pin goes high
	while (GPIO.input(GPIO_LIGHT) == GPIO.LOW):
		count += 1
	return count

def set_button_led(rgb):
	pixels[0] = (rgb[0], rgb[1], rgb[2])

def set_bar_led(rgb):
	pixels[1] = (rgb[0], rgb[1], rgb[2])

def blink_led(rgb):
	# blink 3 times
	for i in range(3):
		pixels[0] = (rgb[0], rgb[1], rgb[2])
		time.sleep(0.1)
		pixels[0] = (0, 0, 0)
		time.sleep(0.1)

def distance():
	# set Trigger to HIGH
	GPIO.output(GPIO_TRIGGER, True)

	# set Trigger to LOW after 0.01ms
	time.sleep(0.00001)
	GPIO.output(GPIO_TRIGGER, False)

	StartTime = time.time()
	StopTime = time.time()

	# save StartTime
	while GPIO.input(GPIO_ECHO) == 0:
		StartTime = time.time()

	# save StopTime (arrival time)
	while GPIO.input(GPIO_ECHO) == 1:
		StopTime = time.time()

	# multiply time difference by sonic speed (34300 cm/s)
	# divide by 2 (there and back)
	TimeElapsed = StopTime - StartTime
	distance = (TimeElapsed * 34300) / 2

	return distance

if __name__ == '__main__':
	try:
		dist = distance()
		while True:
			if on_the_clock():
				rover_working()
				pill_taken = False
			else:
				button_pushed = GPIO.input(GPIO_SNOOZE)
				if button_pushed == False:
					rover_rand_msg()
				time.sleep(0.1)

	except KeyboardInterrupt:
		print ("Script stoppedy by User")
		pixels[0] = (0, 0, 0)
		GPIO.cleanup()
