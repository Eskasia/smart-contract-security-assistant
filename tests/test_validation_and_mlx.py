from pathlib import Path

from smart_contract_audit.llm.mlx_runtime import (
    MLXRuntimeConfig,
    _generation_kwargs,
    discover_mlx_model_paths,
    estimate_weight_memory_gb,
    probe_mlx_runtime,
)
from smart_contract_audit.validation.validator import validate_report


def test_mlx_weight_memory_estimate() -> None:
    assert estimate_weight_memory_gb(8, 4) == 4.0


def test_mlx_probe_records_fallback_without_model_path() -> None:
    probe = probe_mlx_runtime(MLXRuntimeConfig(model_path=None, max_tokens=8))

    assert probe.model_path is None
    assert probe.estimated_weight_memory_gb == 4.0
    assert probe.used_fallback is True
    assert probe.fallback_reason == "model_path_missing"
    assert probe.load_succeeded is False
    assert probe.peak_rss_bytes > 0


def test_mlx_model_discovery_prefers_mlx_4bit(tmp_path: Path) -> None:
    eight_bit = tmp_path / "Qwen-MLX-8bit"
    four_bit = tmp_path / "Qwen-MLX-4bit"
    generic = tmp_path / "GenericModel"
    for model_dir in (eight_bit, four_bit, generic):
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        (model_dir / "model.safetensors").write_text("", encoding="utf-8")

    discovered = discover_mlx_model_paths([tmp_path])

    assert discovered[0] == four_bit
    assert discovered == [four_bit, eight_bit, generic]


def test_mlx_generation_kwargs_are_compatible_with_current_runtime() -> None:
    kwargs = _generation_kwargs(MLXRuntimeConfig(max_tokens=7, temperature=0.2))

    assert kwargs["max_tokens"] == 7
    assert "sampler" in kwargs or kwargs["temp"] == 0.2


def test_schema_validation_rejects_missing_fields() -> None:
    result = validate_report({"overall_status": "finding"})
    assert not result.valid
    assert result.errors
