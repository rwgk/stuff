#include <cstdlib>
#include <iostream>

#if MYCT == 1
void compile_time_selected_function()
{
  std::cout << "fun1" << std::endl;
}
#elif MYCT == 2
void compile_time_selected_function()
{
  std::cout << "fun2" << std::endl;
}
#endif

void runtime_selected_function()
{
  const char* env_value = std::getenv("MYRT");
  if (!env_value) {
    std::cout << "MYRT not in env." << std::endl;
  }
  else {
    std::cout << "MYRT value from environment: \""
              << env_value << "\"" << std::endl;
  }
}

int main()
{
  compile_time_selected_function();
  runtime_selected_function();
  return 0;
}
