from rfid import writeBlock, readBlock, readValue, initValue, incValue, decValue, readCardID, sleepCard, readSector, writeSector
import rfid
import vcs
import eventreader
import struct
import time
from stations import Stations
from eventreader import Buttons
import screen

currentStation = 1
busNumber = "111111"

BLOCK_HEADER	= 1
BLOCK_CARDID	= 2
BLOCK_TRANS		= [8,9,10,12]
BLOCK_MONEY		= 13
BLOCKS = [BLOCK_HEADER, BLOCK_CARDID, BLOCK_MONEY] + BLOCK_TRANS
SECTORS = [0,2,3]

STATUS_OK			= 1
STATUS_NOOFFTAG		= 2
STATUS_TRANSPORT	= 4
STATUS_GETOFF		= 8

ERROR_COMM			= -1
ERROR_RETAG			= -2
ERROR_NOMONEY		= -3
ERROR_OVERCHARGED 	= -4

FEE_SCALE 			= [1, 0.7, 0.5, 0]
blockBuffer			= [0] * 16

def goNext():
	global currentStation
	currentStation += 1
	if(currentStation >= len(Stations)):
		currentStation = 1

def isTagged():
	reply = readCardID()
	if(reply[0] == ERROR_COMM):
		return [ERROR_COMM, reply[1]]
	return [STATUS_OK, reply[1:5]]

#Top up amount
def topUp(amount, stationID):

	tm = time.localtime(time.time())
	
	value = readValue(BLOCK_MONEY)
	if(value[0] == ERROR_COMM):	return ERROR_COMM
	
	value = value[1]

	if(value + amount > 500000): return ERROR_COMM
	
	header = blockBuffer[BLOCK_HEADER]
	dateFormat = "%02d%02d%02d%02d%02d" % (tm.tm_year %100,
		tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)
	

	header[1:5] = [ord(ch) for ch in struct.pack('>I',value + amount)]
	header[5:15] = [ord(ch) for ch in dateFormat]
	header[15] = stationID
	
	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM

	if(incValue(BLOCK_MONEY, amount)[0] == ERROR_COMM): return ERROR_COMM

	return STATUS_OK

#Charge amount from card
def charge(amount):
	global blockBuffer

	tm = time.localtime(time.time())
	
	value = readValue(BLOCK_MONEY)
	if(value[0] == ERROR_COMM):	return ERROR_COMM
	
	value = value[1]

	if(value - amount < 0): return ERROR_NOMONEY
	
	header = blockBuffer[BLOCK_HEADER]
	dateFormat = "%02d%02d%02d%02d%02d" % (tm.tm_year %100,
		tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)
	header[1:5] = [ord(ch) for ch in struct.pack('>I',value - amount)]
	header[5:15] = [ord(ch) for ch in dateFormat]
	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM

	if(decValue(BLOCK_MONEY, amount)[0] == ERROR_COMM): return ERROR_COMM

	return STATUS_OK


def initCard(cardID, cardType, stationID, newValue = 0):
	global blockBuffer
	cardID = [ord(c) for c in cardID]
	header = [0]*16
	header[0] = cardType
	blockBuffer[BLOCK_HEADER] = header
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
	global blockBuffer
	record = blockBuffer[BLOCK_TRANS[index]]
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
	global blockBuffer

	print "\n<Tagged on station " + Stations[stationID] + ", bus No. " + busNo + ">\n" 

	header = blockBuffer[BLOCK_HEADER]

	vector = getTransportVector(header)

	numTransport = 0
		
	for i in range(4):
		if(vector[i] == 0): break
		numTransport += 1

	lastRecord = [0]*16

	if(numTransport > 0): 
		lastRecord = getTransportRecord(numTransport - 1)
	currentRecord = getTransportRecord(numTransport)

	if(isReTagged(currentRecord, busNo, stationID)): 
		print "\n<Retagged>\n"
		return ERROR_RETAG
	if(isOffBoard(currentRecord, busNo, stationID)): 
		print "\n<off_board>\n"
		result = offboardTag(busNo, stationID, header, currentRecord, numTransport)
	else:
		print "\n<on_board>\n"
		result = onboardTag(busNo, stationID, header, lastRecord, currentRecord, numTransport)
	if(result == ERROR_COMM): return ERROR_COMM
	if(sleepCard()[0] == ERROR_COMM): return ERROR_COMM
	return result


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

	fee = int(fee * FEE_SCALE[getUserType(header)])

	result = charge(fee)
	if(result == ERROR_COMM): return ERROR_COMM
	elif(result == ERROR_NOMONEY): return ERROR_NOMONEY

	currentRecord = packOnboardData(busNo, secondFormat(elapsedSecond()), fee, stationID)

	if(writeBlock(BLOCK_TRANS[numTransport], currentRecord)[0] == ERROR_COMM): 
		return ERROR_COMM


	

	return [STATUS_OK + ret,  fee, getUserType(header), currentRecord]

def calculateFee(record, stationID):
	onStation = record[13]
	diff = (stationID - onStation) % len(Stations)
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

	fee = int(calculateFee(currentRecord, stationID) * FEE_SCALE[getUserType(header)])


	result = charge(fee)
	if(result == ERROR_COMM): return ERROR_COMM
	elif(result == ERROR_NOMONEY): return ERROR_NOMONEY

	currentRecord = repackData(currentRecord, secondFormat(elapsedSecond()), fee, stationID)

	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_TRANS[numTransport], currentRecord)[0] == ERROR_COMM):
		return ERROR_COMM



	return [STATUS_GETOFF + STATUS_OK, fee, getUserType(header), currentRecord]

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

def setBusNo(busNo):
	global busNumber
	busNumber = busNo

def drive(busNo = busNumber, stationID = 1):
	global blockBuffer
	global currentStation
	currentStation = stationID
	prevTime = int(time.time())
	prevTime2 = int(time.time())
	errorFlag = 0
	screen.runScreen(Stations[currentStation], busNo)
	while(True):
		errorFlag = 0
		if(time.time() - prevTime > 10):
			goNext()
			prevTime = int(time.time())
			screen.runScreen(Stations[currentStation], busNo)
		if(int(time.time()) != prevTime2):
			prevTime2 = int(time.time())
			screen.timeScreen()

		if(isTagged()[0] == STATUS_OK):
			rfid.flush()
			backup = [0]*4
			screen.cardtagScreen(Stations[currentStation], 0, busNo,
				True, "Tagging...Wait")

			for sectorIdx in SECTORS:
				for i in range(3):
					sector = readSector(sectorIdx)
					if(sector[0] != -1): break
					if (i == 2):
						errorFlag = ERROR_COMM
				backup[sectorIdx] = sector[1:]
				if(errorFlag < 0): 
					break
			if(errorFlag < 0): continue

			for blockIdx in BLOCKS:
				sectorIdx = int(blockIdx / 4)
				offset = blockIdx % 4
				blockBuffer[blockIdx] = backup[sectorIdx][offset*16:offset*16+16]

			result = tagged(busNo, currentStation)
			if(result == ERROR_COMM):
				print "\n<ERROR. Try rolling-back>\n"
				screen.cardtagScreen(Stations[currentStation], 0, busNo,
					True, "ERROR. Try rolling-back")
				for sectorIdx in SECTORS:
					for i in range(3):
						print sectorIdx
						if(writeSector(sectorIdx, backup[sectorIdx])[0] != -1): break
			elif(result == ERROR_NOMONEY):
				screen.cardtagScreen(Stations[currentStation], 0, busNo,
					True, "Not enough minerals.")
				time.sleep(1)
			elif(result == ERROR_RETAG):
				screen.cardtagScreen(Stations[currentStation], 0, busNo,
					True, "Retagged.")
				time.sleep(1)


			elif(result[0] > 0):
				print "\n<Tagging success>\n"
				msg = "Tagging success"
				if(result[0] & STATUS_NOOFFTAG > 0): msg = "NOT TAGGED FOR LAST GETOFF"
				if(result[0] & STATUS_TRANSPORT > 0): msg += ", transport"
				if(result[0] & STATUS_GETOFF > 0): 
					msg += ", Bye!"
				else:
					msg +=". Welcome!"
				screen.cardtagScreen(Stations[currentStation], result[1], busNo,
					True, msg)
				time.sleep(1)


			screen.runScreen(Stations[currentStation], busNo)


		else: time.sleep(0.1)
