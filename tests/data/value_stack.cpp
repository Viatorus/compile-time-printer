#include <ctp/ctp.hpp>

#include <algorithm>

template<typename T>
using stack = std::array<T, 3>;

template<typename T>
constexpr auto push(stack<T>& s, T value) {
	// Find zero.
	auto* it = s.begin();
	while (it != s.end() && *it != 0) {
		++it;
	}
	if (it != s.end()) {
		ctp::print("push", value);
		*it = value;
	} else {
		ctp::print(ctp::stderr, "Stack overflow!");
	}
}

constexpr auto test() {
	stack<int> s{};

	ctp::print(s);

	push(s, 2);
	push(s, 5);
	push(s, 7);

	ctp::print(s);

	push(s, 8);
	return true;
}

constexpr auto i = test();
