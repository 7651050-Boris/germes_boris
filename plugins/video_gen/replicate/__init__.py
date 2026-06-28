"""Replicate video generation backend.

Supports MiniMax Video-01 Live (default), Google Veo 2, HunyuanVideo and
Wan 2.1 via the Replicate Python client.

Model routing:
  - text-to-video: called without image_url
  - image-to-video: called with image_url (not all models support it)

Authentication: REPLICATE_API_TOKEN env var or ~/.hermes/.env.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from agent.video_gen_provider import (
    VideoGenProvider,
    error_response,
    success_response,
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------
#
# Each family declares:
#   text_model      : Replicate model ID for text-to-video
#   image_model     : Replicate model ID for image-to-video (None = not supported)
#   image_param_key : input key for the image URL (default: "first_frame_image")
#   aspect_ratios   : supported ratios or None (endpoint decides)
#   durations       : (min, max) range or None
#   audio           : True if audio generation is supported

REPLICATE_FAMILIES: Dict[str, Dict[str, Any]] = {
    "minimax-video-01-live": {
        "display": "MiniMax Video-01 Live",
        "speed": "~60-120s",
        "price": "premium",
        "strengths": "Cinematic quality, consistent motion, supports image-to-video.",
        "text_model": "minimax/video-01-live",
        "image_model": "minimax/video-01-live",
        "image_param_key": "first_frame_image",
        "aspect_ratios": ("16:9", "9:16", "1:1"),
        "durations": (6, 6),
        "audio": False,
        "extra_input": {"prompt_optimizer": True},
    },
    "veo-2": {
        "display": "Google Veo 2",
        "speed": "~90-180s",
        "price": "premium",
        "strengths": "Google DeepMind flagship. Cinematic, realistic physics, strong prompt adherence.",
        "text_model": "google-deepmind/veo-2",
        "image_model": None,
        "aspect_ratios": ("16:9", "9:16"),
        "durations": (5, 8),
        "audio": False,
        "extra_input": {"duration": 8},
    },
    "hunyuan-video": {
        "display": "HunyuanVideo",
        "speed": "~120-240s",
        "price": "premium",
        "strengths": "Tencent open-source. High motion quality, 5s clips.",
        "text_model": "tencent/hunyuan-video",
        "image_model": None,
        "aspect_ratios": ("16:9", "9:16", "1:1"),
        "durations": (5, 5),
        "audio": False,
        "extra_input": {"num_inference_steps": 50, "fps": 24},
    },
    "wan-2.1": {
        "display": "Wan 2.1 720p",
        "speed": "~60-120s",
        "price": "cheap",
        "strengths": "Alibaba open-source. Great text-to-video at 720p.",
        "text_model": "wan-ai/wan2.1-t2v-720p",
        "image_model": "wan-ai/wan2.1-i2v-480p",
        "image_param_key": "image",
        "aspect_ratios": ("16:9", "9:16", "1:1"),
        "durations": (5, 5),
        "audio": False,
        "extra_input": {},
    },
}

DEFAULT_MODEL = "minimax-video-01-live"


def _get_api_token() -> Optional[str]:
    token = os.getenv("REPLICATE_API_TOKEN")
    if token and token.strip():
        return token.strip()
    try:
        from hermes_cli.config import get_env_value
        token = get_env_value("REPLICATE_API_TOKEN")
        if token and token.strip():
            return token.strip()
    except Exception:
        pass
    return None


def _resolve_family(model_override: Optional[str]) -> tuple[str, Dict[str, Any]]:
    candidates = [model_override]
    candidates.append(os.getenv("REPLICATE_VIDEO_MODEL", "").strip() or None)

    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        vid_cfg = cfg.get("video_gen") or {}
        rep_cfg = vid_cfg.get("replicate") if isinstance(vid_cfg, dict) else {}
        if isinstance(rep_cfg, dict):
            candidates.append(rep_cfg.get("model", "").strip() or None)
        top = vid_cfg.get("model") if isinstance(vid_cfg, dict) else None
        candidates.append(top)
    except Exception:
        pass

    for c in candidates:
        if isinstance(c, str) and c.strip() and c.strip() in REPLICATE_FAMILIES:
            fid = c.strip()
            return fid, REPLICATE_FAMILIES[fid]

    return DEFAULT_MODEL, REPLICATE_FAMILIES[DEFAULT_MODEL]


class ReplicateVideoGenProvider(VideoGenProvider):
    """Replicate video generation backend."""

    @property
    def name(self) -> str:
        return "replicate"

    @property
    def display_name(self) -> str:
        return "Replicate"

    def is_available(self) -> bool:
        return bool(_get_api_token())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": fid,
                "display": meta["display"],
                "speed": meta.get("speed", ""),
                "strengths": meta.get("strengths", ""),
                "price": meta.get("price", ""),
            }
            for fid, meta in REPLICATE_FAMILIES.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Replicate",
            "badge": "paid",
            "tag": "MiniMax Video-01 Live, Veo 2, HunyuanVideo, Wan 2.1.",
            "env_vars": [
                {
                    "key": "REPLICATE_API_TOKEN",
                    "prompt": "Replicate API token",
                    "url": "https://replicate.com/account/api-tokens",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        resolution: str = DEFAULT_RESOLUTION,
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        token = _get_api_token()
        if not token:
            return error_response(
                error="REPLICATE_API_TOKEN is not set. Add it to ~/.hermes/.env or your environment.",
                error_type="missing_credentials",
                provider="replicate",
                prompt=prompt,
            )

        try:
            import replicate as _replicate
        except ImportError:
            try:
                import subprocess, sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "replicate"], capture_output=True)
                import replicate as _replicate
            except Exception as exc:
                return error_response(
                    error=f"replicate package not installed and auto-install failed: {exc}",
                    error_type="missing_dependency",
                    provider="replicate",
                    prompt=prompt,
                )

        family_id, family = _resolve_family(model)
        use_image = bool(image_url and family.get("image_model"))
        modality = "image" if use_image else "text"
        replicate_model = family["image_model"] if use_image else family["text_model"]

        if not replicate_model:
            return error_response(
                error=f"Model family '{family_id}' does not support image-to-video.",
                error_type="unsupported_modality",
                provider="replicate",
                model=family_id,
                prompt=prompt,
            )

        payload: Dict[str, Any] = {"prompt": prompt}

        # image input
        if use_image:
            key = family.get("image_param_key", "first_frame_image")
            payload[key] = image_url

        # aspect ratio
        aspect_ratios = family.get("aspect_ratios")
        if aspect_ratios and aspect_ratio in aspect_ratios:
            payload["aspect_ratio"] = aspect_ratio

        # seed
        if seed is not None:
            payload["seed"] = seed

        # extra model-specific defaults
        extra = family.get("extra_input", {})
        for k, v in extra.items():
            payload.setdefault(k, v)

        try:
            client = _replicate.Client(api_token=token)
            output = client.run(replicate_model, input=payload)

            if output is None:
                return error_response(
                    error="Replicate returned no output",
                    error_type="empty_response",
                    provider="replicate",
                    model=family_id,
                    prompt=prompt,
                )

            url: Optional[str] = None
            if isinstance(output, str):
                url = output
            elif isinstance(output, list) and output:
                url = str(output[0])
            elif hasattr(output, "url"):
                url = str(output.url)
            else:
                url = str(output)

            if not url:
                return error_response(
                    error="Replicate returned empty video URL",
                    error_type="empty_response",
                    provider="replicate",
                    model=family_id,
                    prompt=prompt,
                )

            return success_response(
                video=url,
                model=family_id,
                prompt=prompt,
                modality=modality,
                aspect_ratio=aspect_ratio,
                duration=duration or 0,
                provider="replicate",
                extra={"replicate_model": replicate_model},
            )

        except Exception as exc:
            logger.warning("Replicate video generation failed: %s", exc, exc_info=True)
            return error_response(
                error=f"Replicate request failed: {exc}",
                error_type=type(exc).__name__,
                provider="replicate",
                model=family_id,
                prompt=prompt,
            )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    ctx.register_video_gen_provider(ReplicateVideoGenProvider())
