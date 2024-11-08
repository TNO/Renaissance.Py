#include <stdio.h>

static int static_int = 2;

#define A_DEFINE (4 + static_int)
#define B_DEFINE (A_DEFINE + static_int)

#define FC_MACRO(arg)\
do{\
   arg += A_DEFINE;\
} while(0)

class A {
public:
    A() {
        printf("A constructor\n");
    }
    ~A() {
        printf("A destructor\n");
    }
    protected:
    int a;
    virtual void testA() {
        printf("A test\n");
    }
};

class B: public A {
public:
    B() {
        printf("B constructor\n");
    }
    ~B() {
        printf("B destructor\n");
    }
    public:
    int b;
    virtual int testB(int x, const char *y) {
        this->testA();
        printf("B *s test %d\n", y, x);
        return x;
    }
    void testA() {
        A::testA();
    }
};

static void test() {
    static A a;
    B b;
    b.testB(1, "test");
    b.testA();
}
int main() {
    test ();
    return 0;
}