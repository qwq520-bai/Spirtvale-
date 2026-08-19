"""Slim Windows hook for the CPU-portable AutoMech build.

The development environment contains a CUDA PyTorch wheel.  The packaged
program uses CPU when CUDA is unavailable, so CUDA runtime DLLs are omitted.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


datas = collect_data_files(
    "torch",
    excludes=[
        "**/*.h",
        "**/*.hpp",
        "**/*.cuh",
        "**/*.lib",
        "**/*.dll",
        "**/*.cpp",
        "**/*.pyi",
        "**/*.cmake",
    ],
)
# Torch 的部分配置模块会在运行时通过 inspect 读取源码。
module_collection_mode = "pyz+py"
hiddenimports = collect_submodules("torch")

_CUDA_MARKERS = (
    "cuda",
    "cublas",
    "cudnn",
    "cufft",
    "cusolver",
    "cusparse",
    "curand",
    "nvrtc",
    "nvjitlink",
    "nvperf",
    "cupti",
    "cudart",
    "caffe2_nvrtc",
)


def _is_cuda_binary(source):
    name = Path(source).name.lower()
    return any(marker in name for marker in _CUDA_MARKERS)


binaries = [
    (source, destination)
    for source, destination in collect_dynamic_libs("torch")
    if not _is_cuda_binary(source)
]
