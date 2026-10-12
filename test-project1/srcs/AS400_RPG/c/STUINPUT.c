/* Approved UTF8 IFS reader. Caller authority and directory ACL are deployment prerequisites.
 * No shell, command interpolation, role hint or DB credential is accepted from input.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/stat.h>
#include <unicode/ustring.h>
#if defined(__OS400__)
#include <unistd.h>
#endif
static FILE *approved;
int32_t StApprovedOpen(const char *path,int32_t bytes) {
 char name[512];struct stat st;int i;const char *prefix="/stuapp/approved/";
 if(approved){fclose(approved);approved=0;}
 if(bytes<17||bytes>=512)return 1;
 memcpy(name,path,(size_t)bytes);name[bytes]=0;
 if(memchr(name,0,(size_t)bytes)||strncmp(name,prefix,strlen(prefix))||strstr(name,"..")||strchr(name,'\\'))return 1;
 /* Leaf names only: no nested path or alternate traversal is accepted. */
 if(strchr(name+strlen(prefix),'/'))return 1;
 for(i=(int)strlen(prefix);i<bytes;i++)if(!strchr("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-",name[i]))return 1;
 if(bytes<20||strcmp(name+bytes-4,".txt"))return 1;
#if defined(__OS400__)
 if(lstat(name,&st)||!S_ISREG(st.st_mode))return 1;
#else
 if(stat(name,&st)||!(st.st_mode&S_IFREG))return 1;
#endif
 approved=fopen(name,"rb");return approved?0:1;
}
int32_t StApprovedLine(uint16_t *out,int32_t capacity,int32_t *written) {
 char line[8192];size_t n=0;int next;UErrorCode error=U_ZERO_ERROR;
 *written=0;if(!approved)return -1;
 while((next=fgetc(approved))!=EOF) {
  if(next==0||n>=sizeof(line)-1)return -1;
  line[n++]=(char)next;if(next=='\n')break;
 }
 if(!n)return feof(approved)?0:-1;
 if(ferror(approved))return -1;
 while(n&&(line[n-1]=='\n'||line[n-1]=='\r'))--n;
 u_strFromUTF8(out,capacity,written,line,(int32_t)n,&error);
 if(U_FAILURE(error)){*written=0;return -1;}return 1;
}
void StApprovedClose(void){if(approved){fclose(approved);approved=0;}}
