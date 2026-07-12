#include <mergenvision/face_core/version.hpp>

#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>

int main() {
    const std::string version(mergenvision::face_core::kSemanticVersion);
    if (version.empty()) {
        std::cerr << "FAIL: semantic version is empty\n";
        return EXIT_FAILURE;
    }

    if (mergenvision::face_core::kAbiVersion != 1) {
        std::cerr << "FAIL: unexpected ABI version "
                  << mergenvision::face_core::kAbiVersion << "\n";
        return EXIT_FAILURE;
    }

    std::cout << "mergenvision_face_core " << version
              << " (ABI " << mergenvision::face_core::kAbiVersion << ") smoke OK\n";
    return EXIT_SUCCESS;
}
