# RFID reader YHH522 example 

import sys
import serial
from os import system
import time
import struct

keyA = [0xff] * 6

echoCmd = [0xaa, 0xbb, 0x9, 0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7]
beepCmd = [0xaa, 0xbb, 0x3, 0x14, 0x13]
cardIDCmd = [0xaa, 0xbb, 0x2, 0x20]
cardTypeCmd = [0xaa, 0xbb, 0x02, 0x19]

blockReadCmd = [
	0xaa, 0xbb, 0x0a, 0x21, 0x00, 0x00, 
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
blockWriteCmd = [
	0xaa, 0xbb, 0x1a, 0x22, 0x00, 0x08, 
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
	0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 
	0xDE, 0xAD, 0xBE, 0xFF, 0xDE, 0xAD, 0xBE, 0xFF]
valueInitCmd = [
	0xaa, 0xbb, 0x0e, 0x23, 0x00, 0x08,
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	0x00, 0x00, 0x04, 0x00]
valueReadCmd = [
	0xaa, 0xbb, 0x0a, 0x24, 0x00, 0x08,
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
valueIncCmd = [
	0xaa, 0xbb, 0x0e, 0x25, 0x00, 0x08,
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	0x00, 0x00, 0x04, 0x00]
valueDecCmd = [
	0xaa, 0xbb, 0x0e, 0x26, 0x00, 0x08,
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	0x00, 0x00, 0x04, 0x00]	

reply = []

# for windows
#s = serial.Serial("COM20", baudrate=19200)
# for linux
s = serial.Serial("/dev/ttyUSB0", baudrate=19200)



def clearVCS():
	f = open('/dev/vcs','w')
	f.write(" "*1000)
	f.close()

def dualWrite(vcs,msg):
	vcs.write(msg)
	sys.stdout.write(msg)

def sendCmd(cmd):	

	csum = 0
	
	for c in cmd:
		s.write(chr(c))
		csum = csum ^ c
	csum = csum ^ 0xaa ^ 0xbb
	s.write(chr(csum))

	reply = []
	

	time.sleep(0.1)
	prevTime = time.time()
	while(s.inWaiting() < 1) :
		if(time.time() - prevTime > 1):
			print "Timeout"
			return
	
	csum = 0
	while(s.inWaiting() > 0):
		r = s.read()
		reply.append(r)
		csum = csum ^ ord(r)
	
	csum = csum ^ 0xaa ^ 0xbb 
	
	if(csum != 0):
		print "Checksum incorrect"
	
	return reply

def check(response):
	if(len(response) < 4):
		print "Invalid response"
		return False
	csum = 0

	for c in response[2:]:
		csum = csum ^ ord(c)
	if(csum != 0):
		return False
	return True


def sendCmdD(cmd):
	clearVCS()
	f = open('/dev/vcs','w')
	dualWrite(f, "Command to READER: ")
	
	csum = 0
	
	for c in cmd:
		s.write(chr(c))
		csum = csum ^ c
		dualWrite(f, hex(c) + " ")
	csum = csum ^ 0xaa ^ 0xbb
	s.write(chr(csum))
	dualWrite(f, hex(csum) + "\n")



	dualWrite(f, "Reply from READER: ")
	reply = []
	

	time.sleep(0.1)
	prevTime = time.time()
	while(s.inWaiting() < 1) :
		if(time.time() - prevTime > 1):
			dualWrite("Response timed out\n")
			f.close()
			return
	
	while(s.inWaiting() > 0):
		r = s.read()
		dualWrite(f, hex(ord(r)) + " ")
		reply.append(r)
	dualWrite(f, "\n")
	f.close()
	
def flush():
	reply = []
	for c in range(s.inWaiting()):
		r = s.read()
		reply.append(r)
	
	print [hex(ord(c)) for c in reply]

def readBlock(blockNum):
	clearVCS()
	f = open('/dev/vcs','w')
	dualWrite(f, "Read block " + hex(blockNum) + "\n")
	
	csum = 0
	

	cmd =  blockReadCmd[0:5] + [blockNum] + blockReadCmd[6:12]
	reply = sendCmd(cmd)
	
	if(not check(reply)):
		dualWrite(f, "Checksum Incorrect")
	elif(ord(reply[2]) == 0x02):
		dualWrite(f, "Read Failed")
	else:
		dualWrite(f, "Result : ")
		for c in reply[4:20]:
			dualWrite(f, hex(ord(c)) + " ")		

	dualWrite(f, "\n")
	f.close()

def writeBlock(blockNum, data):
	clearVCS()
	f = open('/dev/vcs', 'w')
	
	if(len(data) != 16):
		dualWrite(f, 'invalid data length\n')
		f.close()
		return

	dualWrite(f, 'Writing to block ' + hex(blockNum) + ', data : ')
	for c in data:
		dualWrite(f, hex(c) + ' ')
	dualWrite(f, '\n')
	
	cmd = blockWriteCmd[0:5] + [blockNum] + blockWriteCmd[6:12] + data
	reply = sendCmd(cmd)
	
	if(not check(reply)):
		dualWrite(f, "Checksum Incorrect")
	elif(ord(reply[3]) == 0x22):
		dualWrite(f, "Write successful")
	elif(ord(reply[3]) == 0xDD):
		dualWrite(f, "Write Failed")
	
	dualWrite(f, "\n")
	f.close()


	
def initValue(blockNum, value):
	
	clearVCS()
	f = open('/dev/vcs', 'w')
	
	cmd = valueInitCmd[0:5] + [blockNum] + valueInitCmd[6:12] + [ord(ch) for ch in struct.pack('I',value)[0:4]]
	
	reply = sendCmd(cmd)
	
	dualWrite(f, 'Writing value to block ' + hex(blockNum) + ', value : ' + str(value) + '\n')
	

	
	if(not check(reply)):
		dualWrite(f, "Checksum Incorrect")
	elif(ord(reply[3]) == 0x23):
		dualWrite(f, "Write successful")
	elif(ord(reply[3]) == 0xDC):
		dualWrite(f, "Write Failed")
	
	dualWrite(f, "\n")
	f.close()

def readValue(blockNum):
	clearVCS()
	f = open('/dev/vcs', 'w')

	cmd = valueReadCmd[0:5] + [blockNum] + valueReadCmd[6:]
	reply = sendCmd(cmd)
	
	dualWrite(f, 'Reading value from block ' + hex(blockNum) + '\n')
	
	val = -1
	
	if(not check(reply)):
		dualWrite(f, "Checksum Incorrect")
	elif(ord(reply[2]) == 0x02):
		dualWrite(f, "Read Failed")
	else:
		val = struct.unpack('I',''.join(reply[4:8]))[0]
		dualWrite(f, "Value = " + str(val))
	dualWrite(f, "\n")
	f.close()
	return val


def incValue(blockNum, value):
	
	clearVCS()
	f = open('/dev/vcs', 'w')
	
	cmd = valueIncCmd[0:5] + [blockNum] + valueIncCmd[6:12] + [ord(ch) for ch in struct.pack('I',value)[0:4]]
	
	reply = sendCmd(cmd)
	
	dualWrite(f, 'Increasing value in block ' + hex(blockNum) + ', amount : ' + str(value) + '\n')
	
	
	if(not check(reply)):
		dualWrite(f, "Checksum Incorrect")
	elif(ord(reply[3]) == 0x25):
		dualWrite(f, "Increment successful")
	elif(ord(reply[3]) == 0xDA):
		dualWrite(f, "Increment Failed")
	
	dualWrite(f, "\n")
	f.close()

def decValue(blockNum, value):
	
	clearVCS()
	f = open('/dev/vcs', 'w')
	
	cmd = valueDecCmd[0:5] + [blockNum] + valueDecCmd[6:12] + [ord(ch) for ch in struct.pack('I',value)[0:4]]
	
	reply = sendCmd(cmd)
	
	dualWrite(f, 'Decreasing value in block ' + hex(blockNum) + ', amount : ' + str(value) + '\n')
	
	
	if(not check(reply)):
		dualWrite(f, "Checksum Incorrect")
	elif(ord(reply[3]) == 0x26):
		dualWrite(f, "Write successful")
	elif(ord(reply[3]) == 0xD9):
		dualWrite(f, "Write Failed")
	
	dualWrite(f, "\n")
	f.close()

