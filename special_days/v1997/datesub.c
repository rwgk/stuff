#include <stdio.h>
#include <stdlib.h>


#include "datum.h"



int lgetdate (int *day, int *month, int *year)
{
  char buf[128];
  int c, i, errorf;

  i = errorf = 0;
  while ((c=getchar()) != EOF && c != '\n' && ! errorf)
  { if (i < 128)
      buf[i++] = c;
    else
      errorf = 1;
  }
  buf[i] = '\0';

  if (! errorf && i == 1 && buf[0] == '*')
  { *day = dfday; *month = dfmonth; *year = dfyear;}
  else
    errorf = str2date (buf, day, month, year);

  if (! errorf)
  { if (*year < 100) *year += dfcent;
    errorf = chkdate (*day, *month, *year);
  }
  return (errorf);
}

int str2date (char string[], int *day, int *month, int *year)
{
  int i, c, nfld, errorf;
  int fs_1, fs_2, *pn;

  *day = *month = *year = 0;
  errorf = 0;
  fs_1 = '.'; fs_2 = '/';

  nfld = 1;
  i = 0;
  while ((c = string[i++]) != '\0' && ! errorf)
  { if (c != ' ' && (c < '0' || c > '9'))
    { if ((c == fs_1 || c == fs_2) && ++nfld < 4)
        fs_1 = fs_2 = c;
      else
	errorf = 1;
    }
  }
  errorf = nfld != 3;

  if (! errorf)
  {
    string[--i] = fs_1;
    i = nfld = 0;

    while (++nfld < 4)
    { switch(nfld)
      { case 1: pn = day; break;
        case 2: pn = month; break;
        case 3: pn = year;
      }
      while ((c = string[i++]) != fs_1 && ! errorf)
        if (c != ' ')
	{ if (*pn < 2000)
	    *pn = (*pn) * 10 + c - '0';
	  else
	    errorf = 1;
	}
    }
    if (fs_1 == '/') {
      i = *day; *day = *month; *month = i;}
  }
  return (errorf);
}

int chkdate (int day, int month, int year)
{
  static int dayspm[13] =
    {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  int errorf, f29;

  errorf = month < 1 ||  month > 12 ||
	   year < 0 || year > 9999 ||
	   day < 1;

  if (! errorf)
  { f29 = month == 2 &&
	  (year % 4 == 0 && year % 100 != 0 || year % 400 == 0);

    errorf = day > dayspm[month] + f29;
  }
  return (errorf);
}

char *dayname (int day, int month, int year)
{
  static char *name[] =
    {"Samstag", "Sonntag", "Montag", "Dienstag", "Mittwoch",
     "Donnerstag", "Freitag"};

  return (name[date2lin (day, month, year) % 7]);
}

char *monthname (int month)
{
  static char *name[] =
    {"Januar", "Februar", "Maerz", "April", "Mai", "Juni",
     "Juli", "August", "September", "Oktober", "November", "Dezember"};

  return (name[(month > 0) ? --month % 12 : 0]);
}

long date2lin (int day, int month, int year)
{
  static int daysbm[13] =
    {0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
  long lin;

  lin =  ((int) (year/100)) * 36524.25;
  lin += (long) (year%100 * 365.25);
  lin += daysbm[month] - (month < 3 &&
             (year % 4 == 0 && year % 100 != 0 || year % 400 == 0));
  lin += day;

  return (lin);
}

void lin2date (long lin, int  *day, int *month, int *year)
{
  long il, jl;

  *year = lin / 36524.25;
  il = *year * 36524.25;
  lin -= il;
  il = lin / 365.25;
  jl = il * 365.25;
  lin -= jl;
  *year = *year * 100 + (int) il;

  if (lin > 59)
  { *month = (lin * 10 + 323)/ 306;
    *day = lin - (int) ((*month * 306 - 323)/ 10);}
  else
  { lin += *year % 4 == 0 && *year % 100 != 0 || *year % 400 == 0;
    *month = lin / 32 + 1;
    *day = lin - (*month - 1) * 31;
  }
}
