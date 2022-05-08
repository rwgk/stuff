#include <iostream>

int short_car_power();
int long_car_power();
int short_truck_power();
int long_truck_power();

int main() {
  std::cout << "short car   power:   " << short_car_power() << std::endl;
  std::cout << "long  car   power:   " << long_car_power() << std::endl;
  std::cout << "short truck power:   " << short_truck_power() << std::endl;
  std::cout << "long  truck power:   " << long_truck_power() << std::endl;
  return 0;
}
