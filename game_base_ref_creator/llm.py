"""Hugging Face model loader and document generator."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from .creation_utils import extract_json_object, finalize_creation
from .prompts import SYSTEM_MESSAGE, build_prompt

logger = logging.getLogger(__name__)

# Re-export for older imports / tests
__all__ = ["ModelManager", "model_manager", "extract_json_object"]

ProgressCallback = Callable[[Any], None]


def _install_download_progress_hooks(emit: Callable[..., None]) -> Callable[[], None]:
    """Patch tqdm so Hugging Face file downloads report percent to the UI."""
    restorers: list[Callable[[], None]] = []

    try:
        from tqdm import tqdm as std_tqdm
    except ImportError:
        return lambda: None

    class ReportingTqdm(std_tqdm):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._last_pct = -1
            self._report(force=True)

        def update(self, n: float = 1) -> bool | None:  # type: ignore[override]
            result = super().update(n)
            self._report()
            return result

        def _report(self, force: bool = False) -> None:
            total = self.total or 0
            if total <= 0:
                desc = (self.desc or "Downloading files").strip()
                emit(desc, None, phase="download")
                return
            pct = min(100.0, 100.0 * float(self.n) / float(total))
            ipct = int(pct)
            if not force and ipct == self._last_pct:
                return
            self._last_pct = ipct
            desc = (self.desc or "Downloading").strip() or "Downloading"
            emit(f"{desc} ({ipct}%)", float(pct), phase="download")

    try:
        import tqdm as tqdm_mod

        original = tqdm_mod.tqdm
        tqdm_mod.tqdm = ReportingTqdm  # type: ignore[misc,assignment]
        restorers.append(lambda orig=original: setattr(tqdm_mod, "tqdm", orig))
    except Exception:  # noqa: BLE001
        pass

    try:
        import tqdm.auto as tqdm_auto

        original_auto = tqdm_auto.tqdm
        tqdm_auto.tqdm = ReportingTqdm  # type: ignore[misc,assignment]
        restorers.append(lambda orig=original_auto: setattr(tqdm_auto, "tqdm", orig))
    except Exception:  # noqa: BLE001
        pass

    try:
        import huggingface_hub.utils.tqdm as hub_tqdm

        if hasattr(hub_tqdm, "tqdm"):
            original_hub = hub_tqdm.tqdm
            hub_tqdm.tqdm = ReportingTqdm  # type: ignore[misc,assignment]
            restorers.append(lambda orig=original_hub: setattr(hub_tqdm, "tqdm", orig))
    except Exception:  # noqa: BLE001
        pass

    def restore() -> None:
        for fn in restorers:
            try:
                fn()
            except Exception:  # noqa: BLE001
                pass

    return restore


def _resolve_dtype(name: str):
    import torch

    mapping = {
        "auto": "auto",
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }
    return mapping.get(str(name).lower(), "auto")


def _resolve_device(name: str) -> str:
    import torch

    name = (name or "auto").lower()
    if name != "auto":
        return name
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _is_phi3_repo(repo_id: str) -> bool:
    r = (repo_id or "").lower()
    return "phi-3" in r or "phi3" in r


def _resolve_trust_remote_code(repo_id: str, model_cfg: dict[str, Any]) -> bool:
    """
    Prefer built-in transformers implementations when available.

    Phi-3 / Phi-3.5 remote modeling_phi3.py still references Cache.seen_tokens,
    which was removed from DynamicCache in recent transformers — that raises
    AttributeError during generate(). Native transformers Phi-3 code is fine.
    """
    explicit = model_cfg.get("trust_remote_code", None)
    if _is_phi3_repo(repo_id):
        if explicit is True:
            logger.warning(
                "Ignoring trust_remote_code=True for %s — remote Phi-3 code is "
                "incompatible with current transformers DynamicCache. "
                "Loading built-in Phi-3 implementation instead.",
                repo_id,
            )
        return False
    if explicit is None:
        return False
    return bool(explicit)


def _to_input_ids(tokenizer: Any, messages: list[dict[str, str]], flat_fallback: str):
    """Build a 2D LongTensor of input ids for model.generate()."""
    import torch

    encoded: Any
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        # Prefer string template + encode — return_tensors on apply_chat_template
        # can yield a BatchEncoding in some transformers versions, which breaks generate().
        try:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            encoded = tokenizer(text, return_tensors="pt")
        except Exception:  # noqa: BLE001
            encoded = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
            )
    else:
        encoded = tokenizer(flat_fallback, return_tensors="pt")

    if hasattr(encoded, "input_ids"):
        input_ids = encoded.input_ids
    elif isinstance(encoded, dict) and "input_ids" in encoded:
        input_ids = encoded["input_ids"]
    else:
        input_ids = encoded

    if not isinstance(input_ids, torch.Tensor):
        input_ids = torch.tensor(input_ids, dtype=torch.long)
    if input_ids.dim() == 1:
        input_ids = input_ids.unsqueeze(0)
    return input_ids


class ModelManager:
    """Loads and runs a configurable Hugging Face instruct model."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._model = None
        self._tokenizer = None
        self._loaded_repo: str | None = None
        self._loaded_revision: str | None = None
        self._device: str = "cpu"
        self._status = "idle"
        self._status_detail = "Model not loaded yet. It will download on first generation."
        self._progress: ProgressCallback | None = None
        self._loaded_trust_remote_code = False

    @property
    def status(self) -> dict[str, Any]:
        return {
            "state": self._status,
            "detail": self._status_detail,
            "loaded_repo": self._loaded_repo,
            "loaded_revision": self._loaded_revision,
            "device": self._device,
        }

    def set_progress_callback(self, cb: ProgressCallback | None) -> None:
        self._progress = cb

    def _emit(
        self,
        message: str,
        percent: float | None = None,
        *,
        phase: str | None = None,
        title: str | None = None,
    ) -> None:
        self._status_detail = message
        logger.info(message)
        if not self._progress:
            return
        payload: dict[str, Any] = {"message": message}
        if percent is not None:
            payload["percent"] = percent
        if phase:
            payload["phase"] = phase
        if title:
            payload["title"] = title
        try:
            self._progress(payload)
        except Exception:  # noqa: BLE001 — UI callback must not break generation
            pass

    def unload(self) -> None:
        with self._lock:
            self._model = None
            self._tokenizer = None
            self._loaded_repo = None
            self._loaded_revision = None
            self._loaded_trust_remote_code = False
            self._status = "idle"
            self._status_detail = "Model unloaded."
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass

    def ensure_loaded(self, model_cfg: dict[str, Any]) -> None:
        repo_id = model_cfg.get("repo_id") or "microsoft/Phi-3.5-mini-instruct"
        revision = model_cfg.get("revision") or "main"

        with self._lock:
            trust = _resolve_trust_remote_code(repo_id, model_cfg)
            if (
                self._model is not None
                and self._tokenizer is not None
                and self._loaded_repo == repo_id
                and self._loaded_revision == revision
                and self._loaded_trust_remote_code == trust
            ):
                return

            # Drop incompatible in-memory weights (e.g. Phi loaded with remote code)
            if self._model is not None:
                self._model = None
                self._tokenizer = None
                self._loaded_repo = None
                self._loaded_revision = None
                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:  # noqa: BLE001
                    pass

            self._status = "loading"
            self._emit(
                f"Downloading / loading {repo_id} from Hugging Face…",
                phase="download",
                title="Downloading model",
            )

            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            device = _resolve_device(model_cfg.get("device", "auto"))
            dtype = _resolve_dtype(model_cfg.get("torch_dtype", "auto"))
            token = model_cfg.get("hf_token") or None
            # trust already resolved above for cache-key comparison

            restore_hooks = _install_download_progress_hooks(self._emit)
            try:
                self._emit(
                    f"Loading tokenizer for {repo_id}…",
                    phase="load",
                    title="Loading model",
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    repo_id,
                    revision=revision,
                    trust_remote_code=trust,
                    token=token,
                )

                load_kwargs: dict[str, Any] = {
                    "revision": revision,
                    "trust_remote_code": trust,
                    "token": token,
                }
                if dtype != "auto":
                    load_kwargs["torch_dtype"] = dtype
                else:
                    load_kwargs["torch_dtype"] = "auto"

                if device == "cuda":
                    load_kwargs["device_map"] = "auto"
                elif device == "mps":
                    load_kwargs["torch_dtype"] = torch.float16 if dtype == "auto" else dtype

                self._emit(
                    f"Loading weights for {repo_id} on {device} "
                    f"(trust_remote_code={trust})…",
                    phase="load",
                    title="Loading model",
                )
                model = AutoModelForCausalLM.from_pretrained(repo_id, **load_kwargs)
            finally:
                restore_hooks()

            self._emit(
                f"Moving model to {device}…",
                phase="load",
                title="Loading model",
            )
            if device == "cpu":
                model = model.to("cpu")
            elif device == "mps":
                model = model.to("mps")

            model.eval()
            self._model = model
            self._tokenizer = tokenizer
            self._loaded_repo = repo_id
            self._loaded_revision = revision
            self._loaded_trust_remote_code = trust
            self._device = device
            self._status = "ready"
            self._emit(
                f"Ready: {repo_id} on {device}",
                percent=100,
                phase="ready",
                title="Model ready",
            )

    def generate_creation(
        self,
        game: str,
        platform: str,
        creation_type: str,
        model_cfg: dict[str, Any],
        system_extra: str = "",
        creation_description: str = "",
        exact_title: bool = False,
    ) -> dict[str, Any]:
        self.ensure_loaded(model_cfg)

        with self._lock:
            assert self._model is not None and self._tokenizer is not None
            self._status = "generating"
            self._emit(
                f"Generating {creation_type} for {game}…",
                phase="generate",
                title="Generating document",
            )

            prompt = build_prompt(
                game,
                platform,
                creation_type,
                system_extra=system_extra,
                creation_description=creation_description,
                exact_title=exact_title,
            )
            tokenizer = self._tokenizer
            model = self._model

            messages = [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ]

            import torch

            input_ids = _to_input_ids(
                tokenizer,
                messages,
                flat_fallback=f"{SYSTEM_MESSAGE}\n\n{prompt}",
            )
            device = next(model.parameters()).device
            input_ids = input_ids.to(device)
            prompt_len = input_ids.shape[-1]

            max_new = int(model_cfg.get("max_new_tokens") or 4096)
            temperature = float(model_cfg.get("temperature") or 0.4)
            top_p = float(model_cfg.get("top_p") or 0.9)
            do_sample = temperature > 0

            gen_kwargs: dict[str, Any] = {
                "max_new_tokens": max_new,
                "do_sample": do_sample,
                "pad_token_id": tokenizer.eos_token_id or tokenizer.pad_token_id,
            }
            if do_sample:
                gen_kwargs["temperature"] = max(temperature, 0.01)
                gen_kwargs["top_p"] = top_p

            # Heartbeat while generate() blocks so the UI keeps updating
            stop_heartbeat = threading.Event()

            def _heartbeat() -> None:
                started = time.time()
                while not stop_heartbeat.wait(1.5):
                    elapsed = int(time.time() - started)
                    self._emit(
                        f"Generating {creation_type} for {game}… "
                        f"({elapsed}s — local model is thinking)",
                        phase="generate",
                        title="Generating document",
                    )

            beat = threading.Thread(target=_heartbeat, daemon=True)
            beat.start()
            try:
                with torch.no_grad():
                    try:
                        output = model.generate(input_ids, **gen_kwargs)
                    except AttributeError as exc:
                        # Remote Phi-3 code + new DynamicCache mismatch
                        if "seen_tokens" not in str(exc):
                            raise
                        self._emit(
                            "Cache compatibility issue — retrying with use_cache=False…",
                            phase="generate",
                            title="Generating document",
                        )
                        gen_kwargs = dict(gen_kwargs)
                        gen_kwargs["use_cache"] = False
                        output = model.generate(input_ids, **gen_kwargs)
            finally:
                stop_heartbeat.set()
                beat.join(timeout=1.0)

            generated = output[0][prompt_len:]
            text = tokenizer.decode(generated, skip_special_tokens=True)
            self._emit("Parsing model JSON…", phase="generate", title="Generating document")

            parsed = finalize_creation(
                text,
                game,
                platform,
                creation_type,
                model_info={
                    "provider": "huggingface",
                    "repo_id": self._loaded_repo,
                    "revision": self._loaded_revision,
                    "device": self._device,
                },
                exact_title=exact_title,
            )

            self._status = "ready"
            self._emit(f"Ready: {self._loaded_repo} on {self._device}")
            return parsed


# Process-wide singleton
model_manager = ModelManager()
