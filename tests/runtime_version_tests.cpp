#include <cstdlib>
#include <iostream>

#include "../src/addons/mfgunlock/runtime_version.hpp"

#define CHECK(condition)                                                        \
  do {                                                                          \
    if (!(condition)) {                                                         \
      std::cerr << "CHECK failed at line " << __LINE__ << ": " #condition     \
                << '\n';                                                        \
      return EXIT_FAILURE;                                                      \
    }                                                                           \
  } while (false)

int main() {
  using namespace mfgunlock::runtimeversion;

  constexpr uint64_t dlssg = Pack(310, 9, 1, 0);
  constexpr uint64_t streamline = Pack(2, 14, 1, 0);
  CHECK(Is(dlssg, 310, 9, 1));
  CHECK(!Is(dlssg, 310, 9, 0));
  CHECK(Is(streamline, 2, 14, 1));
  CHECK(!Is(Pack(2, 14, 1, 1), 2, 14, 1));
  CHECK(!Is(0, 2, 14, 1));

  CHECK(SupportsDynamicProvider(dlssg));
  CHECK(SupportsDynamicProvider(Pack(310, 9, 16, 0)));
  CHECK(!SupportsDynamicProvider(Pack(310, 9, 16, 1)));
  CHECK(!SupportsDynamicProvider(Pack(310, 9, 17, 0)));
  CHECK(!SupportsDynamicProvider(Pack(310, 9, 0, 0)));
  CHECK(!SupportsDynamicProvider(0));
  CHECK(SupportsDynamicWrapper(streamline));
  CHECK(SupportsDynamicWrapper(Pack(2, 14, 16, 0)));
  CHECK(!SupportsDynamicWrapper(Pack(2, 14, 16, 1)));
  CHECK(!SupportsDynamicWrapper(Pack(2, 14, 17, 0)));
  CHECK(!SupportsDynamicWrapper(Pack(2, 13, 0, 0)));
  CHECK(!SupportsDynamicWrapper(0));
  CHECK(ImplementsPresetC(Pack(310, 9, 16, 0)));
  CHECK(!ImplementsPresetC(dlssg));
  CHECK(!ImplementsPresetC(0));

  HMODULE kernel32 = GetModuleHandleW(L"kernel32.dll");
  const Version current = FromModule(kernel32);
  CHECK(current.valid);
  CHECK(IsMappedImage(kernel32));
  CHECK(!IsMappedImage(nullptr));

  std::cout << "runtime version tests passed\n";
  return EXIT_SUCCESS;
}
