#include <iostream>

int add(int a, int b) {
    return a + b;
}

int main() {
    if(add(1,2)){
    add(2,3);
    }else{
    add(3,4);
    }
    std::cout << "Hello, C++!" << std::endl;
    return 0;
}
