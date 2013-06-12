# RFID reader YHH522 example 

import sys
import serial

echoCmd = [0xaa, 0xbb, 0x9, 0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x9]
beepCmd = [0xaa, 0xbb, 0x3, 0x14, 0x13, 0x4]
cardIDCmd = [0xaa, 0xbb, 0x2, 0x20, 0x22]

reply = []

# for windows
s = serial.Serial("COM20", baudrate=19200)
# for linux
#s = serial.Serial("/dev/ttyUSB0", baudrate=19200)

def sendCmd(cmd):
	sys.stdout.write("Command to READER: ")
	for c in cmd:
		s.write(chr(c))
		sys.stdout.write(hex(c)+" ")
	sys.stdout.write("\n")

	sys.stdout.write("Reply from READER: ")
	reply = []
	for c in range(s.inWaiting()):
		r = s.read()
		sys.stdout.write(hex(ord(r))+" ")
		reply.append(r)
	sys.stdout.write("\n")

