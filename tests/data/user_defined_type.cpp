#include <ctp/ctp.hpp>

struct FooBar {
	int i;
};

template<>
struct ctp::formatter<FooBar> {
    static constexpr auto format(const FooBar& a) {
		return std::tuple(".i = {}", a.i);
	}
};

constexpr auto test() {
	FooBar a{1};
	ctp::printf("Print type {}. {}, {}.\n", ctp::type{a}, a, FooBar{2});
	return 0;
}

constexpr auto i = test();
