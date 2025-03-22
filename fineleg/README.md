#### Note to self
To get rerun working on WSL2 (unfortunately CPU only so far), run:
```bash
export WGPU_BACKEND=Vulkan
```

[Rerun troubleshooting site](https://rerun.io/docs/getting-started/troubleshooting#wsl2) recommends these, but not convinced they help:
```bash
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
unset WAYLAND_DISPLAY
```
