#include <iostream>

int unknown_power();
int car_power(int i);
int truck_power(int i);

int main() {
  std::cout << "unknown power:   " << unknown_power() << std::endl;
  for (int i = 0; i < 3; i++) {
    std::cout << "car   power: " << i << "  " << car_power(i) << std::endl;
    std::cout << "truck power: " << i << "  " << truck_power(i) << std::endl;
  }
  return 0;
}
