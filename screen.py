import vcs
import time

def timeScreen():
		tt = time.localtime()
		tstr = "%2I:%2M:%2S %p"
		vcs.write(48, 5, time.strftime(tstr, tt))

def drawButtonRect():

	vcs.drawRect(90, 6, 10, 3, False)
	vcs.drawRect(90, 12, 10, 3, False)
	vcs.drawRect(90, 18, 10, 3, False)
	vcs.drawRect(90, 24, 10, 3, False)

def drawButtonStr(str1, str2, str3, str4):
	vcs.write(93, 7, str(str1))
	vcs.write(93, 13, str(str2))
	vcs.write(93, 19, str(str3))
	vcs.write(93, 25, str(str4))

def basicSet():
	vcs.clear()
	vcs.drawRect(0,0,100,3)
	vcs.write(49,1,"ECHO")
	vcs.drawRect(20,8,60,5,False)

def finishScreen():
	basicSet()
	vcs.write(48, 10, "finish!")
	vcs.write(35, 20, "if you want to start, press button!")

	timeScreen()

def busNumScreen(busnum1, busnum2, busnum3, busnum4):
	basicSet()
	vcs.write(45, 10,"select Bus number")
	vcs.write(35, 20, "Select bus number button")
	
	drawButtonStr(busnum1, busnum2, busnum3, busnum4)
	drawButtonRect()
	
	timeScreen()

def chargeScreen(curMoney):

	basicSet()
	vcs.write(48, 10, "charge")
	vcs.write(35, 20, "Select money to charge")

	drawButtonStr(1000, 5000, 10000, 20000)
	drawButtonRect()

	vcs.write(35, 25, "current Money  :  " +str(curMoney))

	timeScreen()

def chargeFinishScreen(curMoney):

	basicSet()
	vcs.write(46, 10, "finish charging")
	vcs.write(35, 25, "current Money  :  "+str(curMoney))

	timeScreen()

def runScreen(busStop, busnum):
	basicSet()
	vcs.write(43, 10, "run at \""+str(busStop)+"\"" + "(" + str(busnum) + ")")
	drawButtonStr(" "," ","charge", "finish")
	drawButtonRect()
	
	timeScreen()
	
def cardTagScreen(busStop, fee, deposit, busnum, error=False, errorMsg="error"):

	basicSet()
	vcs.write(43, 10, "Running on \""+str(busStop)+"\" "+"("+str(busnum)+")")
	vcs.write(40, 20, "Card is tagged")
	vcs.write(40, 25, "fee     : %6d" % fee)
	vcs.write(40, 26, "Deposit : %6d" % deposit)
	
	if(error==True): errorScreen(errorMsg)
	
	timeScreen()

def errorScreen(errorMsg):

	vcs.drawRect(0, 27, 100, 3)
	vcs.write(46, 28, str(errorMsg))

#finishScreen()
#time.sleep(5)
#busnumScreen(5515, 5513, 5516, 5511)
#time.sleep(5)
#runScreen("abc", 5513)
#time.sleep(5)
#cardtagScreen("abc", 1000, 5516, False)
#time.sleep(5)
#runScreen("bcd", 5513)
#time.sleep(5)
#cardtagScreen("bcd", 0, 5516,True, "Communication Error")
#time.sleep(5)
#chargeScreen(5000)
#time.sleep(5)
#chargeFinishScreen(15000)
#time.sleep(5)
#finishScreen()
	
#charge(5000)
#busnumScreen(1515, 1513, 1516, 5516)
#chargeScreen(5000)
#chargeFinishScreen(15000)
#runScreen("abc")
#cardtagScreen("abc", 1000, False)
#cardtagScreen("bcd", 500, True, "CommunicationError")
#errorScreen("Communication Error")
#finish()
#time.sleep(3)
#start()

#while True:
#	tt=time.localtime()
#	tstr = str(tt.tm_hour) + ":" + str(tt.tm_min)+":"+str(tt.tm_sec)
#	if(tt.tm_sec > 30):
#		 break
#	vcs.clearRect(45,25,30,1)
#	vcs.write(45, 25, tstr)
#	time.sleep(0.5)

