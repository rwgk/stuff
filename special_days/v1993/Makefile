# Beschreibung fuer das Make Kommando

OBJECTS = datum.o datesub.o
INCLUDE = datum.h
FILES = datum.c datesub.c

datum: $(OBJECTS)
	cc $(OBJECTS) -o datum

$(OBJECTS): $(INCLUDE)
	cc -g -c $*.c

clean:
	-rm *.o

lint: $(FILES)
	lint $(FILES)

# vollstaendiges Listing erzeugen
listing:
	-if [ -f 'out' ]; then rm 'out'; else true; fi
	-aus="${FILES}"; \
	 for file in $$aus; do \
	   cat $$file >> out; \
	   echo ' ' >> out; \
	   echo ' ' >> out; \
	 done
	-if [ -f 'out' ]; then drumuc -2 out | lpr -h; rm out; else true; fi
