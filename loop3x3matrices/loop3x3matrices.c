#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#define MemCpy(t, s, n)  memcpy((t), (s), (n) * sizeof (*(t)))
#define MemCmp(t, s, n)  memcmp((t), (s), (n) * sizeof (*(t)))


static void RotMxMultiply(int *rmxab, const int *rmxa, const int *rmxb)
{
  const int  *a, *b;

  /* no loops to be as fast as posslible */

  a = rmxa;
  b = rmxb;
  *rmxab  = *a++ * *b; b += 3; /* r11 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b; b -= 5;
   rmxab++;

  a = rmxa;
  *rmxab  = *a++ * *b; b += 3; /* r12 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b; b -= 5;
   rmxab++;

  a = rmxa;
  *rmxab  = *a++ * *b; b += 3; /* r13 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a++ * *b; b = rmxb;
   rmxab++;

  rmxa = a;
  *rmxab  = *a++ * *b; b += 3; /* r21 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b; b -= 5;
   rmxab++;

  a = rmxa;
  *rmxab  = *a++ * *b; b += 3; /* r22 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b; b -= 5;
   rmxab++;

  a = rmxa;
  *rmxab  = *a++ * *b; b += 3; /* r23 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a++ * *b; b = rmxb;
   rmxab++;

  rmxa = a;
  *rmxab  = *a++ * *b; b += 3; /* r31 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b; b -= 5;
   rmxab++;

  a = rmxa;
  *rmxab  = *a++ * *b; b += 3; /* r32 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b; b -= 5;
   rmxab++;

  a = rmxa;
  *rmxab  = *a++ * *b; b += 3; /* r33 */
  *rmxab += *a++ * *b; b += 3;
  *rmxab += *a   * *b;
}


static int traceRotMx(const int *RotMx)
{
  return RotMx[0] + RotMx[4] + RotMx[8];
}


static int deterRotMx(const int *RotMx)
{
  int     det;

  det =  RotMx[0] * (RotMx[4] * RotMx[8] - RotMx[5] * RotMx[7]);
  det -= RotMx[1] * (RotMx[3] * RotMx[8] - RotMx[5] * RotMx[6]);
  det += RotMx[2] * (RotMx[3] * RotMx[7] - RotMx[4] * RotMx[6]);

  return det;
}


static int EstimateRtype(const int *RotMx, int deter)
{
  if (deter == -1 || deter == 1)
  {
    switch (traceRotMx(RotMx))
    {
      case -3:                  return -1;
      case -2:                  return -6;
      case -1: if (deter == -1) return -4;
               else             return  2;
      case  0: if (deter == -1) return -3;
               else             return  3;
      case  1: if (deter == -1) return -2;
               else             return  4;
      case  2:                  return  6;
      case  3:                  return  1;
    }
  }

  return 0;
}


static int OrderOfRtype(int Rtype)
{
  if (Rtype > 0) return  Rtype;
  if (Rtype % 2) return -Rtype * 2;
                 return -Rtype;
}


static int IsFiniteOrderRotMx(const int R[9], int Rtype)
{
  int  iO, i;
  int  ProperR[9], MxA[9], MxB[9];
  int  *RR, *RRR, *Swp;

  const int IdentityMx[] = { 1, 0, 0,
                             0, 1, 0,
                             0, 0, 1 };

  MemCpy(ProperR, R, 9);
  if (Rtype < 0) for (i = 0; i < 9; i++) ProperR[i] *= -1;

  MemCpy(MxA, ProperR, 9);
  RR = MxA;
  RRR = MxB;

  for (iO = 1; iO < abs(Rtype); iO++) {
    if (MemCmp(IdentityMx, RR, 9) == 0) return 0;
    RotMxMultiply(RRR, ProperR, RR);
    Swp = RR; RR = RRR; RRR = Swp;
  }

  if (MemCmp(IdentityMx, RR, 9) != 0) return 0;

  return 1;
}


static int CountRotMxOrder(const int *R)
{
  int  MxA[9], MxB[9];
  int  *RR, *RRR, *Swp, iO;

  const int IdentityMx[] = { 1, 0, 0,
                             0, 1, 0,
                             0, 0, 1 };

  int  nIdentity = 0;

  RR = (int *) R;
  RRR = MxA;

  for (iO = 1; iO < 7; iO++)
  {
    RotMxMultiply(RRR, R, RR);
    if (RR == R) RR = MxB;
    Swp = RR; RR = RRR; RRR = Swp;

    if (MemCmp(IdentityMx, RR, 9) == 0) nIdentity++;

    if (MemCmp(R, RR, 9) == 0)
      break;
  }

  if (nIdentity != 1) return -iO;

  return iO;
}


static void Loop3x3Matrices(int Range)
{
#define MaxRange 20
  int  m, i, n;
  int  R[9];
  int  det, Rtype, CountedOrder, nLooped, nUniMod;
  int  EstRtyCounters[13], nEstRty;
  int  RtypeCounters[MaxRange + 1][13];
  int  OrderCounters[MaxRange + 1][7];
  int  nFinite[MaxRange + 1];


  if (Range > MaxRange) {
    printf("ERROR: Range too large. Recompile.\n");
    exit(1);
  }

  nLooped = 0;
  nUniMod = 0;
  for (i = 0; i <= 12; i++) EstRtyCounters[i] = 0;
  for (m = 0; m <= MaxRange; m++)
    for (i = 0; i <= 12; i++) RtypeCounters[m][i] = 0;
  for (m = 0; m <= MaxRange; m++)
    for (i = 0; i <= 6; i++)  OrderCounters[m][i] = 0;
  for (m = 0; m <= MaxRange; m++)
    nFinite[m] = -1;

#define loop(i) for (R[i] = -Range; R[i] <= Range; R[i]++)
  loop(0) loop(1) loop(2)
  loop(3) loop(4) loop(5)
  loop(6) loop(7) loop(8)
#undef loop
  {
    nLooped++;

    det = deterRotMx(R);
    if (det != -1 && det != 1) continue;
    nUniMod++;

        Rtype = EstimateRtype(R, det);
    if (Rtype == 0) continue;
    EstRtyCounters[Rtype + 6]++;

    CountedOrder = CountRotMxOrder(R);
    if (IsFiniteOrderRotMx(R, Rtype) == 0) {
      if (CountedOrder >= 0) {
        printf("ERROR: IsFiniteOrderRotMx()\n");
        exit(1);
      }
      continue;
    }

    if (OrderOfRtype(Rtype) != CountedOrder) {
      printf("ERROR: OrderMismatch %d %d\n",
        OrderOfRtype(Rtype), CountedOrder);
      exit(1);
      continue;
    }

    m = 0; for (i = 0; i < 9; i++) if (m < abs(R[i])) m = abs(R[i]);
    if (m < 1 || m > MaxRange) {
      printf("FATAL INTERNAL ERROR\n");
      exit(1);
    }
    RtypeCounters[m][Rtype + 6]++;
    OrderCounters[m][CountedOrder]++;
  }

  printf("nLooped=%d\n", nLooped);
  printf("nUniMod=%d\n", nUniMod);

  nEstRty = 0;
  for (i = 0; i <= 12; i++) {
    Rtype = i - 6;
    if (Rtype != -5 && Rtype != 0 && Rtype != 5) {
      printf("%d %d\n", Rtype, EstRtyCounters[i]);
      nEstRty += EstRtyCounters[i];
    }
    else if (EstRtyCounters[i] != 0) {
      printf("FATAL INTERNAL ERROR\n");
      exit(1);
    }
  }
  printf("nEstRty=%d\n", nEstRty);

  for (m = 2; m <= Range; m++)
    for (i = 0; i <= 12; i++)
      RtypeCounters[m][i] += RtypeCounters[m - 1][i];

  for (m = 1; m <= Range; m++) {
    n = 0;
    for (i = 0; i <= 12; i++) {
      Rtype = i - 6;
      if (Rtype != -5 && Rtype != 0 && Rtype != 5) {
        printf("R:R=%d %d %d\n", m, Rtype, RtypeCounters[m][i]);
        n += RtypeCounters[m][i];
      }
      else if (RtypeCounters[m][i] != 0) {
        printf("FATAL INTERNAL ERROR\n");
        exit(1);
      }
    }
    printf("R:R=%d SumRtypeCounters=%d\n", m, n);
    nFinite[m] = n;
  }

  for (m = 2; m <= Range; m++)
    for (i = 0; i <= 6; i++)
      OrderCounters[m][i] += OrderCounters[m - 1][i];

  for (m = 1; m <= Range; m++) {
    n = 0;
    for (i = 0; i <= 6; i++) {
      if (i != 0 && i != 5) {
        printf("O:R=%d %d %d\n", m, i, OrderCounters[m][i]);
        n += OrderCounters[m][i];
      }
      else if (OrderCounters[m][i] != 0) {
        printf("FATAL INTERNAL ERROR\n");
        exit(1);
      }
    }
    printf("O:R=%d SumOrderCounters=%d\n", m, n);
    if (nFinite[m] != n) {
      printf("FATAL INTERNAL ERROR\n");
      exit(1);
    }
  }

#undef MaxRange
}


static void usage(void)
{
  printf("usage: loop3x3matrices MaxRange\n");
  exit(1);
}


int main(int argc, char *argv[])
{
  int   Range, n;
  char  xtrac;

  if (argc != 2) usage();

      n = sscanf(argv[1], "%d %c", &Range, &xtrac);
  if (n != 1 || Range < 1) usage();

  Loop3x3Matrices(Range);

  return 0;
}
