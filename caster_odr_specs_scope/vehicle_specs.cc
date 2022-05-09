#include <iostream>

int unknown_power();
int car_power();
int truck_power();

int main() {
  std::cout << "unknown power:   " << unknown_power() << std::endl;
  std::cout << "car     power:   " << car_power() << std::endl;
  std::cout << "truck   power:   " << truck_power() << std::endl;
  return 0;
}
