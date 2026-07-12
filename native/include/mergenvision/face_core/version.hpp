#pragma once

#include <string_view>

namespace mergenvision::face_core {

// Semantic version of the native face-core library.
constexpr std::string_view kSemanticVersion = "0.1.0";

// Monotonically-increasing ABI version integer.
// Bump when the public ABI changes incompatibly.
constexpr int kAbiVersion = 1;

} // namespace mergenvision::face_core
