from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from export.export_gguf import (
    SUPPORTED_QUANT_TYPES,
    ExportGGUFError,
    export_gguf,
)


def _make_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text('{"model_type": "llama"}')
    return model_dir


def _make_convert_script(tmp_path: Path) -> Path:
    script = tmp_path / "convert_hf_to_gguf.py"
    script.write_text("# llama.cpp convert stub")
    return script


def _ok_result() -> MagicMock:
    r = MagicMock(spec=subprocess.CompletedProcess)
    r.returncode = 0
    r.stdout = ""
    r.stderr = ""
    return r


def test_export_gguf_raises_when_model_dir_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(ExportGGUFError, match="model_dir does not exist"):
        export_gguf(tmp_path / "nonexistent", tmp_path / "output")


def test_export_gguf_raises_on_unsupported_quant_type(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    convert_script = _make_convert_script(tmp_path)
    with pytest.raises(ExportGGUFError, match="Unsupported quantization_type"):
        export_gguf(
            model_dir,
            tmp_path / "output",
            quantization_type="bad_type",
            llama_cpp_path=convert_script,
        )


def test_export_gguf_raises_when_no_convert_script_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_dir = _make_model_dir(tmp_path)
    monkeypatch.delenv("LLAMA_CPP_CONVERT_SCRIPT", raising=False)
    with pytest.raises(ExportGGUFError, match="llama.cpp convert script not found"):
        export_gguf(model_dir, tmp_path / "output")


def test_export_gguf_raises_when_llama_cpp_path_nonexistent(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    with pytest.raises(ExportGGUFError, match="neither convert_hf_to_gguf.py itself"):
        export_gguf(
            model_dir,
            tmp_path / "output",
            llama_cpp_path=tmp_path / "no_such_dir",
        )


def test_export_gguf_raises_when_env_var_script_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_dir = _make_model_dir(tmp_path)
    monkeypatch.setenv("LLAMA_CPP_CONVERT_SCRIPT", str(tmp_path / "missing.py"))
    with pytest.raises(ExportGGUFError, match="LLAMA_CPP_CONVERT_SCRIPT env var points to"):
        export_gguf(model_dir, tmp_path / "output")


def test_export_gguf_raises_when_subprocess_fails(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    convert_script = _make_convert_script(tmp_path)

    failed = MagicMock(spec=subprocess.CompletedProcess)
    failed.returncode = 1
    failed.stdout = ""
    failed.stderr = "fatal: unsupported architecture"

    with (
        patch("export.export_gguf._run_convert_subprocess", return_value=failed),
        pytest.raises(ExportGGUFError, match="GGUF conversion failed"),
    ):
        export_gguf(model_dir, tmp_path / "output", llama_cpp_path=convert_script)


def test_export_gguf_success_default_quant(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    convert_script = _make_convert_script(tmp_path)
    output_dir = tmp_path / "output"

    with patch("export.export_gguf._run_convert_subprocess", return_value=_ok_result()) as mock_run:
        result = export_gguf(model_dir, output_dir, llama_cpp_path=convert_script)

    expected_gguf = output_dir / "model-q4_k_m.gguf"

    assert result == {
        "status": "completed",
        "model_dir": str(model_dir),
        "output_dir": str(output_dir),
        "gguf_path": str(expected_gguf),
        "quantization_type": "q4_k_m",
    }

    cmd = mock_run.call_args[0][0]
    assert str(convert_script) in cmd
    assert str(model_dir) in cmd
    assert "--outtype" in cmd
    assert "q4_k_m" in cmd
    assert "--outfile" in cmd
    assert str(expected_gguf) in cmd


def test_export_gguf_custom_model_name(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    convert_script = _make_convert_script(tmp_path)

    with patch("export.export_gguf._run_convert_subprocess", return_value=_ok_result()):
        result = export_gguf(
            model_dir,
            tmp_path / "output",
            llama_cpp_path=convert_script,
            model_name="my-llama-3-finetuned",
        )

    assert result["gguf_path"].endswith("my-llama-3-finetuned-q4_k_m.gguf")


def test_export_gguf_llama_cpp_path_as_directory(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    llama_dir = tmp_path / "llama_cpp"
    llama_dir.mkdir()
    (llama_dir / "convert_hf_to_gguf.py").write_text("# stub")

    with patch("export.export_gguf._run_convert_subprocess", return_value=_ok_result()) as mock_run:
        result = export_gguf(model_dir, tmp_path / "output", llama_cpp_path=llama_dir)

    cmd = mock_run.call_args[0][0]
    assert str(llama_dir / "convert_hf_to_gguf.py") in cmd
    assert result["status"] == "completed"


def test_export_gguf_script_from_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    model_dir = _make_model_dir(tmp_path)
    convert_script = _make_convert_script(tmp_path)
    monkeypatch.setenv("LLAMA_CPP_CONVERT_SCRIPT", str(convert_script))

    with patch("export.export_gguf._run_convert_subprocess", return_value=_ok_result()):
        result = export_gguf(model_dir, tmp_path / "output")

    assert result["status"] == "completed"


def test_export_gguf_all_quant_types_accepted(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    convert_script = _make_convert_script(tmp_path)

    with patch("export.export_gguf._run_convert_subprocess", return_value=_ok_result()):
        for quant in SUPPORTED_QUANT_TYPES:
            result = export_gguf(
                model_dir,
                tmp_path / "output",
                llama_cpp_path=convert_script,
                quantization_type=quant,
            )
            assert result["quantization_type"] == quant
