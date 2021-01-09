#include <ctp/ctp.hpp>

constexpr int fib(int n) {
	if (n <= 1) {
		if (n == 1) {
			ctp::printf("{} + ", n);
		}
		return n;
	}
	return fib(n - 1) + fib(n - 2);
}

constexpr auto test() {
	ctp::printf("0 = {}\n", fib(6));
	return true;
}

constexpr auto i = test();
