#include <stdio.h>
#include <stdlib.h>
#include <time.h>


#define DATUM_MAIN
#include "datum.h"


#define DATEOUT "%10s: %2d.%02d.%d"


int main(void)
{
  int i, c;

  time_t      t;
  struct tm   *currtime;

  t = time(0);
  currtime = localtime(&t);

  dfday = currtime->tm_mday;
  dfmonth = currtime->tm_mon + 1;
  dfyear = currtime->tm_year + 1900;
  dfcent = (dfyear / 100) * 100;

  do
   {/*      menue        */

    printf("\n\n\nD A T U M   B E R E C H N U N G E N                 ");
    printf(DATEOUT, dayname (dfday, dfmonth, dfyear),
		    dfday, dfmonth, dfyear); printf("\n");
      for (i=1; i<75; i++) putchar('='); printf("\n\n");
    printf("(1)  Wochentag bei gegebenem Datum\n");
    printf("(2)  Tage zwischen zwei Daten\n");
    printf("(3)  End-Datum = Anfangs-Datum + Tage\n");
    printf("(4)  Liste besonderer Tage\n");
    printf("(5)  Standard-Datum eingeben\n");
    printf("(6)  E n d e\n");
    printf("\nAuswahl: ");

    c = ' ';
    while ((i = getchar()) != '\n')
      if (c == ' ') c = i;

    switch (c)
    { case '1': dayoweek(); break;
      case '2': diffdays(); break;
      case '3': dateplus(); break;
      case '4': stardays(); break;
      case '5': standard();
    }
   }
  while (c != '6');

  printf("\n\nBye, bye...\n\n");

  exit(0);
  return 0;
}

int dayoweek(void)
{
  int day, month, year;

  printf("\n\n\nWochentag bei gegebenem Datum\n\n");

  do
    printf("Datum: ");
  while (lgetdate (&day, &month, &year));

  printf("\n");
  printf("\n\n\nWochentag bei gegebenem Datum:\n\n");
  printf(DATEOUT, dayname (day, month, year), day, month, year);
  printf("\n\n\nWeiter mit <RETURN>");

  while (getchar() != '\n');
  return (0);
}

int diffdays(void)
{
  int  day, month, year;
  long lin1, lin2;

  printf("\n\n\nTage zwischen zwei Daten\n\n");

  do
    printf("1. Datum: ");
  while (lgetdate (&day, &month, &year));
  lin1 = date2lin (day, month, year);

  do
    printf("2. Datum: ");
  while (lgetdate (&day, &month, &year));
  lin2 = date2lin (day, month, year);

  report (lin1, lin2);
  return (0);
}

int dateplus(void)
{
  int  day, month, year;
  long il, lin1, lin2;

  printf("\n\n\nEnd-Datum = Anfangs-Datum + Tage\n\n");

  do
    printf("Anfangs-Datum: ");
  while (lgetdate (&day, &month, &year));
  lin1 = date2lin (day, month, year);

  do
    printf("Tage bis zum End-Datum: ");
  while (scanf("%ld", &il) != 1);
  lin2 = lin1 + il;

  while (getchar() != '\n');

  report (lin1, lin2);
  return (0);
}

int standard(void)
{
  printf("\n\n\nEingabe Standarddatum\n\n");

  do
    printf("Datum: ");
  while (lgetdate (&dfday, &dfmonth, &dfyear));

  return (0);
}

int report (long lin1, long lin2)
{
  int  day, month, year;
  long il;

  if (lin2 < lin1) {il = lin1; lin1 = lin2; lin2 = il;}

  printf("\n\n\nZwischen     "); lin2date (lin1, &day, &month, &year);
  printf(DATEOUT, dayname (day, month, year), day, month, year);
  printf(  "\n\n     und     "); lin2date (lin2, &day, &month, &year);
  printf(DATEOUT, dayname (day, month, year), day, month, year);
  printf("\n\n");
  if (lin2 - lin1 == 1)
    printf("                  liegt ein Tag.");
  else
    printf("                  liegen %d Tage.", lin2 - lin1);

  printf("\n\n\nWeiter mit <RETURN>");

  while (getchar() != '\n');
  return (0);
}

int stardays(void)
{
  int  day0, month0, year0;
  int  day, month, year;
  long yearage;
  long il, lin1, lin2;

  FILE *opfile;

  printf("\n\n\nListe besonderer Tage\n\n");

  do
    printf("Anfangs-Datum: ");
  while (lgetdate (&day0, &month0, &year0));
  lin1 = date2lin (day0, month0, year0);

  printf("Wochentag          Datum                    Alter in Tagen");
  printf("   Alter in Jahren\n\n");

  opfile = fopen("Liste","w");

  if (opfile != NULL)
  { fprintf(opfile,
	    "Wochentag          Datum                    Alter in Tagen");
    fprintf(opfile, "   Alter in Jahren\n\n");
  }

  il = 0;
  lin2 = lin1;
  while (il < 44445)
  { lin2date (lin2 + il, &day, &month, &year);
    yearage = (long) (year - year0 -
		      (month < month0 || (month == month0 && day < day0)));

    printf("%-19s%2d. %-9s%6d%15ld%15ld\n",
            dayname (day, month, year),
	    day, monthname (month), year,
	    il, yearage);

    if (opfile != NULL)
    { fprintf(opfile, "%-19s%2d. %-9s%6d%15ld%15ld\n",
              dayname (day, month, year),
	      day, monthname (month), year,
	      il, yearage);
    }
    nextoffs (&il);
  }
  if (opfile != NULL) fclose (opfile);

  printf("\n\nWeiter mit <RETURN>");

  while (getchar() != '\n');

  return (0);
}

int nextoffs (long *days)
{
  long il;

  if (*days < 100)
    *days = 100;

  else if (*days < 999)
  { il = *days / 100;
    *days = (*days % 10) ? 100 * ++il : 111 * il;}

  else if (*days == 999)
    *days = 1000;

  else if (*days < 9999)
  { il = *days / 1000;
    *days = (*days % 10) ? 1000 * ++il : 1111 * il;}

  else if (*days == 9999)
    *days = 10000;

  else
  { il = *days + (long) (*days / 10000) * 111;
    if (il % 11111 == 0)
      *days = il;
    else
      *days = (long) (*days / 1000 + 1) * 1000;
  }
  return(0);
}
