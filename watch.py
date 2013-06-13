import time
import vcs
import eventreader

vcs.clearRect(3,3,40,1)

def b2ic(b):
	if(b): return '1'
	return '0'

while(True):
	time.sleep(0.5)
	eventreader.updateButtonState()
	l=[]
	for i in range(7):
		l.append(eventreader.isButtonDown(i))
	
	vcs.write(3,4,''.join([b2ic(c) for c in l]))

	
