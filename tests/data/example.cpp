#include <ctp/ctp.hpp>

struct FooBar {
	int i;
	float j;
};

template<>
struct ctp::formatter<FooBar> {
	static constexpr auto format(const FooBar& obj) {
		return std::tuple{"(.i = {}, .j = {})", obj.i, obj.j};
	}
};

constexpr auto test() {
	ctp::print("Integral:");
	ctp::print(true, 1, -2, std::numeric_limits<uint64_t>::max());

	ctp::print("\nFloating point:");
	ctp::print(1.22F, std::numeric_limits<float>::infinity());
	ctp::printf("{:.2f}\n", 1.22F);

	ctp::print("\nArray:");
	std::array<int, 5> arr{1, 5, 3, 2, 4};
	ctp::print(arr);
	ctp::printf("Third element is: {[2]}\n", arr);

	ctp::print("\nView:");
	ctp::print(ctp::view(arr.data() + 1, 3));

	ctp::print("\nTuple:");
	std::tuple<int, double> tuple{1, 2.5};
	ctp::print(tuple);
	ctp::printf("Second element is: {[1]}\n", tuple);

	ctp::print("\nPair:");
	std::pair<int, double> pair{-3.5, 2};
	ctp::print(pair);

	ctp::print("\nTypes:");
	ctp::printf("Pair '{}' is not an alias of tuple '{}'.\n", ctp::type<decltype(pair)>{}, ctp::type{tuple});
	ctp::printf("But both have the same size: {} - {}\n", sizeof(pair), sizeof(tuple));

	ctp::print("\nUser-defined type:");
	FooBar foobar{3, -1.25F};
	ctp::print(ctp::type<FooBar>{}, foobar);

	ctp::printf(ctp::stderr, u"\n\tFatal ");
	ctp::print(ctp::stderr, U"success! :)");

	[[maybe_unused]] constexpr auto i = ctp::print("Print examples:\n");

	return true;
}

constexpr auto t = test();
