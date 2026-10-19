#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <math.h>

  int main
 (){while(
 1){float 
  a,b,c,d
  ,e;for
  (a=0;a<
  6.28;a+=
.1){for(b=2
;b>=0;b-=.1)
{for(c=-1;c<1
 ;c+=.05){d=cos
 (a)*(1.4*acos(
  1/(b+1))-1.2)-
   c;e=.2*pow(2.72
    ,-pow(1.2*b-1.1,8
     ));printf("%c",fabs
        (d)<e?".:-=+*#%@"
         [(int)((cos(acos((
          d)/e)+a)+1)*4.5)]:
              ' ');}printf("\n")
                   ;}usleep(99999
		                      );}}}
