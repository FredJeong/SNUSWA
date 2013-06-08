#include <fstream>
#include <iostream>

using namespace std;

int main()
{
	char buf[16];
	ifstream buttonEvent ("/dev/input/event0",ios::in | ios::binary);
	const char* OUTFILE = "/root/buttonEvents.bin";

	const unsigned char SEARCH		= 0xD9;
	const unsigned char VOLUMEUP	= 0x73;
	const unsigned char VOLUMEDOWN	= 0x72;
	const unsigned char HOME		= 0x66;
	const unsigned char ENTER		= 0x1C;
	const unsigned char MENU		= 0x8B;
	const unsigned char BACK		= 0x9E;
	
	const char buttons[] = {HOME, ENTER, MENU, BACK, SEARCH, VOLUMEUP, VOLUMEDOWN};
	char buttonStatus[7] = {0,};

	while(1)
	{
		if(!buttonEvent) 
		{
			break;
		}
		while(buttonEvent.read(buf,16))
		{
			if(!buttonEvent) break;
			if(buf[8] != 1) continue;
			for(int i = 0; i < 7; i++)
			{
				if(buf[10] == buttons[i])
				{
					buttonStatus[i] = buf[12];
					ofstream fout(OUTFILE, ios::out | ios::binary);
					fout.write(buttonStatus,7);
					fout.close();
					break;
				}
			}
		}
	}
	buttonEvent.close();
	return 0;
}

			

