#include <ctp/ctp.hpp>

#include <algorithm>

template<size_t N>
constexpr size_t test() {
	ctp::print(N);
	return N;
}

// This will fail on some GCC versions.
// static_assert(test<1>() == 1);
// Workaround is to instantiation test via constexpr variable.
static_assert(ctp::forward<test<1>> == 1);
static_assert(ctp::forward<test<2>()> == 2);
static_assert(ctp::forward<test<3>()> == 3, "Failed");

// template<auto X = ctp::forward<test<4>>>
// template<auto X = test<4>()>
// Workaround is to instantiation test via constexpr variable.
template<auto X = ctp::forward<test<4>>>
constexpr auto get() {
	return X;
}

constexpr auto z = get();
static_assert(z == 4);

// Same as above but with an extra argument.

template<size_t N>
constexpr size_t test_with_args(size_t i) {
	ctp::print(N);
	return N + i;
}

static_assert(ctp::forward<test_with_args<1>, 1> == 2);
static_assert(ctp::forward<test_with_args<2>(1)> == 3);
static_assert(ctp::forward<test_with_args<3>(3)> == 6, "Failed");

template<auto X, auto Y = ctp::forward<test_with_args<4>, X>>
constexpr auto get_with_args() {
	return Y;
}

constexpr auto z_with_args = get_with_args<1>();
static_assert(z_with_args == 5);
