#include <stdio.h>
#include <cuda.h>

int main(void) {
    CUresult res;

    // Initialize the CUDA driver API
    res = cuInit(0);
    if (res != CUDA_SUCCESS) {
        fprintf(stderr, "cuInit failed with error code %d\n", res);
        return 1;
    }

    // Get the number of CUDA devices
    int count = 0;
    res = cuDeviceGetCount(&count);
    if (res != CUDA_SUCCESS) {
        fprintf(stderr, "cuDeviceGetCount failed with error code %d\n", res);
        return 1;
    }

    printf("Number of CUDA devices: %d\n", count);

    // Print name of first device (if available)
    if (count > 0) {
        CUdevice dev;
        cuDeviceGet(&dev, 0);
        char name[100];
        cuDeviceGetName(name, sizeof(name), dev);
        printf("Device 0 name: %s\n", name);
    }

    return 0;
}
