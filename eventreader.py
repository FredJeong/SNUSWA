

prevButtonState = [0]*7
buttonDown 		= [0]*7
buttonUp 		= [0]*7
touchDown		= 0
touchUp			= 0
prevScreenState = 0

class Buttons:
	HOME		= 0
	ENTER		= 1
	MENU		= 2
	BACK		= 3
	SEARCH		= 4
	VOLUMEUP	= 5
	VOLUMEDOWN	= 6


def getButtonState():
	buttonEvent = open('buttonEvents.bin','rb')
	c = buttonEvent.read(7)
	if(len(c) < 7):
		return [-1]
		buttonEvent.close()
	buttonEvent.close()
	return [ord(state) for state in c]

def isButtonDown(btn_id):
	if(btn_id < 0 or btn_id > 6):
		return False
	return buttonDown[btn_id] == 1

def isButtonUp(btn_id):
	if(btn_id < 0 or btn_id > 6):
		return False
	return buttonUp[btn_id] == 1

def isButtonPressed(btn_id):
	if(btn_id < 0 or btn_id > 6):
		return False
	if((state == getButtonState())[0] < 0):
		return False
	return state[btn_id] == 1

def updateButtonState():

	global prevButtonState
	global buttonDown
	global buttonUp
	currentButtonState = getButtonState()
	for i in range(7):
		if(prevButtonState[i] < currentButtonState[i]):
			buttonDown[i] = 1
			buttonUp[i] = 0
		elif(prevButtonState[i] > currentButtonState[i]):
			buttonUp[i] = 1
			buttonDown[i] = 0
		else:
			buttonUp[i] = buttonDown[i] = 0

	prevButtonState = currentButtonState
	
	return 0

def getScreenState():
	screenEvent = open('screenEvents.bin','rb')
	c = screenEvent.read(5)
	if(len(c) < 5):
		return [-1]
	x = ord(c[0])*256 + ord(c[1])
	y = ord(c[2])*256 + ord(c[3])
	if(ord(c[4]) != 0):
		pressed = 1
	else:
		pressed = 0
	screenEvent.close()
	return [x, y, pressed]

def isTouchDown():
	return touchDown == 1

def isTouchUp():
	return touchUp == 1



def updateScreenState():
	global prevScreenState
	global touchUp
	global touchDown
	currentScreenState = getScreenState()
	if(currentScreenState[0] < 0):
		return -1
	if(prevScreenState < currentScreenState[2]):
		touchDown = 1
		touchUp = 0
	elif(prevScreenState < currentScreenState[2]):
		touchUp = 1
		touchDown = 0
	else:
		touchDown = touchUp = 0

	prevScreenState = currentScreenState
	return 0
	