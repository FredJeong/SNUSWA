from eventreader import Buttons
import eventreader
import time

eventreader.prevButtonState = [0]*7
while(True):
	time.sleep(0.1)
	eventreader.updateButtonState()
	if(eventreader.isButtonDown(Buttons.VOLUMEUP)):
		print "<<<"
	if(eventreader.isButtonDown(Buttons.VOLUMEDOWN)):
		print ">>>"
