#include <ctp/ctp.hpp>

constexpr int fib(int n, const ctp::noise& noise) {
	if (n <= 1) {
		if (n == 1) {
			ctp::printf("{} + ", n);
		}
		return n;
	}
	return fib(n - 1, noise) + fib(n - 2, noise);
}

constexpr auto test() {
	ctp::noise n{};
	ctp::printf("0 = {}\n", fib(6, n));
	return true;
}

constexpr auto i = test();
