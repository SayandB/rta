#!/usr/bin/env bash

set -u

if [[ "$(uname -s)" != "Linux" ]]; then
  printf 'ERROR: This audit must run on the target Linux workstation.\n' >&2
  exit 2
fi

kernel_release="$(uname -r)"
printf 'Kernel: %s\n' "$kernel_release"

if command -v nvidia-smi >/dev/null 2>&1; then
  printf '\nGPU inventory:\n'
  nvidia-smi --list-gpus
  printf '\nGPU telemetry:\n'
  nvidia-smi --query-gpu=name,driver_version,utilization.gpu,memory.used,memory.total,power.draw --format=csv
else
  printf 'WARN: nvidia-smi is not installed or not on PATH.\n'
fi

if command -v nvcc >/dev/null 2>&1; then
  printf '\nCUDA compiler:\n'
  nvcc --version
else
  printf 'WARN: nvcc is not installed or not on PATH.\n'
fi

headers_path="/lib/modules/${kernel_release}/build"
if [[ -e "$headers_path" ]]; then
  printf '\nKernel headers: %s\n' "$headers_path"
else
  printf 'WARN: Kernel build headers not found at %s.\n' "$headers_path"
fi

if [[ -r /sys/kernel/btf/vmlinux ]]; then
  printf 'Kernel BTF: available at /sys/kernel/btf/vmlinux\n'
else
  printf 'WARN: Kernel BTF is unavailable; eBPF CO-RE support may be limited.\n'
fi
