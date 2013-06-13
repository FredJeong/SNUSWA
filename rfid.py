import sys
import serial
from os import system
import time
import struct

keyA = [0xff] * 6

echoCmd = [0xaa, 0xbb, 0x9, 0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7]
beepCmd = [0xaa, 0xbb, 0x3, 0x14, 0x13]
cardIDCmd = [0xaa, 0xbb, 0x2, 0x20]
cardSleepCmd = [0xaa, 0xbb, 0x02, 0x12]
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
sectorReadCmd = [
	0xaa, 0xbb, 0x0a, 0x2a, 0x00, 0x01,
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
sectorWriteCmd = [
	0xaa, 0xbb, 0x3a, 0x2b, 0x00, 0x01,
	0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
	0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 
	0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 
	0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33]



reply = []

ERR_CHKSUM	= 0
ERR_INPUT	= 1
ERR_COMM	= 2

# for windows
#s = serial.Serial("COM20", baudrate=19200)
# for linux
s = serial.Serial("/dev/ttyUSB0", baudrate=19200)

def process(cmd):
	if(len(cmd) < 3):
		return cmd
	newCmd = cmd[0:2]
	for ch in cmd[2:]:
		newCmd.append(ch)
		if(ch == 0xaa):
			newCmd.append(0x00)
	return newCmd

def processInv(cmd):
	if(len(cmd) < 3):
		return cmd
	newCmd = cmd[0:2]
	aaOccurred = False
	for ch in cmd[2:]:
		if(aaOccurred):
			aaOccurred = False
			continue
		newCmd.append(ch)
		if(ch == 0xaa):
			aaOccurred = True
	return newCmd


def sendCmd(cmd):

	time.sleep(0.1)
	flush()

	csum = 0
	cmd = process(cmd)

	for c in cmd:
		s.write(chr(c))
		csum = csum ^ c
	csum = csum ^ 0xaa ^ 0xbb
	s.write(chr(csum))

	reply = []
	

	prevTime = time.time()
	while(s.inWaiting() < 1) :
		if(time.time() - prevTime > 1):
			sys.stdout.write("Timeout")
			return
	
	csum = 0
	while(s.inWaiting() > 0):
		while(s.inWaiting() > 0):
			r = s.read()
			reply.append(ord(r))
			csum = csum ^ ord(r)
		time.sleep(0.05)
	csum = csum ^ 0xaa ^ 0xbb 
	
	if(csum != 0):
		sys.stdout.write("Checksum incorrect")
	
	return reply

def check(response):
	if(len(response) < 4):
		sys.stdout.write("Invalid response")
		return False
	csum = 0

	for c in response[2:]:
		csum = csum ^ c
	if(csum != 0):
		return False
	return True


def sendCmdD(cmd):

	sys.stdout.write("Command to READER: ")
	
	csum = 0
	cmd = process(cmd)

	for c in cmd:
		s.write(chr(c))
		csum = csum ^ c
		sys.stdout.write(hex(c) + " ")
	csum = csum ^ 0xaa ^ 0xbb
	s.write(chr(csum))
	sys.stdout.write(hex(csum) + "\n")



	sys.stdout.write("Reply from READER: ")
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
		sys.stdout.write(hex(r) + " ")
		reply.append(r)
	sys.stdout.write("\n")
	f.close()
	
def flush():
	reply = []
	for c in range(s.inWaiting()):
		r = s.read()
		reply.append(r)
	
	sys.stdout.write(''.join([hex(ord(c)) for c in reply]))

def readCardID():

	ret = []
	reply = processInv(sendCmd(cardIDCmd))

	if(not check(reply)):
		ret = [-1, ERR_CHKSUM]
	elif(reply[2] == 0x06):
		ret = [1] + reply[4:8]
	else:
		ret = [-1, ERR_COMM]

	return ret

def sleepCard():
	ret = []
	reply = processInv(sendCmd(cardSleepCmd))

	if(not check(reply)):
		ret = [-1, ERR_CHKSUM]
	elif(reply[3] == 0x12):
		ret = [1]
	else:
		ret = [-1, ERR_COMM]

	return ret

def readBlock(blockNum):

	ret = []

	sys.stdout.write("Read block " + hex(blockNum) + "\n")

	cmd = blockReadCmd[0:5] + [blockNum] + blockReadCmd[6:12]
	reply = processInv(sendCmd(cmd))
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[2]== 0x02):
		sys.stdout.write("Read Failed")
		ret = [-1, ERR_COMM]
	else:
		sys.stdout.write("Result : ")
		for c in reply[4:-1]:
			sys.stdout.write(hex(c) + " ")
		ret = [1] + reply[4:-1]

	sys.stdout.write("\n")
	
	return ret;

def readSector(sectorNum):

	ret = []

	sys.stdout.write("Read sector " + hex(sectorNum) + "\n")

	cmd = sectorReadCmd[0:5] + [sectorNum] + sectorReadCmd[6:]
	reply = processInv(sendCmd(cmd))
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[2]== 0x02):
		sys.stdout.write("Read Failed")
		ret = [-1, ERR_COMM]
	else:
		sys.stdout.write("Result : ")
		for c in reply[5:-1]:
			sys.stdout.write(hex(c) + " ")
		ret = [1] + reply[5:-1]

	sys.stdout.write("\n")
	
	return ret;


def writeBlock(blockNum, data):

	ret = [-1]

	sys.stdout.write('Writing to block ' + hex(blockNum) + ', \ndata : ')
	for c in data:
		sys.stdout.write(hex(c) + ' ')
	sys.stdout.write('\n')

	if(len(data) != 16):
		sys.stdout.write('invalid data length : ' + str(len(data)) + '\n')
		ret = [-1, ERR_INPUT]
		return ret

	cmd = blockWriteCmd[0:5] + [blockNum] + blockWriteCmd[6:12] + data
	reply = processInv(sendCmd(cmd))
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[3] == 0x22):
		sys.stdout.write("Write successful")
		ret = [1]
	elif(reply[3] == 0xDD):
		sys.stdout.write("Write Failed")
		ret = [-1, ERR_COMM]


	sys.stdout.write("\n")
	return ret

def writeSector(sectorNum, data):

	ret = [-1]

	sys.stdout.write('Writing to sector ' + hex(sectorNum) + ', \ndata : ')
	for c in data:
		sys.stdout.write(hex(c) + ' ')
	sys.stdout.write('\n')

	if(sectorNum <= 0x20 and len(data) != 48):
		sys.stdout.write('invalid data length : ' + str(len(data)) + '\n')
		ret = [-1, ERR_INPUT]
		return ret
	elif(sectorNum > 0x20 and sectorNum <= 0x29 and len(data) != 240):
		sys.stdout.write('invalid data length : ' + str(len(data)) + '\n')
		ret = [-1, ERR_INPUT]
		return ret
	
	
	cmd = sectorWriteCmd[0:5] + [sectorNum] + sectorWriteCmd[6:12] + data
	reply = processInv(sendCmd(cmd))
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[3] == 0x2B):
		sys.stdout.write("Write successful")
		ret = [1]
	elif(reply[3] == 0xD4):
		sys.stdout.write("Write Failed")
		ret = [-1, ERR_COMM]

	sys.stdout.write("\n")
	return ret

	
def initValue(blockNum, value):
	
	
	cmd = valueInitCmd[0:5] + [blockNum] + valueInitCmd[6:12] + [ord(ch) for ch in struct.pack('I',value)[0:4]]
	
	reply = processInv(sendCmd(cmd))
	
	sys.stdout.write('Writing value to block ' + hex(blockNum) + ', value : ' + str(value) + '\n')
	
	ret = []
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[3] == 0x23):
		sys.stdout.write("Write successful")
		ret = [1]
	elif(reply[3] == 0xDC):
		sys.stdout.write("Write Failed")
		ret = [-1, ERR_COMM]
	sys.stdout.write("\n")
	return ret

def readValue(blockNum):

	cmd = valueReadCmd[0:5] + [blockNum] + valueReadCmd[6:]
	reply = processInv(sendCmd(cmd))
	
	sys.stdout.write('Reading value from block ' + hex(blockNum) + '\n')
	
	val = -1

	ret = []
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[2] == 0x02):
		sys.stdout.write("Read Failed")
		ret = [-1, ERR_COMM]
	else:
		val = struct.unpack('I',''.join([chr(c) for c in reply[4:8]]))[0]
		sys.stdout.write("Value = " + str(val))
		ret = [1, val]
	sys.stdout.write("\n")
	return ret


def incValue(blockNum, value):
	
	cmd = valueIncCmd[0:5] + [blockNum] + valueIncCmd[6:12] + [ord(ch) for ch in struct.pack('I',value)[0:4]]
	
	reply = processInv(sendCmd(cmd))
	
	sys.stdout.write('Increasing value in block ' + hex(blockNum) + ', amount : ' + str(value) + '\n')
	
	ret = []
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]
	elif(reply[3] == 0x25):
		sys.stdout.write("Increment successful")
		ret = [1]
	elif(reply[3] == 0xDA):
		sys.stdout.write("Increment Failed")
		ret = [-1, ERR_COMM]
	sys.stdout.write("\n")
	return ret

def decValue(blockNum, value):
	cmd = valueDecCmd[0:5] + [blockNum] + valueDecCmd[6:12] + [ord(ch) for ch in struct.pack('I',value)[0:4]]
	
	reply = processInv(sendCmd(cmd))
	
	sys.stdout.write('Decreasing value in block ' + hex(blockNum) + ', amount : ' + str(value) + '\n')
	
	ret = [-1]
	
	if(not check(reply)):
		sys.stdout.write("Checksum Incorrect")
		ret = [-1, ERR_CHKSUM]		
	elif(reply[3] == 0x26):
		sys.stdout.write("Write successful")
		ret = [1]
	elif(reply[3] == 0xD9):
		sys.stdout.write("Write Failed")
		ret = [-1, ERR_COMM]
	
	sys.stdout.write("\n")
	return ret

