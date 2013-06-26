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
BLOCK_CARDNO	= 2
BLOCK_TRANS		= [8,9,10,12]
BLOCK_MONEY		= 13
BLOCKS = [BLOCK_HEADER, BLOCK_CARDNO, BLOCK_MONEY] + BLOCK_TRANS
SECTORS = [0,2,3]

STATUS_OK			= 1
STATUS_NOOFFTAG		= 2
STATUS_TRANSPORT	= 4
STATUS_GETOFF		= 8

ERROR_COMM			= -1
ERROR_RETAG			= -2
ERROR_NOMONEY		= -3
ERROR_OVERCHARGED 	= -4

ERROR_CARDNO		= [ord('F')]*16

FEE_SCALE 			= [1, 0.7, 0.5, 0]
blockBuffer			= [0] * 16

outFile				= file					

def goNext():
	global currentStation
	currentStation += 1
	if(currentStation >= len(Stations)):
		currentStation = 1

def goPrev():
	global currentStation
	currentStation -= 1
	if(currentStation <= 0):
		currentStation = len(Stations) - 1

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


def initCard(CARDNO, cardType, stationID, newValue = 0):
	global blockBuffer
	CARDNO = [ord(c) for c in CARDNO]
	header = [0]*16
	header[0] = cardType
	blockBuffer[BLOCK_HEADER] = header
	if(writeBlock(BLOCK_HEADER, header)[0] == ERROR_COMM): return ERROR_COMM
	if(writeBlock(BLOCK_CARDNO, CARDNO)[0] == ERROR_COMM): return ERROR_COMM
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

def isReTaggedOnboard(record, busNo, stationID):
	if(record[13] != stationID or busNo != unpackData(record)[0:6].strip()): return False
	if(record[6] != 0xff): return False
	onTime = (record[3] << 16) + (record[4] << 8) + record[5]
	diff = (elapsedSecond() - onTime) % 86400
	if(diff < 300): return True
	return False

def isReTaggedOffboard(record, busNo, stationID):
	if(record[14] != stationID or busNo != unpackData(record)[0:6].strip()): return False
	offTime = (record[19] << 16) + (record[20] << 8) + record[21]
	diff = (elapsedSecond() - onTime) % 86400
	if(diff < 300): return True
	return False

#precondition : not isRetagged()
def isOffBoard(record, busNo, stationID):
	if(record[6] == 0xff and busNo == unpackData(record)[0:6].strip()): return True
	return False


def tagged(busNo, stationID):
	global blockBuffer

	print "\n<Tagged on station " + Stations[stationID] + ", bus No. " + busNo + ">\n" 

	header = blockBuffer[BLOCK_HEADER]

	if(header == 0):
		for i in range(3):
			header = readBlock(BLOCK_HEADER)
			if(header[0] != ERROR_COMM):
				header = header[1:]
				break
	if(header[0] == ERROR_COMM):
		return ERROR_COMM



	vector = getTransportVector(header)

	numTransport = 0
		
	for i in range(4):
		if(vector[i] == 0): break
		numTransport += 1

	lastRecord = [0]*16

	if(numTransport > 0): 
		lastRecord = getTransportRecord(numTransport - 1)
	currentRecord = getTransportRecord(numTransport)

	if(isReTaggedOnboard(currentRecord, busNo, stationID)): 
		print "\n<Retagged>\n"
		return ERROR_RETAG
	if(isReTaggedOffboard(lastRecord, busNo, stationID)): 
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

def writeRecordToFile(cardNo, record):
	cardNo = ''.join([chr(c) for c in cardNo])
	record = unpackData(record)
	buf = "%16s%32s\n" % (cardNo, record)
	outFile.write(buf)

#precondition : not isReTagged() and not isOffBoard()
def onboardTag(busNo, stationID, header, lastRecord, currentRecord, numTransport):
	
	ret = 0
	fee = 1000

	if(not lastOffTagged(currentRecord)):
		ret += STATUS_NOOFFTAG
		fee += 500
		numTransport = 0
		header = setTransportVector(header, [0]*4)
		writeRecordToFile(blockBuffer[BLOCK_CARDNO], currentRecord)
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
	
	writeRecordToFile(blockBuffer[BLOCK_CARDNO], currentRecord)

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

def main(busNos):
	screen.busNumScreen(busNos[0],busNos[1],busNos[2],busNos[3])

	while(True):
		eventreader.updateButtonState()
		busNumber = ""
		for i in range(4):
			if(eventreader.isButtonDown(i)): busNumber = busNos[i]
		if(len(busNumber) > 0):
			result = drive(busNumber, 1)
			screen.busNumScreen(busNos[0],busNos[1],busNos[2],busNos[3])
		if(eventreader.isButtonDown(Buttons.SEARCH)):
			break
		time.sleep(0.1)
	vcs.clear()
	vcs.drawRect(30,10,40,10)
	vcs.write(48,14,"Bye!")
	vcs.write(47,15,"-ECHO-")

def getFileName():
	now = time.localtime(time.time())
	return "trans_%04d_%02d%02d_%02d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday,
		now.tm_hour, now.tm_min, now.tm_sec)

def getValueFromBlock(block):
	packed = ''.join([chr(c) for c in block[0:4]])
	return struct.unpack('I',packed)[0]


def drive(busNo = busNumber, stationID = 1):
	global blockBuffer
	global currentStation
	currentStation = stationID
	prevTime = int(time.time())
	prevTime2 = int(time.time())
	errorFlag = 0
	screen.runScreen(Stations[currentStation], busNo)
	backup = [0]*4

	global outFile
	outFile = open(getFileName(), "w")
	while(True):
		eventreader.updateButtonState()

		errorFlag = 0
		if(int(time.time()) != prevTime2):
			prevTime2 = int(time.time())
			screen.timeScreen()

		if(eventreader.isButtonDown(Buttons.VOLUMEDOWN)):
			goPrev()
			screen.runScreen(Stations[currentStation], busNo)

		if(eventreader.isButtonDown(Buttons.VOLUMEUP)):
			goNext()
			screen.runScreen(Stations[currentStation], busNo)

		if(eventreader.isButtonDown(Buttons.BACK)):
			outFile.close()
			return 0


		if(eventreader.isButtonDown(Buttons.MENU)):
			rfid.flush()
			vcs.write(35, 20, "Please tag your bus card!")
			while True:
				while(isTagged()[0] != STATUS_OK): time.sleep(0.1)

				for i in range(3):
					blockBuffer[BLOCK_HEADER] = readBlock(BLOCK_HEADER)
					if(blockBuffer[BLOCK_HEADER][0] != ERROR_COMM):
						blockBuffer[BLOCK_HEADER] = blockBuffer[BLOCK_HEADER][1:]
						break
					time.sleep(0.1)

				for i in range(3):
					[res,Money] = readValue(BLOCK_MONEY)
					if(res != ERROR_COMM): break
					time.sleep(0.1)
				if(blockBuffer[BLOCK_HEADER][0] == ERROR_COMM or res == ERROR_COMM):
					errorFlag = ERROR_COMM
					vcs.write(35, 20, "READ ERROR"                        )
					print "\n<READ ERROR>\n"
					rfid.sleepCard()
					time.sleep(2)
					screen.runScreen(Stations[currentStation], busNo)
					break

				screen.chargeScreen(Money)
				while True:
					eventreader.updateButtonState()
					amount = 0
					if(eventreader.isButtonDown(Buttons.HOME)): 
						amount = 1000
					elif(eventreader.isButtonDown(Buttons.ENTER)): 
						amount = 5000
					elif(eventreader.isButtonDown(Buttons.MENU)): 
						amount = 10000
					elif(eventreader.isButtonDown(Buttons.BACK)):
						amount = 20000
					else:
						time.sleep(0.1)
						continue
					res = topUp(amount, currentStation)
					if(res != STATUS_OK):
						errorFlag = res
						vcs.write(35, 20, "WRITE ERROR. Rolling back..          ")
						print "\n<WRITE ERROR. Rolling back..>\n"

						for i in range(3):
							res = writeBlock(BLOCK_HEADER, blockBuffer[BLOCK_HEADER])
							if(res != ERROR_COMM): break
							time.sleep(0.1)

						writeRecordToFile(ERROR_CARDNO, 
							packOnboardData("000000",secondFormat(elapsedSecond()), -res,0))

						rfid.sleepCard()
						time.sleep(2)
						screen.runScreen(Stations[currentStation], busNo)
						break
					if(errorFlag == 0):
						screen.chargeFinishScreen(Money + amount)
					break
				time.sleep(3)
				screen.runScreen(Stations[currentStation], busNo)
				rfid.sleepCard()
				break
					

		if(isTagged()[0] == STATUS_OK):
			rfid.flush()
			screen.cardTagScreen(Stations[currentStation], 0, 0, busNo,
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
				print "Sector[%d][%d] => Block[%d]" % (sectorIdx, offset, blockIdx)
				blockBuffer[blockIdx] = backup[sectorIdx][offset*16:offset*16+16]

			value = 0
			if(blockBuffer[BLOCK_MONEY] !=0):
				value = getValueFromBlock(blockBuffer[BLOCK_MONEY])
			screen.cardTagScreen(Stations[currentStation], 0, value, busNo,
				True, "Tagging...Wait")


			result = tagged(busNo, currentStation)
			if(result == ERROR_COMM):
				errorFlag = result
				print "\n<ERROR. Try rolling-back>\n"
				screen.cardTagScreen(Stations[currentStation], 0, value, busNo,
					True, "ERROR. Try rolling-back")
				for sectorIdx in SECTORS:
					for i in range(3):
						print sectorIdx
						if(writeSector(sectorIdx, backup[sectorIdx])[0] != -1): break
				writeRecordToFile(ERROR_CARDNO, 
					packOnboardData("000000",secondFormat(elapsedSecond()), -result,0))
			elif(result == ERROR_NOMONEY):
				errorFlag = result
				screen.cardTagScreen(Stations[currentStation], 0, value, busNo,
					True, "Not enough minerals.")
				print "\n<Not enough minerals.>\n"
				writeRecordToFile(ERROR_CARDNO, 
					packOnboardData("000000",secondFormat(elapsedSecond()), -result,0))
				time.sleep(2)
			elif(result == ERROR_RETAG):
				errorFlag = result
				screen.cardTagScreen(Stations[currentStation], 0, value, busNo,
					True, "Retagged.")
				print "\n<Retagged.>\n"
				writeRecordToFile(ERROR_CARDNO, 
					packOnboardData("000000",secondFormat(elapsedSecond()), -result,0))
				time.sleep(2)


			elif(result[0] > 0):
				print "\n<Tagging success>\n"
				msg = "Tagging success"
				if(result[0] & STATUS_NOOFFTAG > 0): msg = "NOT TAGGED FOR LAST GETOFF"
				if(result[0] & STATUS_TRANSPORT > 0): msg += ", transport"
				if(result[0] & STATUS_GETOFF > 0): 
					msg += ", Bye!"
				else:
					msg +=". Welcome!"
				screen.cardTagScreen(Stations[currentStation], result[1], value - result[1],
					busNo, True, msg)
				print "\n<" + msg + ">\n"
				time.sleep(2)


			screen.runScreen(Stations[currentStation], busNo)

		if(int(time.time()) - prevTime > 300):
			prevTime = int(time.time())
			outFile.close()
			outFile = open(getFileName(), "w")


		time.sleep(0.1)

main(["1550-1","5511","650","5528"])