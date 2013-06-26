import screen
import eventreader
import vcs
import time
from eventreader import Buttons
import bus
from rfid import writeBlock, readBlock, readValue, initValue, incValue, decValue, readCardID, sleepCard, readSector, writeSector
import rfid

STATUS_OK		= 1 
STATUS_NOOFFTAG		= 2
STATUS_TRANSPORT	= 4
STATUS_GETOFF		= 8


def chargeProcess(busNo, stationID, stationName):
	vcs.write(35, 20, "Please tag your bus card!")
	while True:
		if(bus.isTagged()[0] == STATUS_OK):
			Money = rfid.readValue(bus.BLOCK_MONEY)[1]
			screen.chargeScreen(Money)
			while True:
				eventreader.updateButtonState()
				amount = 0
				if(eventreader.isButtonDown(Buttons.HOME)): amount = 1000
				elif(eventreader.isButtonDown(Buttons.ENTER)): amount = 5000
				elif(eventreader.isButtonDown(Buttons.MENU)): amount = 10000
				elif(eventreader.isButtonDown(Buttons.BACK)):amount = 20000
				else:
					time.sleep(0.1)
					continue

				bus.topUp(amount, stationID)
				[res,Money] = rfid.readValue(bus.BLOCK_MONEY)
				time.sleep(3)
				screen.runScreen(stationName, busNo)
				return res

