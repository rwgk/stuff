cmake_minimum_required(VERSION 3.5)

find_package(PythonLibs REQUIRED)
find_package(Boost COMPONENTS python REQUIRED)

# Without this, any build libraries automatically have names "lib{x}.so"
set(CMAKE_SHARED_MODULE_PREFIX "")

add_library(test_python_multiple_inheritance MODULE test_python_multiple_inheritance.cpp)
target_link_libraries(test_python_multiple_inheritance ${Boost_LIBRARIES} ${PYTHON_LIBRARIES})
target_include_directories(test_python_multiple_inheritance PRIVATE ${PYTHON_INCLUDE_DIRS})
