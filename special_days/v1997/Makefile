#

objects = datum.o datesub.o

CC = cc
CCFLAGS = -xansi -fullwarn -wlint -woff 822,826,827,852

datum: $(objects)
	$(CC) $(CCFLAGS) -o datum $(objects)

clean:
	rm -f datum $(objects)

$(objects): datum.h

.c.o:
	$(CC) $(CCFLAGS) -c $*.c
