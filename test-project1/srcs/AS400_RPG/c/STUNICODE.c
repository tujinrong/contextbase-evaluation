/* ILE C / ICU option 39. UTF16 pointers exclude RPG varying prefixes.
 * Errors: 1 required, 2 scalar/UTF16/control/length, 3 format, 4 conversion.
 * No replacement conversion: an unrepresentable scalar must use explicit F8.
 */
#include "STUNICODE.h"
#include <stdlib.h>
#include <string.h>
#include <unicode/uchar.h>
#include <unicode/unorm.h>
#include <unicode/ustring.h>
#include <unicode/ucnv.h>
#include <unicode/ucnv_err.h>

static int32_t scalar(const uint16_t *s,int32_t n,int32_t *i,uint32_t *cp) {
    uint32_t a;
    if (*i>=n) return 0;
    a=s[(*i)++];
    if (a>=0xd800 && a<=0xdbff) {
        uint32_t b;
        if (*i>=n || (b=s[(*i)++])<0xdc00 || b>0xdfff) return -1;
        a=0x10000+((a-0xd800)<<10)+(b-0xdc00);
    } else if(a>=0xdc00 && a<=0xdfff) return -1;
    *cp=a; return 1;
}
int32_t StUnicodeScalars(const uint16_t *s,int32_t n) {
    int32_t i=0,c=0,r;uint32_t cp;
    if(n<0 || (!s && n)) return -1;
    while((r=scalar(s,n,&i,&cp))>0) c++;
    return r<0?-1:c;
}
static int put(uint16_t *s,int32_t cap,int32_t *n,uint32_t cp) {
    int32_t need=cp>0xffff?2:1;
    if(*n+need>cap || cp>0x10ffff || (cp>=0xd800 && cp<=0xdfff)) return 0;
    if(need==2) { cp-=0x10000;s[(*n)++]=(uint16_t)(0xd800+(cp>>10));s[(*n)++]=(uint16_t)(0xdc00+(cp&0x3ff)); }
    else s[(*n)++]=(uint16_t)cp;
    return 1;
}
static int white(uint32_t cp) { return u_isUWhiteSpace((UChar32)cp); }
static int ascii_digit(uint32_t cp) { return cp>=0x30 && cp<=0x39; }
static int ascii_letter(uint32_t cp) { return (cp>=0x41&&cp<=0x5a)||(cp>=0x61&&cp<=0x7a); }
static int hyphen(uint32_t cp) { return cp==0x2d||cp==0x2010||cp==0x2011||cp==0x2212; }
static int email(uint16_t *s,int32_t n) {
    int32_t at=-1,i,start;
    for(i=0;i<n;i++) {
        if(s[i]==0x40) { if(at>=0) return 0;at=i; }
        if(s[i]>0x7f || s[i]<0x21) return 0;
    }
    if(at<=0||at==n-1||s[0]==0x2e||s[at-1]==0x2e) return 0;
    for(i=0;i<at;i++) {
        uint32_t c=s[i];
        if(!(ascii_letter(c)||ascii_digit(c)||c==0x2e||c==0x21||c==0x23||c==0x24||c==0x25||c==0x26||c==0x27||c==0x2a||c==0x2b||c==0x2d||c==0x2f||c==0x3d||c==0x3f||c==0x5e||c==0x5f||c==0x60||c==0x7b||c==0x7c||c==0x7d||c==0x7e)) return 0;
        if(c==0x2e&&i&&s[i-1]==0x2e) return 0;
    }
    start=at+1;
    for(i=start;i<=n;i++) {
        if(i==n||s[i]==0x2e) {
            if(i==start||i-start>63||s[start]==0x2d||s[i-1]==0x2d) return 0;
            start=i+1;
        } else {
            if(!(ascii_letter(s[i])||ascii_digit(s[i])||s[i]==0x2d)) return 0;
            if(s[i]>=0x41&&s[i]<=0x5a) s[i]+=0x20;
        }
    }
    return 1;
}
int32_t StUnicodeNormalize(const uint16_t *input,int32_t units,int32_t rawMax,int32_t savedMax,int32_t mode,int32_t required,uint16_t *output,int32_t capacity,int32_t *written) {
    UChar stage[4096],norm[4096],upper[4096];
    int32_t i=0,n=0,m=0,start=0,end,c;uint32_t cp;UErrorCode error=U_ZERO_ERROR;
    *written=0;c=StUnicodeScalars(input,units);
    if(c<0||c>rawMax||units>2048) return 2;
    while(scalar(input,units,&i,&cp)>0) {
        if(mode==1&&cp==0x0d) { if(i<units&&input[i]==0x0a) i++;cp=0x0a; }
        if(u_charType((UChar32)cp)==U_CONTROL_CHAR && !(mode==1&&cp==0x0a)) return 2;
        if(!put(stage,4096,&n,cp)) return 2;
    }
    /* Unicode trim occurs at scalar boundaries. */
    while(start<n) { int32_t p=start;scalar(stage,n,&p,&cp);if(!white(cp))break;start=p; }
    end=n;while(end>start) { int32_t p=end-1;if(stage[p]>=0xdc00&&stage[p]<=0xdfff)p--;int32_t q=p;scalar(stage,n,&q,&cp);if(!white(cp))break;end=p; }
    n=end-start;memmove(stage,stage+start,(size_t)n*2);
    if(!n) return required?1:0;
    if((mode>=2&&mode<=8) || mode==10 || mode==11) {
        m=unorm_normalize(stage,n,UNORM_NFKC,0,norm,4096,&error);
        if(U_FAILURE(error)||m>4096) return 2;
    } else { m=n;memcpy(norm,stage,(size_t)n*2); }
    if(mode==2||mode==5) {
        n=u_strToUpper(upper,4096,norm,m,"",&error);
        if(U_FAILURE(error)||n>4096) return 2;
        memcpy(norm,upper,(size_t)n*2);m=n;
    }
    i=0;n=0;int pending=0;
    while(scalar(norm,m,&i,&cp)>0) {
        if(mode==2||mode==4||mode==7||mode==8) { if(white(cp))continue; }
        if(mode==7||mode==8) { if(hyphen(cp)||(mode==8&&(cp==0x28||cp==0x29)))continue; }
        if(mode==3||mode==4) {
            if(white(cp)) { pending=n>0;continue; }
            if((cp>=0x3041&&cp<=0x3096)||cp==0x309d||cp==0x309e) cp+=0x60;
            if(!((cp>=0x30a1&&cp<=0x30fa)||cp==0x30fc||cp==0x30fb||cp==0x30fd||cp==0x30fe)) return 3;
            if(mode==3&&pending) { if(!put(output,capacity,&n,0x20))return 2;pending=0; }
        }
        if(!put(output,capacity,&n,cp)) return 2;
    }
    c=StUnicodeScalars(output,n);if(c<0||c>savedMax) return 2;
    if(mode==5) {
        if(!n||!(ascii_letter(output[0])||ascii_digit(output[0]))) return 3;
        for(i=0;i<n;i++) if(!((output[i]>=0x41&&output[i]<=0x5a)||ascii_digit(output[i])||output[i]==0x2d))return 3;
    } else if(mode==6) {
        for(i=0;i<n;i++) if(!ascii_digit(output[i]))return 3;
        if(n!=savedMax) return 3;
    } else if(mode==7) {
        if(n!=7) return 3;for(i=0;i<n;i++)if(!ascii_digit(output[i]))return 3;
    } else if(mode==8) {
        int begin=output[0]==0x2b?1:0;
        if(begin) { if(n<8||n>16||output[1]==0x30)return 3; }
        else if((n!=10&&n!=11)||output[0]!=0x30) return 3;
        for(i=begin;i<n;i++)if(!ascii_digit(output[i]))return 3;
    } else if(mode==9 && !email(output,n)) return 3;
    else if(mode==10) {
        if(n!=10||output[4]!=0x2d||output[7]!=0x2d) return 3;
        for(i=0;i<n;i++)if(i!=4&&i!=7&&!ascii_digit(output[i]))return 3;
    } else if(mode==11 || mode==12) { for(i=0;i<n;i++)if(!ascii_digit(output[i]))return 3; }
    *written=n;return 0;
}
int32_t StUnicodeToJob(const uint16_t *input,int32_t units,int32_t ccsid,char *output,int32_t capacity,int32_t *written) {
    UErrorCode e=U_ZERO_ERROR;UConverter *c=ucnv_openCCSID(ccsid,UCNV_IBM,&e);
    *written=0;if(U_FAILURE(e)||!c)return 4;
    ucnv_setFromUCallBack(c,UCNV_FROM_U_CALLBACK_STOP,0,0,0,&e);
    *written=ucnv_fromUChars(c,output,capacity,input,units,&e);ucnv_close(c);
    if(U_FAILURE(e)||*written>capacity) { *written=0;return 4; }return 0;
}
int32_t StUnicodeFromJob(const char *input,int32_t bytes,int32_t ccsid,uint16_t *output,int32_t capacity,int32_t *written) {
    UErrorCode e=U_ZERO_ERROR;UConverter *c=ucnv_openCCSID(ccsid,UCNV_IBM,&e);
    *written=0;if(U_FAILURE(e)||!c)return 4;
    ucnv_setToUCallBack(c,UCNV_TO_U_CALLBACK_STOP,0,0,0,&e);
    *written=ucnv_toUChars(c,output,capacity,input,bytes,&e);ucnv_close(c);
    if(U_FAILURE(e)||*written>capacity||StUnicodeScalars(output,*written)<0) { *written=0;return 4; }return 0;
}
int32_t StUnicodeEscape(const uint16_t *input,int32_t units,int32_t decode,uint16_t *out,int32_t capacity,int32_t *written) {
    int32_t i=0,n=0;uint32_t cp;const uint16_t hex[]={0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x41,0x42,0x43,0x44,0x45,0x46};
    *written=0;if(StUnicodeScalars(input,units)<0)return 2;
    while(scalar(input,units,&i,&cp)>0) {
        if(decode&&cp==0x5c) {
            if(i>=units)return 3;
            if(input[i]==0x5c) { i++;cp=0x5c; }
            else if(input[i]==0x75&&i+1<units&&input[i+1]==0x7b) {
                int digits=0;i+=2;cp=0;
                while(i<units&&input[i]!=0x7d) {
                    uint32_t v=input[i++];int d;
                    if(v>=0x30&&v<=0x39)d=v-0x30;else if(v>=0x41&&v<=0x46)d=v-0x41+10;else if(v>=0x61&&v<=0x66)d=v-0x61+10;else return 3;
                    if(++digits>6)return 3;cp=cp*16+d;
                }
                if(!digits||i>=units||input[i++]!=0x7d)return 3;
            } else return 3;
            if(!put(out,capacity,&n,cp))return 3;
        } else if(!decode) {
            if(cp==0x5c) { if(!put(out,capacity,&n,0x5c)||!put(out,capacity,&n,0x5c))return 2; }
            else if(cp>=0x20&&cp<0x7f) { if(!put(out,capacity,&n,cp))return 2; }
            else {
                uint32_t v=cp;int k=0,j;uint16_t buf[6];
                do { buf[k++]=hex[v&15];v>>=4; }while(v);
                if(!put(out,capacity,&n,0x5c)||!put(out,capacity,&n,0x75)||!put(out,capacity,&n,0x7b))return 2;
                for(j=k-1;j>=0;j--)if(!put(out,capacity,&n,buf[j]))return 2;
                if(!put(out,capacity,&n,0x7d))return 2;
            }
        } else if(!put(out,capacity,&n,cp))return 2;
    }
    *written=n;return 0;
}

/* SHA-256 over explicit big-endian UTF16 units, independent of host endian. */
static const uint32_t K[64]={
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static uint32_t rr(uint32_t x,int n){return (x>>n)|(x<<(32-n));}
static void block(uint32_t h[8],const unsigned char p[64]) {
 uint32_t w[64],a,b,c,d,e,f,g,k,t1,t2;int i;
 for(i=0;i<16;i++)w[i]=((uint32_t)p[4*i]<<24)|((uint32_t)p[4*i+1]<<16)|((uint32_t)p[4*i+2]<<8)|p[4*i+3];
 for(i=16;i<64;i++)w[i]=(rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>10))+w[i-7]+(rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>3))+w[i-16];
 a=h[0];b=h[1];c=h[2];d=h[3];e=h[4];f=h[5];g=h[6];k=h[7];
 for(i=0;i<64;i++){t1=k+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^((~e)&g))+K[i]+w[i];t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));k=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
 h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=k;
}
void StUnicodeDigest(const uint16_t *s,int32_t units,char out[64]) {
 uint32_t h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
 unsigned char p[64];int32_t i,n=0;uint64_t bits=(uint64_t)units*16;const char *hex="0123456789abcdef";
 for(i=0;i<units;i++){p[n++]=(unsigned char)(s[i]>>8);p[n++]=(unsigned char)s[i];if(n==64){block(h,p);n=0;}}
 p[n++]=0x80;if(n>56){memset(p+n,0,64-n);block(h,p);n=0;}memset(p+n,0,56-n);
 for(i=0;i<8;i++)p[63-i]=(unsigned char)(bits>>(i*8));block(h,p);
 for(i=0;i<32;i++){unsigned char v=(unsigned char)(h[i/4]>>(24-8*(i%4)));out[2*i]=hex[v>>4];out[2*i+1]=hex[v&15];}
}
