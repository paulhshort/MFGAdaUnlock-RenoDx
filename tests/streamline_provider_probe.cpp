// SPDX-License-Identifier: MIT
// Map an offline plugin copy without executing it, exercise the actual addon
// patch/restore implementation, and verify complete mapped sections restored.
#include "../src/addons/mfgunlock/addon.cpp"
#include <iostream>
extern "C" __declspec(dllexport) void ReShadeLogMessage(void*,int,const char* message) {
  std::cout << message << '\n';
}
int wmain(int argc,wchar_t** argv) {
  reshade::internal::get_reshade_module_handle(GetModuleHandleW(nullptr));
  if(argc!=2)return 2;
  HMODULE module=LoadLibraryExW(argv[1],nullptr,DONT_RESOLVE_DLL_REFERENCES);
  if(!module)return 3;
  unsigned char* base=nullptr;const IMAGE_NT_HEADERS64* nt=nullptr;
  if(!ModuleImage(module,&base,&nt))return 4;
  std::vector<std::pair<unsigned char*,std::vector<unsigned char>>> originals;
  const auto* section=IMAGE_FIRST_SECTION(nt);
  for(WORD i=0;i<nt->FileHeader.NumberOfSections;++i,++section){
    if(!(section->Characteristics&IMAGE_SCN_MEM_READ))continue;
    auto* start=base+section->VirtualAddress;
    originals.emplace_back(start,std::vector<unsigned char>(start,start+section->Misc.VirtualSize));
  }
  const auto version=mfgunlock::runtimeversion::FromModule(module);
  if(!version.valid)return 5;
  PatchFrameCountCeiling(module);
  const bool patched=CeilingPatchStillOwned();
  std::cout<<"ceiling_patched="<<patched<<" compiled="<<g_ceiling_compiled<<" effective="<<g_ceiling_effective<<"\n";
  const bool flip=TryPatchFlipMeteringInModule(module);
  std::cout<<"flip_metering_patched="<<flip<<"\n";
  RestoreFlipMetering();RestoreFrameCountCeiling();
  bool restored=true;
  for(const auto& [address,bytes]:originals)restored &= std::memcmp(address,bytes.data(),bytes.size())==0;
  std::cout<<"all_mapped_sections_restored="<<restored<<"\n";
  FreeLibrary(module);
  return patched&&restored?0:1;
}
