#include <cstring>
#include <iostream>

int main(void) {
  unsigned char raw_bytes[32];
  std::memset(raw_bytes, 0xaa, 32);  // each byte is 10101010
  std::cout << "sizeof(raw_bytes) " << sizeof(raw_bytes) << std::endl;
#define SHOW(T) std::cout << #T << " " << sizeof(T) << " " << *((T*) raw_bytes) << std::endl
  SHOW(unsigned char);
  SHOW(signed char);
  SHOW(unsigned short);
  SHOW(signed short);
  SHOW(unsigned int);
  SHOW(signed int);
  SHOW(unsigned long);
  SHOW(signed long);
  SHOW(unsigned long long);
  SHOW(signed long long);
  SHOW(float);
  SHOW(double);
  SHOW(long double);
  return 0;
}
