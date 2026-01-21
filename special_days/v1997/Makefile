#

objects = datum.o datesub.o

CC = cc
CCFLAGS =

datum: $(objects)
	$(CC) $(CCFLAGS) -o datum $(objects)

clean:
	rm -f datum $(objects)

$(objects): datum.h

.c.o:
	$(CC) $(CCFLAGS) -c $*.c
