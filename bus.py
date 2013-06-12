from rfid import writeBlock, readBlock, readValue, initValue, incValue, decValue, readCardID
#import vcs
#import eventreader
import struct
import time
from stations import Station

currentStation = 0


BLOCK_HEADER	= 1
BLOCK_CARDID	= 2
BLOCK_TRANS		= [8,9,10,12]
BLOCK_MONEY		= 13

STATUS_OK			= 1
STATUS_NOOFFTAG		= 2
STATUS_TRANSPORT	= 4

ERROR_COMM			= -1
ERROR_RETAG			= -2
ERROR_NOMONEY		= -3
ERROR_OVERCHARGED 	= -4

FEE_SCALE 			= [1, 0.7, 0.5, 0]

def goNext():
	currentStation += 1
	if(currentStation >= len(Station)):
		currentStation = 0

def isTagged():
	reply = readCardID()
	if(reply[0] == ERROR_COMM):
		return [ERROR_COMM, reply[1]]
	return [STATUS_OK, reply[1:5]]

#Top up amount
def topUp(amount, stationID):

	tm = time.localtime(time.time())
	
	value = readValue(9)
	if(value[0] == ERROR_COMM):	return ERROR_COMM
	
	value = value[1]

	if(value + amount > 500000): return ERROR_COMM
	
	header = readBlock(BLOCK_HEADER);
	if(header[0] == ERROR_COMM): return ERROR_COMM
	header = header[1:]
	dateFormat = "%02d%02d%02d%02d%02d" % (tm.tm_year %100,
		tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)
	header[1:5] = [ord(ch) for ch in struct.pack('>I',value + amount)]
	header[5:15] = [ord(ch) for ch in dateFormat]
	header[15] = stationID
	print header
	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM

	if(incValue(BLOCK_MONEY, amount)[0] == ERROR_COMM): return ERROR_COMM

	return STATUS_OK

#Charge amount from card
def charge(amount):


	tm = time.localtime(time.time())
	
	value = readValue(BLOCK_MONEY)
	if(value[0] == ERROR_COMM):	return ERROR_COMM
	
	value = value[1]

	if(value - amount < 0): return ERROR_NOMONEY
	
	header = readBlock(BLOCK_HEADER);
	if(header[0] == ERROR_COMM): return ERROR_COMM
	header = header[1:]
	dateFormat = "%02d%02d%02d%02d%02d" % (tm.tm_year %100,
		tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)
	header[1:5] = [ord(ch) for ch in struct.pack('>I',value - amount)]
	header[5:15] = [ord(ch) for ch in dateFormat]
	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM

	if(decValue(BLOCK_MONEY, amount)[0] == ERROR_COMM): return ERROR_COMM

	return STATUS_OK


def initCard(cardID, cardType, stationID, newValue = 0):
	cardID = [ord(c) for c in cardID]
	header = [0]*16
	header[0] = cardType
	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_CARDID, cardID)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_TRANS[0], [0]*16)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_TRANS[1], [0]*16)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_TRANS[2], [0]*16)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_TRANS[3], [0]*16)[0] == ERROR_COMM): return ERROR_COMM
	if(initValue(BLOCK_MONEY, 0)[0] == ERROR_COMM):	 	   return ERROR_COMM
	return topUp(newValue, stationID)
	
#returns seconds elapsed from today 00:00
def elapsedSecond():	
	tm = time.localtime(time.time())
	return int(time.mktime(tm) - time.mktime(tm[0:3] + (0, 0, 0) + tm[6:9]))

#First 4 bits of header[0] contains transportation info vector
#(0000 for first tag, then 1000, 1100, 1110, 1111 for subsequent onboard tagging)
def getTransportVector(header):
	vector = [0]*4
	for i in range(4,8):
		if((1<<i) & header[0] > 0):
			vector[7 - i] = 1
	return vector

def setTransportVector(header, vector):
	if(len(vector) != 4):
		return header

	mask = 0
	for bit in vector:
		mask = (mask << 1) | bit
	header[0] = header[0] & 0x0f
	header[0] = header[0] | (mask << 4)

	return header

def getTransportRecord(index):
	record = readBlock(BLOCK_TRANS[index])
	if(record[0] == ERROR_COMM): return ERROR_COMM
	record = record[1:]
	return record

def lastOffTagged(record):
	return record[6] != 0xff

def isTransport(record, busNo):
	if(busNo == unpackData(record)[0:6].strip()): return False
	offTime = (record[6] << 16) + (record[7] << 8) + record[8]
	diff = (elapsedSecond() - offTime) % 86400
	if(diff < 300): return True
	return False



def getUserType(header):
	return header[0] & 0x3

def isReTagged(record, busNo, stationID):
	if(record[13] != stationID or busNo != unpackData(record)[0:6].strip()): return False
	if(record[6] != 0xff): return False
	onTime = (record[3] << 16) + (record[4] << 8) + record[5]
	diff = (elapsedSecond() - onTime) % 86400
	if(diff < 3600): return True
	return False

#precondition : not isRetagged()
def isOffBoard(record, busNo, stationID):
	if(record[6] == 0xff and busNo == unpackData(record)[0:6].strip()): return True
	return False


def tagged(busNo, stationID):

	print "Tagged on station " + Station[stationID-1] + ", bus No. " + busNo

	header = readBlock(BLOCK_HEADER)
	if(header[0] == ERROR_COMM): return ERROR_COMM
	header = header[1:]

	vector = getTransportVector(header)

	numTransport = 0
		
	for i in range(4):
		if(vector[i] == 0): break
		numTransport += 1

	lastRecord = [0]*16

	if(numTransport > 0): 
		lastRecord = getTransportRecord(numTransport - 1)
		if(lastRecord == ERROR_COMM): return ERROR_COMM
	currentRecord = getTransportRecord(numTransport)
	if(currentRecord == ERROR_COMM): 
		return ERROR_COMM

	if(isReTagged(currentRecord, busNo, stationID)): 
		print "Retagged"
		return ERROR_RETAG
	if(isOffBoard(currentRecord, busNo, stationID)): 
		print "off_board"
		return offboardTag(busNo, stationID, header, currentRecord, numTransport)
	print "on_board"
	return onboardTag(busNo, stationID, header, lastRecord, currentRecord, numTransport)

#precondition : not isReTagged() and not isOffBoard()
def onboardTag(busNo, stationID, header, lastRecord, currentRecord, numTransport):
	
	ret = 0
	fee = 1000

	if(not lastOffTagged(currentRecord)):
		ret += STATUS_NOOFFTAG
		fee += 500
		numTransport = 0
		header = setTransportVector(header, [0]*4)
		if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM

	if(numTransport > 0):
		if(isTransport(lastRecord, busNo)):
			fee = 0
			ret += STATUS_TRANSPORT
		else:
			numTransport = 0
			header = setTransportVector(header, [0]*4)
			if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM

	fee *= FEE_SCALE[getUserType(header)]

	currentRecord = packOnboardData(busNo, secondFormat(elapsedSecond()), fee, stationID)

	if(writeBlock(BLOCK_TRANS[numTransport], currentRecord)[0] == ERROR_COMM): 
		return ERROR_COMM

	if(charge(fee) == ERROR_COMM): return ERROR_COMM

	return [STATUS_OK + ret, currentRecord]

def calculateFee(record, stationID):
	onStation = record[13]
	diff = (stationID - onStation) % len(Station)
	if(diff < 5): return 0
	return (diff - 5) * 100

def offboardTag(busNo, stationID, header, currentRecord, numTransport):
	ret = 0
	fee = 0
	vector = [0]*4
	if(numTransport >= 3): numTransport = -1 
	for i in range(numTransport + 1):
		vector[i] = 1
	header = setTransportVector(header, vector)

	fee = calculateFee(currentRecord, stationID) * FEE_SCALE[getUserType(header)]

	currentRecord = repackData(currentRecord, secondFormat(elapsedSecond()), fee, stationID)

	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_TRANS[numTransport], currentRecord)[0] == ERROR_COMM):
		return ERROR_COMM

	if(charge(fee) == ERROR_COMM): return ERROR_COMM

	return STATUS_OK

def secondFormat(seconds):
	return "%02d%02d%02d" % (int(seconds / 60 / 60), int(seconds / 60) % 60, seconds % 60)



def packData(busNo, onTime, feeBasic, onStationID, offTime, feeAdd, offStationID):
	busNoCoded = 0xffffffff
	packed = []
	for ch in busNo:
		if(ch == '-'): n = 0xa
		elif(ord(ch) >= ord('0') and ord(ch) <= ord('9')):	n = int(ch)
		else: n = 0xf

		busNoCoded = (busNoCoded << 4) + n

	onTimeInt =  ( int(onTime[0:2]) * 60 + int(onTime[2:4]) ) * 60 + int(onTime[4:6])
	offTimeInt =  ( int(offTime[0:2]) * 60 + int(offTime[2:4]) ) * 60 + int(offTime[4:6])

	packed = [ord(ch) for ch in struct.pack('>I', busNoCoded & 0xffffffff)[1:]]
	packed += [ord(ch) for ch in struct.pack('>I', onTimeInt)[1:]]
	packed += [ord(ch) for ch in struct.pack('>I', offTimeInt)[1:]]
	packed += [ord(ch) for ch in struct.pack('>H', feeBasic)]
	packed += [ord(ch) for ch in struct.pack('>H', feeAdd)]
	packed += [onStationID, offStationID, 0]

	return packed

def repackData(packed, offTime, feeAdd, offStationID):
	unpacked = unpackData(packed)
	return packData(unpacked[0:6], unpacked[6:12], int(unpacked[12:16]), int(unpacked[16:19]),
		offTime, feeAdd, offStationID)

def packOnboardData(busNo, onTime, feeBasic, onstationID):
	busNoCoded = 0xffffffff
	packed = []
	for ch in busNo:
		if(ch == '-'): n = 0xa
		elif(ord(ch) >= ord('0') and ord(ch) <= ord('9')):	n = int(ch)
		else: n = 0xf

		busNoCoded = (busNoCoded << 4) + n

	onTimeInt =  ( int(onTime[0:2]) * 60 + int(onTime[2:4]) ) * 60 + int(onTime[4:6])

	packed = [ord(ch) for ch in struct.pack('>I', busNoCoded & 0xffffffff)[1:]]
	packed += [ord(ch) for ch in struct.pack('>I', onTimeInt)[1:]]
	packed += [0xff, 0xff, 0xff]
	packed += [ord(ch) for ch in struct.pack('>H', feeBasic)]
	packed += [0, 0]
	packed += [onstationID, 0xff, 0]

	return packed

def unpackData(packed):
	busNoEncoded = struct.unpack('sss', ''.join([chr(c) for c in packed[0:3]]))
	busNo = ''
	for ch in busNoEncoded:
		chPair = [(ord(ch) >> 4) & 0xf, ord(ch) & 0xf]
		for c in chPair:
			if (c >= 0 and c <= 9):
				busNo += str(c)
			elif (c == 0xa):
				busNo += '-'
			else:
				busNo += ' '

	onTimeInt = struct.unpack('>I', '\x00' + ''.join([chr(c) for c in packed[3:6]]))[0]
	offTimeInt = struct.unpack('>I', '\x00' + ''.join([chr(c) for c in packed[6:9]]))[0]

	onTime = secondFormat(onTimeInt)
	offTime = secondFormat(offTimeInt)

	feeBasic = "%04d" % struct.unpack('>H', ''.join([chr(c) for c in packed[9:11]]))[0]
	feeAdd  = "%04d" % struct.unpack('>H', ''.join([chr(c) for c in packed[11:13]]))[0]

	onstationID = "%03d" % packed[13]
	offstationID = "%03d" % packed[14]

	return busNo + onTime + feeBasic + onstationID + offTime + feeAdd + offstationID

def drive():
	while(True):
		if(isTagged()[0] == STATUS_OK):
			tagged("34",4)