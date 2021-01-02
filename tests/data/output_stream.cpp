#include <ctp/ctp.hpp>

constexpr auto test() {
	ctp::print(1);
	ctp::print(ctp::stdout, 1);
	ctp::printf(ctp::stdout, "Log {}\n", 1);

	ctp::print(ctp::stderr, 1);
	ctp::printf(ctp::stderr, "Log {}\n", 1);
	return 0;
}

constexpr auto i = test();
