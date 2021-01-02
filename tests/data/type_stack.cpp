#include <ctp/ctp.hpp>

template<typename...>
struct stack {};

template<typename... Ts, typename T>
constexpr auto push(stack<Ts...>, T) {
	[[maybe_unused]] constexpr auto x = ctp::print("push", ctp::type<T>{});

	return stack<T, Ts...>{};
}

constexpr auto test() {
	using s = stack<>;

	[[maybe_unused]] constexpr auto i = ctp::print(ctp::type<s>{});

	using s1 = decltype(push(s{}, 1));
	using s2 = decltype(push(s1{}, 2.0));
	using s3 = decltype(push(s2{}, 's'));

	ctp::print(ctp::type<s3>{});

	return true;
}

constexpr auto i = test();
