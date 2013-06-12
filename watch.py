import time
import vcs

vcs.clearRect(3,3,40,1)
while(True):
	time.sleep(0.1)
	f = open('screenEvents.bin','rb')
	c = f.read(5);
	if(len(c)<5):
		continue
	x = ord(c[0])*256 + ord(c[1])
	y = ord(c[2])*256 + ord(c[3])
	msg = '(' + str(x)+', '+str(y)+')        '
	vcs.write(3,3,msg)
	vcs.write(3,4,str(ord(c[4]))+'  ')
	f.close()

	
