# Preset C compatibility fork — 1.4.3-c1

Based on Mavis MFGAdaUnlock-RenoDx 1.4.3 (`e09ed477`). This fork adds exact
DLSS-G **310.9.16.0** and Streamline DLSS-G plugin **2.14.16.0** support to the
existing Dynamic MFG policy. It retains 310.9.1 / 2.14.1 compatibility.

The addon is reusable across compatible x64 ReShade games; it contains no
Witcher-specific paths or resolution settings. Native Dynamic MFG still needs
a supported D3D12 Streamline integration and valid feature capability feedback.
This is not a promise of compatibility with every game, renderer, or anti-cheat.

## What changed

- Exact mapped-module version allowlists admit the two reviewed versions.
  Unknown builds, unsupported API capabilities and transient resource states
  retain their existing rejection/fallback behavior.
- The 310.9.16 PE profile permits only independently matched, unchanged kernels.
  Its new 248-byte `BlendCandidatesFused` parameter layout and `FGLite` kernel
  remain native. Old blending patches are not applied to them.
- All six base kernels and thirteen quality variants are recovered **byte for
  byte from the official 1.4.3 addon**. No replacement GPU algorithm was invented
  for this compatibility update. Modified CUDA tables are not committed.
- The overlay/log identifies this as `Paul fork 1.4.3-c1`.

## Install

Close the game. Back up its current MFG addon. Replace that file with this build,
keeping its existing filename if an early-loader configuration refers to it.
Keep only one active MFG unlocker. Existing `RenoDX.MFGUnlock` settings remain
valid; no config reset or fixed rendering resolution is required.

Use NVIDIA-signed DLSS-G 310.9.16 and the matching Streamline 2.14.16 plugins in
the game's actual plugin directory. The latest public SDK interposer is 2.14.1;
the OTA 2.14.16 package does not contain a new interposer. SR/RR/NR are distinct
components. This addon does not install or download the NVIDIA model, change
drivers, or force Preset C over the user's selection.

Choose Preset C through NVIDIA App when supported. A selectable preset or a DLL
load is not proof of active frame generation. Check effective preset feedback,
live generated-frame counts, and actual gameplay. Do not treat an inactive
main-menu counter as failure. This fork does not force FG during invalid inputs,
videos, loading or device transitions.

## Validation

CPU suite: 32 tests passed in the local build. Probes mapped copies of both old
and new NVIDIA DLLs without executing their entry points. They exercised the
actual patch/restore functions: 310.9.16 geometry and temporal matching,
intentional rejection of its changed blend kernel, and 2.14.16 frame-count and
flip-metering patches. Every mapped section was restored byte-exactly.

CUDA compilation/JIT was possible on 616.56, but that is **not** full Preset C
gameplay proof. The user subsequently installed 617.42. In-game performance,
image quality, and universal game compatibility remain unverified.

## Build the release variant

Use the existing CMake project under `tests` with MSVC, the normal RenoDX/ReShade,
Detours, JSON and Streamline dependencies. Obtain the official upstream 1.4.3
addon (SHA-256 `18636063cc4a762c24e2f2c25fef248058509986caae5becee65b5075fbe5e90`).
Run:

```text
python tools/recover_release_tables.py --addon <official-1.4.3.addon64> --output src/addons/mfgunlock --receipt <local-receipt.json>
cmake -S tests -B build -DRENODX_SOURCE_DIR=<dependency-tree>
cmake --build build --config Release --target mfgunlock_preset_c
```

The release target retains the upstream local low-overhead policy, paired
diagonals and V2 inpaint selection. Research targets are not release packages.
Generated NVIDIA-derived tables, provider DLLs and private captures stay out of
Git. Keep the upstream MIT license and attribution.

Rollback: close the game and restore its backed-up MFG addon and runtime DLLs as
one matching set. Do not restore over a newer user edit without comparing hashes.
