#include <stdio.h>



int main()
{
	char buf[16];
	const char* OUTFILE = "buttonEvents.bin";
	FILE* buttonEvent = fopen("/dev/input/event0", "rb");
	FILE* fout = fopen(OUTFILE, "wb");

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
		int size;
		while((size= fread(buf,1,16,buttonEvent))>=0)
		{
			if(size<16) continue;
			if(!buttonEvent) break;
			if(buf[8] != 1) continue;
			int i;
			for(i = 0; i < 7; i++)
			{
				if(buf[10] == buttons[i])
				{
					buttonStatus[i] = buf[12] ;
					fseek(fout,0,0);
					fwrite(buttonStatus,1,7,fout);
					fflush(fout);
				}
			}
		}
	}
	fclose(fout);
	fclose(buttonEvent);
	return 0;
}

			

