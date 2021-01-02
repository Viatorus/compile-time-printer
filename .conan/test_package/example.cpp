#include <ctp/ctp.hpp>

#include <iostream>
#include <string>
#include <vector>

constexpr int get() {
	ctp::print(1, ctp::type<std::vector<std::string>>{}, 1.012f, ctp::type{1});
	ctp::printf("{} - {} = {}", 5.9, 42, 5.9 - 42);
	return 0;
}

constexpr auto test = get();

int main() {
	return 0;
}
