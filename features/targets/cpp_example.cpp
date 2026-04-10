//c lib using cpp conv
#include <cstdio>
//c++ lib
#include <iostream>
#include <string>
//c++17 libs
#include <filesystem>
#include <optional>
//c++26 libs
#include <ranges>


namespace example
{
   class base {
        public:
            virtual void greet() const {}
    };
    class derived : public base {
        public:
            void greet() const override {
                std::cout << "Hello from derived class!" << std::endl;
            }
    };

    void cpp_example() {
        std::cout << "Hello from C++!" << std::endl;

        // Using C++17 filesystem
        std::filesystem::path path = "example.txt";
        if (std::filesystem::exists(path)) {
            std::cout << "File exists: " << path << std::endl;
        } else {
            std::cout << "File does not exist: " << path << std::
        }
    }
}