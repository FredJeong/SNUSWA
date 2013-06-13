#include <stdlib.h>

void main()
{
	system("ifconfig usb0 192.168.10.11/24 up");
	system("mount -t nfs -o nolock 192.168.10.10:/root/nfs /mnt/nfs");
	system("export PATH=$PATH:$HOME/python");
}
