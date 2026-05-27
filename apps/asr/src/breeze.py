"""Breeze-ASR-25 model wrapper.

Wave 1 design:
  - Model is loaded lazily on first request (avoids slow startup in dev)
  - ``stub_mode=True`` short-circuits to a fake transcript so the rest of the
    stack can be tested without a GPU.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    language: str = "zh"
    duration_s: float = 0.0
    model_id: str = ""
    stub: bool = False


class BreezeAsr:
    """Lazy-loaded Breeze-ASR-25 pipeline."""

    def __init__(self) -> None:
        self._pipeline: Any = None
        self._device: str = ""

    def _resolve_device(self) -> str:
        cfg = get_settings().asr_device
        if cfg != "auto":
            return cfg
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _load(self) -> None:
        if self._pipeline is not None:
            return

        settings = get_settings()
        self._device = self._resolve_device()
        logger.info(
            "Loading Breeze-ASR-25 (%s) on %s",
            settings.breeze_model_id,
            self._device,
        )

        # Defer heavy imports until first use.
        import torch
        from transformers import (
            AutomaticSpeechRecognitionPipeline,
            WhisperForConditionalGeneration,
            WhisperProcessor,
        )

        processor = WhisperProcessor.from_pretrained(
            settings.breeze_model_id,
            cache_dir=settings.asr_cache_dir,
        )
        model = WhisperForConditionalGeneration.from_pretrained(
            settings.breeze_model_id,
            cache_dir=settings.asr_cache_dir,
            torch_dtype=torch.bfloat16 if self._device == "cuda" else torch.float32,
        )
        if self._device == "cuda":
            model = model.to("cuda")
        model.eval()

        self._pipeline = AutomaticSpeechRecognitionPipeline(
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            chunk_length_s=0,  # full-utterance mode per HF model card
        )

    def transcribe(self, audio_bytes: bytes) -> TranscriptionResult:
        settings = get_settings()
        if settings.asr_stub_mode:
            return TranscriptionResult(
                text="[stub] ASR not actually invoked",
                model_id=settings.breeze_model_id,
                stub=True,
            )

        self._load()
        waveform, sample_rate = _decode_to_mono_16k(audio_bytes)
        output = self._pipeline(waveform, return_timestamps=True)  # type: ignore[misc]
        text = output["text"].strip() if isinstance(output, dict) else str(output).strip()
        duration = len(waveform) / sample_rate
        return TranscriptionResult(
            text=text,
            duration_s=duration,
            model_id=settings.breeze_model_id,
        )


def _decode_to_mono_16k(audio_bytes: bytes) -> tuple[np.ndarray, int]:
    """Decode raw audio (wav/flac/mp3 via soundfile/torchaudio) → mono 16kHz float32."""
    import soundfile as sf
    import torchaudio

    waveform_np, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=True)
    # (n_frames, channels) → mono
    waveform_np = waveform_np.mean(axis=1)

    if sample_rate != 16_000:
        import torch
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16_000)
        waveform_np = resampler(torch.from_numpy(waveform_np)).numpy()
        sample_rate = 16_000

    return waveform_np, sample_rate


_asr = BreezeAsr()


def get_asr() -> BreezeAsr:
    return _asr
