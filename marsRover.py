#import RPi.GPIO as GPIO
import time
import socket
from io import BlockingIOError
from roboclaw import Roboclaw
import constants as c
from datetime import datetime as dt, timedelta as td
from time import sleep
import subprocess
import atexit
from math import *
import cmath as cm
socket.setdefaulttimeout(10)
tank_controls = True

def run_script_on_exit(): # we had i litttle bit of oooopsie so we kill :Ds meow
    subprocess.call(['/home/pi/Desktop/marsRover/KillProcess.sh'])

atexit.register(run_script_on_exit)

class Event:
	def __init__(self, duration=0):
		self.duration = td(seconds=duration)
	def run(self):
		return

class Events: # i honestly don't know, it works though
	class ActionEvent(Event):
		def __init__(self, duration=0):
			self.duration = td(seconds=duration)
	class DriveEvent(ActionEvent):
		def run(self, **kwargs):
			drive(int(kwargs['speed']))

	class ReverseEvent(ActionEvent):
		def run(self, **kwargs):
			reverse(int(kwargs['speed']))

	class TurnLeftEvent(ActionEvent):
		def run(self, **kwargs):
			if tank_controls: turn_left(int(kwargs['turning']))
			else: turn_left_steering(int(kwargs['turning']))

	class TurnRightEvent(ActionEvent):
		def run(self, **kwargs):
			if tank_controls: turn_right(int(kwargs['turning']))
			else: turn_right_steering(int(kwargs['turning']))
   
	class SteerLeftEvent(ActionEvent):
		def run(self, **kwargs):
			# print("kwargs:")
			# print(kwargs)
			"""print("*kwargs:")
			print(*kwargs)
			print("**kwargs:")
			print(**kwargs)
			print('kwargs speed')
			print(kwargs['speed'])
			print('kwargs radius')
			print(kwargs['radius']) """
			turn_left_steering(int(kwargs['speed']), int(kwargs['radius']))

	class SteerRightEvent(ActionEvent):
		def run(self, **kwargs):
			turn_left_steering(int(kwargs['speed']), int(kwargs['radius']))

	class StopEvent(Event):
		def run(self, **kwargs):
			stop()

	class SetupEvent(Event): pass
	class SetSpeedEvent(SetupEvent):
		def __init__(self, speed):
			queue.speed = speed

		def run(self):
			print(('SetSpeed', queue.speed))
			return ('speed', int(queue.speed))

	class SetTurnspeedEvent(SetupEvent):
		def __init__(self, turning):
			queue.turning = turning
			# print("Turnspeed")
			# print(queue.turning)

		def run(self):
			print(('SetTurnSpeed', queue.turning))
			return ('turning', int(queue.turning))

class Queue(list):
	def __init__(self):
		self.endtime = None
		self.speed = 126
		self.turning = 126
		self.radius = 20
		self.duration = 0
  
	def velocityandstuf(self):
		print("intit velandstuf")
		vR = int(self.radius)
		print(vR)
		v1_3 = ((sqrt(pow(vR, 2)+(12*vR)+180))/(vR+9))
		v2 = 1
		v5 = (vR-9)/(vR+9)
		v4_6 = (sqrt(pow(vR, 2)-12*vR+180)/(vR+9))

		a1_3 = degrees(atan((12)/(sqrt(pow(vR, 2)+(12*vR)+180)-6)))
		a4_6 = degrees(atan(12/(sqrt(pow(vR, 2)-12*vR+180)-6)))
		print(v1_3, v2, v5, v4_6, a1_3, a4_6)
		return v1_3, v2, v5, v4_6, a1_3, a4_6

	def append(self, event):
		event.runtime = self.endtime if self.endtime else now
		if isinstance(event, Events.ActionEvent):
			self.endtime = event.endtime = event.runtime + event.duration
		elif isinstance(event, Events.SetupEvent):
			self.endtime = event.endtime = event.runtime
		super().append(event)
		print("------------------------------------------")
		print("Current Speed: " + str(self.speed))
		print('Current Turning Speed: ' + str(self.turning))
		print('Current Turn Radius: ' + str(self.radius))
		print('Current Cmd Duration: ' + str(self.duration) + " Seconds")
		# print('PID Position: ' + roboclaw.ReadM2PositionPID(132))
		print('ENC Val: ' + roboclaw.ReadEncM2(0x84))
		print("------------------------------------------")

	def run_next(self):
		event = self.pop(0)
		if isinstance(event, Events.ActionEvent):
			event.run(**self.run_kwargs)
		elif isinstance(event, Events.SetupEvent):
			setattr(self, *event.run())

	@property
	def run_kwargs(self):
		return {'speed': self.speed, 'turning': self.turning, 'radius': self.radius}
queue = Queue()

def setup(ip=c.pi_ip):
	global inter
	global address
	global roboclaw
 
	inter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	print("Current ip: ")
	print(ip)
	inter.bind((ip, 8080))
	inter.listen(5)

	address = { # Stores the addresses of the motorcontrolors
		1: 0x80, #front motors
		2: 0x81, #mid motors
		3: 0x82, #back motors
		4: 0x83, #front steering
		5: 0x84 #back steering
	}

	print("Opening devPort")
	roboclaw = Roboclaw("/dev/tty50", 38400) #Not sure if this is a typo or not S or 5
	print(roboclaw.Open())
 
	#queue.velocityandstuf()

def drive(speed):
	print('drive')
	if not local_testing:
		roboclaw.ForwardM1(address[1], speed)
		roboclaw.ForwardM2(address[1], speed)
		roboclaw.ForwardM1(address[2], speed)
		roboclaw.ForwardM2(address[2], speed)
		roboclaw.ForwardM1(address[3], speed)
		roboclaw.ForwardM2(address[3], speed)


def reverse(speed):
	print('reverse')
	if not local_testing:
		roboclaw.BackwardM1(address[1], speed)
		roboclaw.BackwardM2(address[1], speed)
		roboclaw.BackwardM1(address[2], speed)
		roboclaw.BackwardM2(address[2], speed)
		roboclaw.BackwardM1(address[3], speed)
		roboclaw.BackwardM2(address[3], speed)

def turn_left(turning):
	print('turn left')
	if not local_testing:
		# print("Turnspeed")
		# print(turning)
		roboclaw.ForwardM2(address[1], turning)
		roboclaw.BackwardM1(address[1], turning)
		roboclaw.ForwardM2(address[2], turning)
		roboclaw.BackwardM1(address[2], turning)
		roboclaw.ForwardM2(address[3], turning)
		roboclaw.BackwardM1(address[3], turning)


def turn_left_steering(speed, radius):
	print('turn left (steering)')
	print('radius: ' + str(radius))
	print('speed: ' + str(speed))
	queue.velocityandstuf()
	if not local_testing:
		roboclaw.ForwardM1(address[4], speed)
		roboclaw.ForwardM2(address[4], speed)
		roboclaw.BackwardM1(address[5], speed)
		roboclaw.BackwardM2(address[5], speed)

def turn_right(turning):
	print('turn right')
	if not local_testing:
		# print("Turnspeed")
		# print(turning)
		roboclaw.ForwardM1(address[1], turning)
		roboclaw.BackwardM2(address[1], turning)
		roboclaw.ForwardM1(address[2], turning)
		roboclaw.BackwardM2(address[2], turning)
		roboclaw.ForwardM1(address[3], turning)
		roboclaw.BackwardM2(address[3], turning)


def turn_right_steering(speed, radius):
	print('turn right (steering)')
	print('radius: ' + str(radius))
	print('speed: ' + str(speed))
	queue.velocityandstuf()
	if not local_testing:
		roboclaw.BackwardM1(address[4], speed)
		roboclaw.BackwardM2(address[4], speed)
		roboclaw.ForwardM1(address[5], speed)
		roboclaw.ForwardM2(address[5], speed)

def stop():
	print('stop')
	if not local_testing:
		roboclaw.BackwardM1(address[1], 0)
		roboclaw.BackwardM2(address[1], 0)
		roboclaw.BackwardM1(address[2], 0)
		roboclaw.BackwardM2(address[2], 0)
		roboclaw.BackwardM1(address[3], 0)
		roboclaw.BackwardM2(address[3], 0)
		roboclaw.BackwardM1(address[4], 0)
		roboclaw.BackwardM2(address[4], 0)
		roboclaw.BackwardM1(address[5], 0)
		roboclaw.BackwardM2(address[5], 0)

queue = Queue()

def loop():
	global connection
	global now
	while True:
		try: # waits for conection
			connection = inter.accept()[0]
			connection.setblocking(0)
		except socket.timeout: print('Can\'t find a cient-side machine to connect to. Attempting to reconnect...')
		else: break
	text_controls = False
	while True:
		try:
			now = dt.now() #Updates the time on every iteration
			try: data = connection.recv(4096)
			except BlockingIOError: data = None
			if data: # decodes and manipulates the data so that we can make it usefull
				data = data.decode('utf-8').replace('&&', '&').split('&')[-2]
				text_controls = int(data[0])
				data = data[1:]
				if text_controls:
					for command in (arg.strip(' ') for arg in data.split('-')): #strips and splits the command so that it can accept arguments
						if command.find('-') == -1:
							for command1 in command.split('-'):
								# print(command[0])
								# print(command1[0])
								# print(command1)
								# print(command)
								if command1[0] == 'r':
									queue.radius = int(command1[2:])
									# print('cmdQr: ' + str(queue.radius))
									# print('cmdQd: ' + str(queue.duration))
									# print('cmdQs: ' + str(queue.speed))
									# print('cmdQt ' + str(queue.turning))
								elif command1[0] == 'd':
									queue.duration = command1[2:]
									# print('cmdQr: ' + str(queue.radius))
									# print('cmdQd: ' + str(queue.duration))
									# print('cmdQs: ' + str(queue.speed))
									# print('cmdQt ' + str(queue.turning))
								elif command1[0] == 's':
									queue.speed = command1[2:]
									# print('cmdQr: ' + str(queue.radius))
									# print('cmdQd: ' + str(queue.duration))
									# print('cmdQs: ' + str(queue.speed))
									# print('cmdQt ' + str(queue.turning))
								elif command1[0] == 't':
									queue.turning = command1[2:]
									# print('cmdQr: ' + str(queue.radius))
									# print('cmdQd: ' + str(queue.duration))
									# print('cmdQs: ' + str(queue.speed))
									# print('cmdQt ' + str(queue.turning))
										
					# print(data.split('-'))
					dataMod = [arg.strip(' ') for arg in data.split('-')]
					# print(dataMod)
					# event = (dataSingle.strip(' ') + 'Event') # makes the "event thing" form earlier
					event_type = getattr(Events, dataMod[0].replace("_", " ").title().replace(" ", "") + 'Event')
					# print(event_type)
					if dataMod[0].replace("_", " ").title().replace(" ", "") == "SetSpeed":
						event = event_type(int(queue.speed))
						# print(event)
						queue.append(event)
					elif dataMod[0].replace("_", " ").title().replace(" ", "") == "SetTurning":
						event = event_type(int(queue.turning))
						# print(event)
						queue.append(event)
					else:
						event = event_type(int(queue.duration))
						# print(event)
						queue.append(event)

				else: # if using fancy controlls it prints out speed in the terminal
					speed = int(data[4:12], 2)
					steering = int(data[12:20], 2)
					print('Speed: ' + str(speed) + ' | Steering: ' + str(steering))
					if data[0] == '1': drive(speed) # these accept data and then run drive functions
					elif data[2] == '1': reverse(speed)
					elif data[1] == '1':
						if tank_controls: turn_left(steering)
						else: turn_left_steering(steering)
					elif data[3] == '1':
						if tank_controls: turn_right(steering)
						else: turn_right_steering(steering)
					else: stop()

			if text_controls:
				if queue:
					for event in queue.copy():
						if now >= event.runtime:
							stop()
							queue.run_next()
				else:
					if queue.endtime and now >= queue.endtime:
						stop()
						queue.endtime = None
		except KeyboardInterrupt:
			close()
			return
		except Exception as e:
			print(e)

def close():
	print("Stopping")
	sleep(2)
	if 'connecton' in globals().keys(): connection.close()
	subprocess.call(['/home/pi/Desktop/marsRover/KillProcess.sh'])


if __name__ == '__main__':
	global local_testing
	local_testing = False
	#setup()
	#print(roboclaw.ReadEncM1(0x82))
	try:
		setup()
		print('Setup completed with default ip')
		# print('PID Position: ' + roboclaw.ReadM2PositionPID(132))
		#try:
		#	print(roboclaw.ReadEncM1(address[3]))
		#except:
		#	print("line not working")
	except:
		retry_query = input('Setup failed. Do you want to...\n  1. Retry with different ip\n  2. Run local testing\n  3. Exit\nResponse: ')
		while True:
			if retry_query.isdigit() and 1 <= int(retry_query) <= 4:
				retry_query = int(retry_query)
				break
			retry_query = input('Invalid response. Do you want to...\n  1. Retry with different ip\n  2. Run local testing\n  3. Exit\nResponse: ')
		if retry_query == 1:
			new_ip = input('Enter new ip address: ')
			setup(ip=new_ip)
			print('Setup completed with ip "' + new_ip + '"')
		elif retry_query == 2:
			local_testing = True
			setup(ip='localhost')
			print('Setup completed in local test environment. Running without motors')
		else: exit()
	print("Running")
	try: loop()
	except KeyboardInterrupt: close()
