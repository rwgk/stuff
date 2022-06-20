#include <iostream>

int car_power();
int truck_power();

int main() {
  std::cout << "START main()" << std::endl;
  int pwr = 0;
  pwr = car_power();
  std::cout << "car   power: " << pwr << std::endl;
  pwr = truck_power();
  std::cout << "truck power: " << pwr << std::endl;
  return 0;
}
