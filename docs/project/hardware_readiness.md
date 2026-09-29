# Linux hardware readiness audit

Before designing GPU routing, Triton JIT, or eBPF telemetry around the remote workstation, collect its actual driver, CUDA, kernel-header, and BTF capabilities.

Run this read-only audit on the target Linux host:

```bash
bash scripts/audit_hardware.sh
```

The audit reports GPU model/count and available telemetry via `nvidia-smi`, CUDA compiler availability, build headers for the running kernel, and `/sys/kernel/btf/vmlinux`. It does not install packages, request elevated privileges, or change host configuration. Missing tools are reported as warnings so the output can guide the next hardware design decision.

Do not scaffold CUDA-specific execution or eBPF attachment code until this report identifies supported GPU and kernel capabilities. Keep the Mac development path hardware-independent.
