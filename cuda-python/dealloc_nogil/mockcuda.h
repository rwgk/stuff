#ifndef MOCKCUDA_H
#define MOCKCUDA_H
#ifdef __cplusplus
extern "C" {
#endif

void mockcuda_init(void);     // start a background thread grabbing an internal lock
void mockcuda_shutdown(void); // stop it
void mockcuda_free(void* p);  // pretend "driver" free (takes an internal lock, then free)

#ifdef __cplusplus
}
#endif
#endif
