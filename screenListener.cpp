#include <fstream>

using namespace std;

int main()
{
	char buf[16];
	ifstream screenEvent ("/dev/input/event1",ios::in | ios::binary);
	const char* OUTFILE = "/root/screenEvents.bin";

	char screenStatus[5] = {0,};		//{ Xpos_H, Xpos_L, Ypos_H, Ypos_L, Pressed }


	while(1)
	{
		if(!screenEvent) break;
		while(screenEvent.read(buf,16))
		{
			if(buf[8] == buf[11] == 1 && buf[10] == 0x4a)
			{
				if(buf[12] == 1)		//Pressed
				{
					screenStatus[4] = 1;
				}
				if(buf[12] == 0)		//Released
				{
					screenStatus[4] = 0;
				}

				ofstream fout (OUTFILE, ios::out | ios::binary);
				fout.write(screenStatus,5);
				fout.close();
			}
			else if(buf[8] == 3)
			{
				if(buf[10] == 0)		//X_pos
				{
					screenStatus[0] = buf[13];
					screenStatus[1] = buf[12];
				}
				else if(buf[10] == 1)	//Y_pos
				{
					screenStatus[2] = buf[13];
					screenStatus[3] = buf[12];
				}
				ofstream fout (OUTFILE, ios::out | ios::binary);
				fout.write(screenStatus,5);
				fout.close();
			}
		}
	}
	screenEvent.close();
	return 0;
}

			

