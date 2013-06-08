

def openW():
	return open('/dev/vcs','w')

def getContent():
	f = open('/dev/vcs','r')
	content = f.read()
	f.close()
	return content

def write(x,y,string):
	content = getContent()
	pos = x + y * 100
	content = list(content)
	content[pos:pos + len(string)] = list(string)
	f = openW()
	f.write("".join(content))
	f.close()

def clear():
	f = openW()
	f.write(" "*100*30)
	f.close()

def clearRect(x,y,width,height):
	for i in range(y, y + height):
		write(x, i, " " * width)

def drawRect(x,y,width,height,clear = True):
	write(x, y, "-" * width)
	write(x, y + height - 1, "-" * width)
	for i in range(y + 1, y + height - 1):
		if(clear):
			write(x, i, "|" + " " * (width - 2) + "|")
		else:
			write(x, i, "|")
			write(x + width - 1, i, "|")


