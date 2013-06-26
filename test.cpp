#include <stdio.h>

int main()
{
	FILE* fout = fopen("dummy.txt","wb");
	char buf[10] = "hello";
	for(int i = 0; i< 10; i++)
	{
		fseek(fout,0,0);
		fwrite(buf,1,6,fout);
		fflush(fout);
		if(i == 8) buf[3] = 'L';
	}
	
	return 0;
}
