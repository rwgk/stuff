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

    // Print all devices names
    for (int i = 0; i < count; i++) {
        CUdevice dev;
        cuDeviceGet(&dev, i);
        char name[100];
        cuDeviceGetName(name, sizeof(name), dev);
        printf("Device %d name: %s\n", i, name);
    }

    return 0;
}
