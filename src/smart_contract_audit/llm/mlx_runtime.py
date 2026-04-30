from __future__ import annotations

import platform
import resource
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class MLXRuntimeConfig:
    model_path: str | None = None
    quantization_bits: int = 4
    max_tokens: int = 1024
    temperature: float = 0.1


DEFAULT_MLX_MODEL_ROOTS = (
    Path.home() / "models",
    Path.home() / ".cache" / "huggingface" / "hub",
    Path.home() / "Library" / "Application Support" / "oMLX",
)


@dataclass(frozen=True)
class MLXRuntimeProbe:
    model_path: str | None
    quantization_bits: int
    parameter_count_billion: float
    estimated_weight_memory_gb: float
    mlx_lm_available: bool
    used_fallback: bool
    fallback_reason: str | None
    load_succeeded: bool
    generated_tokens_requested: int
    duration_ms: int
    peak_rss_bytes: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_weight_memory_gb(parameter_count_billion: float, quantization_bits: int) -> float:
    raw_bytes = parameter_count_billion * 1_000_000_000 * quantization_bits / 8
    return round(raw_bytes / 1_000_000_000, 2)


def mlx_available() -> bool:
    try:
        import mlx_lm  # noqa: F401
    except ImportError:
        return False
    return True


def discover_mlx_model_paths(search_roots: list[Path] | None = None) -> list[Path]:
    roots = search_roots or list(DEFAULT_MLX_MODEL_ROOTS)
    candidates: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for config_path in root.rglob("config.json"):
            model_dir = config_path.parent
            if any(model_dir.glob("*.safetensors")):
                candidates.add(model_dir)
    return sorted(candidates, key=_model_sort_key)


def generate_with_mlx(prompt: str, config: MLXRuntimeConfig) -> str | None:
    if not config.model_path or not mlx_available():
        return None

    try:
        from mlx_lm import generate, load
    except ImportError:
        return None

    model, tokenizer = load(config.model_path)
    return generate(
        model,
        tokenizer,
        prompt=prompt,
        **_generation_kwargs(config),
    )


def _generation_kwargs(config: MLXRuntimeConfig) -> dict[str, object]:
    kwargs: dict[str, object] = {"max_tokens": config.max_tokens}
    try:
        from mlx_lm.sample_utils import make_sampler

        kwargs["sampler"] = make_sampler(temp=config.temperature)
    except ImportError:  # pragma: no cover - compatibility with older mlx-lm
        kwargs["temp"] = config.temperature
    return kwargs


def probe_mlx_runtime(
    config: MLXRuntimeConfig,
    parameter_count_billion: float = 8.0,
    prompt: str = "Return JSON: {\"ok\": true}",
) -> MLXRuntimeProbe:
    started = time.perf_counter()
    available = mlx_available()
    fallback_reason: str | None = None
    load_succeeded = False

    if not config.model_path:
        fallback_reason = "model_path_missing"
    elif not available:
        fallback_reason = "mlx_lm_unavailable"
    else:
        try:
            generated = generate_with_mlx(prompt, config)
            load_succeeded = generated is not None
            if generated is None:
                fallback_reason = "generation_returned_none"
        except Exception as exc:  # pragma: no cover - depends on local model/runtime state
            fallback_reason = f"{type(exc).__name__}: {exc}"

    duration_ms = round((time.perf_counter() - started) * 1000)
    return MLXRuntimeProbe(
        model_path=config.model_path,
        quantization_bits=config.quantization_bits,
        parameter_count_billion=parameter_count_billion,
        estimated_weight_memory_gb=estimate_weight_memory_gb(
            parameter_count_billion,
            config.quantization_bits,
        ),
        mlx_lm_available=available,
        used_fallback=not load_succeeded,
        fallback_reason=fallback_reason,
        load_succeeded=load_succeeded,
        generated_tokens_requested=config.max_tokens,
        duration_ms=duration_ms,
        peak_rss_bytes=_peak_rss_bytes(),
    )


def _peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == "Darwin":
        return int(peak)
    return int(peak * 1024)


def _model_sort_key(path: Path) -> tuple[int, int, str]:
    lowered = path.name.lower()
    is_mlx = 0 if "mlx" in lowered else 1
    is_4bit = 0 if "4bit" in lowered or "4-bit" in lowered else 1
    return (is_mlx, is_4bit, str(path))
