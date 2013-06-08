

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


