/*
 *  Compile-Time Printer
 *  ----------------------------------------------------------
 *  Copyright 2021 Toni Neubert. All rights reserved.
 *
 *  Distributed under the Boost Software License, Version 1.0.
 *  (See accompanying file LICENSE.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
 */
#ifndef COMPILE_TIME_PRINTER_HPP_INCLUDE
#define COMPILE_TIME_PRINTER_HPP_INCLUDE

// If defined, don't print anything.
// #define CTP_QUIET
// If defined, don't even print version indicator.
// #define CTP_DEAD_QUIET

#if defined(CTP_DEAD_QUIET) && !defined(CTP_QUIET)
    #define CTP_QUIET
#endif

#if defined(__clang__) || !defined(__GNUC__) || defined(__INTEL_COMPILER) || __cplusplus < 201703L
    #if !defined(CTP_QUIET)
        #define CTP_QUIET
        #error "Only GCC >= 7, STD >= C++17 is supported."
    #endif
#endif

#include <array>
#include <string_view>
#include <tuple>

#include <cmath>
#include <cstddef>
#include <cstdint>

namespace ctp {

/**
 * Represents a file descriptor.
 */
struct file_descriptor {
	size_t value;
	constexpr bool operator==(const file_descriptor& other) const;
};

/// Standard output stream (stdout).
inline constexpr file_descriptor stdout{1};

/// Standard error output stream (stderr).
inline constexpr file_descriptor stderr{2};

/**
 * Prints all arguments in a simple, standardized format.
 * Each argument is separated by one space, ending with a line break.
 * @param args - the arguments to print.
 */
template<typename... Args>
constexpr auto print(Args&&... args);

/**
 * Prints all arguments in a simple, standardized format to a specific file  descriptor.
 * Each argument is separated by one space, ending with a line break.
 * @param fd - the file descriptor
 * @param args - the arguments to print
 */
template<typename FileDescriptor,
         typename... Args,
         std::enable_if_t<std::is_same_v<std::decay_t<FileDescriptor>, file_descriptor>>* = nullptr>
constexpr auto print(FileDescriptor&& fd, Args&&... args);

/**
 * Formats and prints all arguments in the desired format.
 * @param args - the arguments to format and print
 */
template<typename... Args>
constexpr auto printf(std::string_view format = "", Args&&... args);

/**
 * Formats and prints all arguments in the desired format to a specific file descriptor.
 * @param fd - the file descriptor
 * @param args - the arguments to format and print
 */
template<typename FileDescriptor,
         typename... Args,
         std::enable_if_t<std::is_same_v<std::decay_t<FileDescriptor>, file_descriptor>>* = nullptr>
constexpr auto printf(FileDescriptor&& fd, std::string_view format = "", Args&&... args);

/**
 * For user-defined types, the format function of the specialized formatter<T> struct template is used.
 * Provide a function `constexpr auto format(T);` returning a tuple like object. The first element must be a format
 * string followed by the arguments.
 * @tparam T - the user-defined type
 */
template<typename T>
struct formatter;

/**
 * Helper to print a contiguous range.
 * @tparam T - the value type of the range
 */
template<typename T>
class view;

/**
 * Helper to print the types of arguments rather than the values.
 * @tparam Ts - the types to print
 */
template<typename... Ts>
struct type;

/**
 * Helper to generate extra noise to force the compiler not to cache the evaluation of a print statement.
 * Should be taken by reference.
 */
struct noise {};

namespace detail {

/// Forward a value.
template<typename T, std::enable_if_t<!std::is_invocable_v<T>>* = nullptr>
constexpr T forward(T&& value) {
	return value;
}

/// Forward the return value of a function.
template<typename T, typename... Ts, std::enable_if_t<std::is_invocable_v<T, Ts...>>* = nullptr>
constexpr auto forward(T&& func, Ts&&... args) {
	return func(std::forward<Ts>(args)...);
}

}    // namespace detail

/**
 * Helper to use print/printf in static_assert and template parameters.
 * The expression/function will be instantiated as constexpr variable, to overcome compile errors.
 * @tparam ExprFunc - the expression or function which should be instantiated
 * @tparam Args - the arguments for the function
 */
template<auto ExprFunc, auto... Args>
inline constexpr auto forward = detail::forward(std::forward<decltype(ExprFunc)>(ExprFunc),
                                                std::forward<decltype(Args)>(Args)...);

namespace detail {

inline constexpr auto protocol_version = 1;

enum class Indicator : uint32_t {
	Version = 32,
	StartOut = 33,
	StartErr = 34,
	StartOutFormat = 35,
	StartErrFormat = 36,
	End = 37,
	NaNFloat = 128,
	PositiveInfinityFloat = 129,
	NegativeInfinityFloat = 130,
	NegativeFloat = 131,
	PositiveFloat = 132,
	FractionFloat = 133,
	PositiveInteger = 134,
	NegativeInteger = 135,
	Type = 136,
	ArrayBegin = 138,
	ArrayEnd = 139,
	StringBegin = 140,
	StringEnd = 141,
	TupleBegin = 142,
	TupleEnd = 143,
	CustomFormatBegin = 144,
	CustomFormatEnd = 145,
};

template<typename T, std::enable_if_t<std::is_arithmetic_v<T>>* = nullptr>
constexpr __uint128_t to_abs_int(T value) {
	if constexpr (std::is_signed_v<T>) {
		return static_cast<__uint128_t>(std::abs(value));
	} else {
		return static_cast<__uint128_t>(value);
	}
}

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wshift-count-overflow"

#ifdef CTP_QUIET
#define CTP_INTERNAL_PRINT(x, y)              \
	{                                         \
		[[maybe_unused]] auto unused_x = (x); \
		[[maybe_unused]] auto unused_y = (y); \
	}
#else
#define CTP_INTERNAL_PRINT(x, y) \
	{ [[maybe_unused]] auto unused = (x) << static_cast<uint32_t>(y); }
#endif

/// Print integer values.
template<typename T, typename... Args, std::enable_if_t<std::is_integral_v<T>>* = nullptr>
constexpr void print_value(int& /*unused*/, T value, Args&&... /*unused*/) {
	if constexpr (std::is_signed_v<T>) {
		if (value < 0) {
			CTP_INTERNAL_PRINT(to_abs_int(value), Indicator::NegativeInteger);
		} else {
			CTP_INTERNAL_PRINT(to_abs_int(value), Indicator::PositiveInteger);
		}
	} else {
		CTP_INTERNAL_PRINT(to_abs_int(value), Indicator::PositiveInteger);
	}
}

/// Print floating point values.
template<typename T, typename... Args, std::enable_if_t<std::is_floating_point_v<T>>* = nullptr>
constexpr void print_value(int& one, T value, Args&&... /*unused*/) {
	if (value != value) {
		CTP_INTERNAL_PRINT(one, Indicator::NaNFloat);
		return;
	}
	if (value < 0) {
		if (std::abs(value) == std::numeric_limits<long double>::infinity()) {
			CTP_INTERNAL_PRINT(one, Indicator::NegativeInfinityFloat);
			return;
		}
		CTP_INTERNAL_PRINT(to_abs_int(value), Indicator::NegativeFloat);
	} else if (value >= 0) {
		if (value == std::numeric_limits<long double>::infinity()) {
			CTP_INTERNAL_PRINT(one, Indicator::PositiveInfinityFloat);
			return;
		}
		CTP_INTERNAL_PRINT(to_abs_int(value), Indicator::PositiveFloat);
	}
	long double decimal = value;
	auto fraction = std::abs(decimal) - std::floor(std::abs(decimal));
	fraction *= std::pow(10.0L, std::numeric_limits<long double>::digits10);
	CTP_INTERNAL_PRINT(to_abs_int(fraction), Indicator::FractionFloat);
}

/// Print contiguous sequences of not char-like objects.
template<
  typename T,
  typename... Args,
  std::enable_if_t<!std::is_convertible_v<T, std::string_view> && sizeof(decltype(view(std::declval<T>())))>* = nullptr>
constexpr void print_value(int& one, T&& value, Args&&... args) {
	CTP_INTERNAL_PRINT(one, Indicator::ArrayBegin);
	for (auto v : view(value)) {
		print_value(one, v, std::forward<Args>(args)..., v, value);
	}
	CTP_INTERNAL_PRINT(one, Indicator::ArrayEnd);
}

/// Print contiguous sequence of char-like objects.
template<typename T, typename... Args, std::enable_if_t<std::is_convertible_v<T, std::string_view>>* = nullptr>
constexpr void print_value(int& one, T value, Args&&... args) {
	CTP_INTERNAL_PRINT(one, Indicator::StringBegin);
	for (auto v : std::string_view{value}) {
		print_value(one, v, std::forward<Args>(args)..., v, value);
	}
	CTP_INTERNAL_PRINT(one, Indicator::StringEnd);
}

/// Print tuple like.
template<size_t... Is, typename T, typename... Args>
constexpr void print_value(int& one, std::index_sequence<Is...> /*unused*/, T&& tuple, Args&&... args) {
	CTP_INTERNAL_PRINT(one, Indicator::TupleBegin);
	(print_value(one, std::get<Is>(std::forward<T>(tuple)), std::forward<Args>(args)..., Is, Is...), ...);
	CTP_INTERNAL_PRINT(one, Indicator::TupleEnd);
}

template<typename T>
struct is_not_std_array : std::true_type {};

template<typename T, size_t N>
struct is_not_std_array<std::array<T, N>> : std::false_type {};

template<typename T>
struct is_complete {
private:
	template<typename U>
	static int is_complete_helper(int (*)[sizeof(U)]);
	template<typename>
	static char is_complete_helper(...);

public:
	static constexpr bool value = sizeof(is_complete_helper<T>(0)) != 1;
};

template<typename T>
struct is_tuple_like :
  std::integral_constant<bool, is_complete<std::tuple_size<T>>::value && is_not_std_array<T>::value> {};

// Unpack tuple like.
template<typename T, typename... Args, std::enable_if_t<is_tuple_like<std::decay_t<T>>::value>* = nullptr>
constexpr void print_value(int& one, T&& tuple, Args&&... args) {
	print_value(one,
	            std::make_index_sequence<std::tuple_size_v<std::decay_t<T>>>{},
	            std::forward<T>(tuple),
	            std::forward<Args>(args)...);
}

/// Print type.
template<typename... Ts, typename... Args>
constexpr void print_value(int& one, type<Ts...>, Args&&... /*unused*/) {
	CTP_INTERNAL_PRINT(one, Indicator::Type);
}

/// Generate noise.
template<typename... Args>
constexpr void print_value(int&, const noise&, Args&&... /*unused*/) {}

/// Print with user-defined formatter.
template<typename T,
         typename... Args,
         std::enable_if_t<sizeof(std::string_view{std::get<0>(std::declval<ctp::formatter<std::decay_t<T>>>().format(
                            std::declval<T>()))}) == 16>* = nullptr>
constexpr void print_value(int& one, T&& value, Args&&... args) {
	CTP_INTERNAL_PRINT(one, Indicator::CustomFormatBegin);
	print_value(one, formatter<std::decay_t<T>>{}.format(value), std::forward<Args>(args)...);
	CTP_INTERNAL_PRINT(one, Indicator::CustomFormatEnd);
}

/// Print start indicator output stream and if first argument is the format string.
template<bool Format, typename Arg, typename... Args>
constexpr void print_start_indicator(int& one, Arg&& arg, Args&&...) {
	if constexpr (std::is_same_v<std::decay_t<Arg>, file_descriptor>) {
		if (arg == stderr) {
			if (Format) {
				CTP_INTERNAL_PRINT(one, Indicator::StartErrFormat);
			} else {
				CTP_INTERNAL_PRINT(one, Indicator::StartErr);
			}
			return;
		}
	}
	if (Format) {
		CTP_INTERNAL_PRINT(one, Indicator::StartOutFormat);
	} else {
		CTP_INTERNAL_PRINT(one, Indicator::StartOut);
	}
}

/// Print end indicator.
template<typename... Args>
constexpr auto print_end_indicator(int one, Args&&... /*unused*/) {
	CTP_INTERNAL_PRINT(one, Indicator::End);
	return one;
}

/// Trigger unused variable instead of fpermissive warning to be compatible to other compiler in the future.
#pragma GCC diagnostic push
#pragma GCC diagnostic warning "-Wunused-variable"
template<int Version>
constexpr auto print_protocol_version() {
#ifndef CTP_DEAD_QUIET
	int version = Version;
#endif
	return Version;
}
#pragma GCC diagnostic pop

inline constexpr auto indicate_protocol_version = print_protocol_version<protocol_version>();

#pragma GCC diagnostic pop

inline constexpr struct separator_t {
} separator;

/// Unpack and print each argument.
template<size_t... Is, typename... Args>
constexpr void print_helper(int& one, std::index_sequence<Is...> /*unused*/, Args&&... args) {
	// First parameter (unpacked by ...) is the value to print.
	// The separator is used to better parse the type of the first parameter from the variadic template list. All other
	// parameters and the index sequence are unused but otherwise same arguments are mentioned only once.
	(print_value(one, std::forward<Args>(args), separator, std::forward<Args>(args)..., Is, Is...), ...);
}

template<bool Format,
         typename Arg = ctp::noise,
         typename... Args,
         std::enable_if_t<!std::is_same_v<std::decay_t<Arg>, file_descriptor> ||
                          (std::is_same_v<std::decay_t<Arg>, file_descriptor> && sizeof...(Args) > 0)>* = nullptr>
constexpr auto print(Arg&& arg = {}, Args&&... args) {
	int one = 1;
	print_start_indicator<Format>(one, std::forward<Arg>(arg), std::forward<Args>(args)...);

	/// Skip first argument if file descriptor.
	if constexpr (std::is_same_v<std::decay_t<Arg>, file_descriptor>) {
		print_helper(one, std::make_index_sequence<sizeof...(Args)>{}, std::forward<Args>(args)...);
	} else {
		print_helper(
		  one, std::make_index_sequence<sizeof...(Args) + 1>{}, std::forward<Arg>(arg), std::forward<Args>(args)...);
	}

	return print_end_indicator(one, std::forward<Arg>(arg), std::forward<Args>(args)...);
}

}    // namespace detail

constexpr bool file_descriptor::operator==(const file_descriptor& other) const {
	return value == other.value;
}

template<typename... Args>
constexpr auto print(Args&&... args) {
	return detail::print<false>(std::forward<Args>(args)...);
}

template<typename FileDescriptor,
         typename... Args,
         std::enable_if_t<std::is_same_v<std::decay_t<FileDescriptor>, file_descriptor>>*>
constexpr auto print(FileDescriptor&& stream, Args&&... args) {
	return detail::print<false>(std::forward<FileDescriptor>(stream), std::forward<Args>(args)...);
}

template<typename FileDescriptor,
         typename... Args,
         std::enable_if_t<std::is_same_v<std::decay_t<FileDescriptor>, file_descriptor>>*>
constexpr auto printf(FileDescriptor&& stream, std::string_view format, Args&&... args) {
	return detail::print<true>(std::forward<FileDescriptor>(stream), format, std::forward<Args>(args)...);
}

template<typename... Args>
constexpr auto printf(std::string_view format, Args&&... args) {
	return detail::print<true>(stdout, format, std::forward<Args>(args)...);
}

template<typename T>
class view {
public:
	template<typename, typename = void>
	struct has_size_and_data : std::false_type {};

	template<typename U>
	struct has_size_and_data<
	  U,
	  std::void_t<decltype(std::size(std::declval<U>())), decltype(std::data(std::declval<U>()))>> : std::true_type {};

	constexpr view() = default;

	template<size_t N>
	explicit constexpr view(const std::array<T, N>& arr) : data_{arr.data()}, size_{arr.size()} {}

	template<size_t N>
	explicit constexpr view(const T (&arr)[N]) : data_{arr}, size_{N} {}

	template<typename U, std::enable_if_t<has_size_and_data<U>::value>* = nullptr>
	explicit constexpr view(const U& arr) : data_(arr.data()), size_{arr.size()} {}

	template<typename U, std::enable_if_t<std::is_integral_v<U>>* = nullptr>
	constexpr view(const T* first, U&& size) : data_{first}, size_{static_cast<size_t>(size)} {}

	constexpr view(const T* first, const T* last) : data_{first}, size_{static_cast<size_t>(last - first)} {}

	constexpr auto begin() const {
		return data_;
	}

	constexpr auto end() const {
		return data_ + size_;
	}

private:
	const T* data_{};
	size_t size_{};
};

template<typename T, size_t N>
view(std::array<T, N>) -> view<T>;

template<typename T, size_t N>
view(T (&)[N]) -> view<T>;

template<typename T>
view(T) -> view<std::remove_pointer_t<decltype(std::data(std::declval<T>()))>>;

template<typename T>
view(T*, T*) -> view<T>;

template<typename T, typename U>
view(T*, U) -> view<T>;

template<typename... Ts>
struct type {
	constexpr type() = default;

	constexpr type(Ts&&... /*unused*/) {}
};

template<typename... Ts>
type(Ts&&...) -> type<Ts...>;

}    // namespace ctp

#endif    // COMPILE_TIME_PRINTER_HPP_INCLUDE
