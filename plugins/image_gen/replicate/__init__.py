"""Replicate image generation backend.

Supports FLUX 1.1 Pro Ultra (default), FLUX 1.1 Pro, Flux Schnell,
Ideogram v3 and Stable Diffusion 3.5 via the Replicate Python client.

Authentication: REPLICATE_API_TOKEN env var or ~/.hermes/.env.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    resolve_aspect_ratio,
    error_response,
    success_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

REPLICATE_MODELS: Dict[str, Dict[str, Any]] = {
    "black-forest-labs/flux-1.1-pro-ultra": {
        "display": "FLUX 1.1 Pro Ultra",
        "speed": "~15-30s",
        "strengths": "Highest quality. Up to 4MP. Best for photorealism and complex prompts.",
        "price": "~$0.06/img",
        "aspect_ratios": {
            "landscape": "16:9",
            "square": "1:1",
            "portrait": "9:16",
        },
        "input_key": "aspect_ratio",
        "output_format": "webp",
        "output_quality": 80,
        "safety_tolerance": 2,
        "prompt_upsampling": True,
    },
    "black-forest-labs/flux-1.1-pro": {
        "display": "FLUX 1.1 Pro",
        "speed": "~8-15s",
        "strengths": "Fast, high quality. Great balance of speed and detail.",
        "price": "~$0.04/img",
        "aspect_ratios": {
            "landscape": "16:9",
            "square": "1:1",
            "portrait": "9:16",
        },
        "input_key": "aspect_ratio",
        "output_format": "webp",
        "output_quality": 80,
        "safety_tolerance": 2,
        "prompt_upsampling": True,
    },
    "black-forest-labs/flux-schnell": {
        "display": "FLUX Schnell",
        "speed": "~2-5s",
        "strengths": "Fastest FLUX. Good for drafts and iterations.",
        "price": "~$0.003/img",
        "aspect_ratios": {
            "landscape": "16:9",
            "square": "1:1",
            "portrait": "9:16",
        },
        "input_key": "aspect_ratio",
    },
    "ideogram-ai/ideogram-v3-balanced": {
        "display": "Ideogram v3 Balanced",
        "speed": "~10-20s",
        "strengths": "Excellent text rendering in images, stylized art.",
        "price": "~$0.08/img",
        "aspect_ratios": {
            "landscape": "ASPECT_16_9",
            "square": "ASPECT_1_1",
            "portrait": "ASPECT_9_16",
        },
        "input_key": "aspect_ratio",
        "rendering_quality": "QUALITY",
    },
    "stability-ai/stable-diffusion-3.5-large": {
        "display": "Stable Diffusion 3.5 Large",
        "speed": "~15-25s",
        "strengths": "Open weights, good for creative and stylized outputs.",
        "price": "~$0.065/img",
        "aspect_ratios": {
            "landscape": "16:9",
            "square": "1:1",
            "portrait": "9:16",
        },
        "input_key": "aspect_ratio",
        "output_format": "webp",
        "output_quality": 90,
        "cfg_scale": 4.5,
        "steps": 40,
    },
}

DEFAULT_MODEL = "black-forest-labs/flux-1.1-pro-ultra"


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


def _resolve_model(model_override: Optional[str]) -> tuple[str, Dict[str, Any]]:
    if model_override and model_override.strip() in REPLICATE_MODELS:
        mid = model_override.strip()
        return mid, REPLICATE_MODELS[mid]

    env_model = os.getenv("REPLICATE_IMAGE_MODEL", "").strip()
    if env_model in REPLICATE_MODELS:
        return env_model, REPLICATE_MODELS[env_model]

    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        img_cfg = cfg.get("image_gen") or {}
        rep_cfg = img_cfg.get("replicate") if isinstance(img_cfg, dict) else {}
        if isinstance(rep_cfg, dict):
            cfg_model = rep_cfg.get("model", "").strip()
            if cfg_model in REPLICATE_MODELS:
                return cfg_model, REPLICATE_MODELS[cfg_model]
    except Exception:
        pass

    return DEFAULT_MODEL, REPLICATE_MODELS[DEFAULT_MODEL]


class ReplicateImageGenProvider(ImageGenProvider):
    """Replicate image generation backend."""

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
                "id": model_id,
                "display": meta["display"],
                "speed": meta.get("speed", ""),
                "strengths": meta.get("strengths", ""),
                "price": meta.get("price", ""),
            }
            for model_id, meta in REPLICATE_MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Replicate",
            "badge": "paid",
            "tag": "FLUX 1.1 Pro Ultra, Ideogram v3, SD 3.5 and more.",
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
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
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

        aspect = resolve_aspect_ratio(aspect_ratio)
        model_id, meta = _resolve_model(kwargs.get("model"))

        aspect_map = meta.get("aspect_ratios", {})
        api_aspect = aspect_map.get(aspect, aspect_map.get("landscape", "16:9"))

        payload: Dict[str, Any] = {
            "prompt": prompt,
        }
        input_key = meta.get("input_key", "aspect_ratio")
        payload[input_key] = api_aspect

        for field in ("output_format", "output_quality", "safety_tolerance", "prompt_upsampling",
                      "rendering_quality", "cfg_scale", "steps"):
            if field in meta:
                payload[field] = meta[field]

        try:
            client = _replicate.Client(api_token=token)
            output = client.run(model_id, input=payload)

            if output is None:
                return error_response(
                    error="Replicate returned no output",
                    error_type="empty_response",
                    provider="replicate",
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )

            url: Optional[str] = None
            if isinstance(output, list) and output:
                url = str(output[0])
            elif hasattr(output, "url"):
                url = str(output.url)
            elif isinstance(output, str):
                url = output
            else:
                url = str(output)

            if not url:
                return error_response(
                    error="Replicate returned empty URL",
                    error_type="empty_response",
                    provider="replicate",
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )

            return success_response(
                image=url,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
                provider="replicate",
            )

        except Exception as exc:
            logger.warning("Replicate image generation failed: %s", exc, exc_info=True)
            return error_response(
                error=f"Replicate request failed: {exc}",
                error_type=type(exc).__name__,
                provider="replicate",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    ctx.register_image_gen_provider(ReplicateImageGenProvider())
