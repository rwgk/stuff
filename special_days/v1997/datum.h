#if defined(DATUM_MAIN)
int dfday;
int dfmonth;
int dfyear;
int dfcent;
#else
extern int dfday;
extern int dfmonth;
extern int dfyear;
extern int dfcent;
#endif

int dayoweek(void);
int diffdays(void);
int dateplus(void);
int standard(void);
int report(long lin1, long lin2);
int stardays(void);
int nextoffs(long *days);

int lgetdate(int *day, int* month, int *year);
int str2date(char string[], int *day, int *month, int *year);
int chkdate(int day, int month, int year);
char *dayname(int day, int month, int year);
char *monthname(int month);
long date2lin(int day, int month, int year);
void lin2date(long lin, int *day, int *month, int *year);
