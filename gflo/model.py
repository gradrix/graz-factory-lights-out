"""One serialized, bounded turn against an explicitly configured local vLLM."""

from __future__ import annotations

import fcntl
import hashlib
import http.client
import json
import os
import socket
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.records import Digest, Record, WorkAtom
from gflo.worker import (
    CandidateResult,
    ReadFileRequest,
    WorkerError,
    compose_view,
    messages,
    parse_result,
    strict_json,
)


class ModelError(RuntimeError):
    """Transport/protocol/budget failure; raw evidence remains in the artifact store."""


class ModelProfile(Record):
    profile_id: Literal["vllm-python-worker-v1"] = "vllm-python-worker-v1"
    base_url: str
    model: str
    deployment_digest: Digest
    context_limit: Annotated[int, Field(ge=1, le=16384)] = 16384
    timeout_seconds: Annotated[float, Field(gt=0, le=120, allow_inf_nan=False)] = 120.0

    @model_validator(mode="after")
    def local_endpoint(self) -> ModelProfile:
        url = urlsplit(self.base_url)
        if (
            url.scheme != "http"
            or url.hostname not in ("127.0.0.1", "::1")
            or url.username is not None
            or url.password is not None
            or url.path != "/v1"
            or url.query
            or url.fragment
            or url.port is None
            or not self.model
            or len(self.model) > 200
        ):
            raise ValueError(
                "Worker profile requires an explicit numeric-loopback HTTP /v1 endpoint"
            )
        return self


class ContextManifest(Record):
    profile_digest: Digest
    view_digest: Digest
    request_digest: Digest
    prompt_tokens: int
    output_reserved: int
    total_limit: int
    accounting: Literal["vllm-chat-tokenize-v1"] = "vllm-chat-tokenize-v1"


class ModelTurn(Record):
    manifest_digest: Digest
    response_digest: Digest
    result: CandidateResult | ReadFileRequest
    prompt_tokens: int
    completion_tokens: int
    elapsed_seconds: float


class LocalModel:
    def __init__(self, artifacts: ArtifactStore, profile: ModelProfile):
        self.artifacts = artifacts
        self.profile = ModelProfile.model_validate(profile)
        self.last_evidence_digest: str | None = None
        # One lock per endpoint, shared across this user's Factory instances.
        lock_root = Path.home() / ".cache" / "gflo" / "model-locks"
        lock_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock_path = lock_root / hashlib.sha256(profile.base_url.encode()).hexdigest()

    def _request(
        self,
        path: str,
        payload: dict[str, Any] | None,
        deadline: float,
        exchanges: list[dict[str, Any]],
    ) -> dict[str, Any]:
        remaining = deadline - time.monotonic()
        request_started = time.monotonic()
        if remaining <= 0:
            raise ModelError("Model turn deadline exceeded")
        url = urlsplit(self.profile.base_url)
        assert url.hostname is not None
        connection = http.client.HTTPConnection(url.hostname, url.port, timeout=remaining)
        raw_request = json.dumps(payload, sort_keys=True).encode() if payload is not None else b""
        exchange: dict[str, Any] = {
            "path": path,
            "request_digest": self.artifacts.publish(raw_request),
        }
        exchanges.append(exchange)
        chunks: list[bytes] = []
        timer: threading.Timer | None = None
        try:
            connection.connect()
            sock = connection.sock
            assert sock is not None

            def expire() -> None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(max(0, deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request(
                "POST" if payload is not None else "GET",
                path,
                body=raw_request if payload is not None else None,
                headers={"Content-Type": "application/json", "Connection": "close"},
            )
            response = connection.getresponse()
            exchange["status"] = response.status
            size = 0
            while True:
                chunk = response.read1(min(65536, 2097153 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > 2097152:
                    raise ModelError("Model response exceeds 2 MiB")
            if time.monotonic() >= deadline:
                raise ModelError("Model turn deadline exceeded")
            if response.length not in (None, 0):
                raise ModelError("Incomplete model HTTP response")
            if response.status != 200:
                raise ModelError(f"Model endpoint rejected request: HTTP {response.status}")
            try:
                body = strict_json(b"".join(chunks))
            except ValueError as exc:
                raise ModelError("Malformed endpoint JSON") from exc
            if not isinstance(body, dict):
                raise ModelError("Model endpoint must return a JSON object")
            return body
        except (OSError, http.client.HTTPException) as exc:
            raise ModelError("Local model transport failed or timed out") from exc
        finally:
            if timer is not None:
                timer.cancel()
                timer.join(timeout=1)
            connection.close()
            exchange["response_digest"] = self.artifacts.publish(b"".join(chunks))
            exchange["elapsed_seconds"] = time.monotonic() - request_started

    def turn(
        self,
        atom: WorkAtom,
        source_digest: str,
        *,
        current_inputs: Callable[[], str],
        selected_paths: tuple[str, ...] | None = None,
        diagnostic_digests: tuple[str, ...] = (),
    ) -> ModelTurn:
        """Produce a validated proposal only; no file write, tool dispatch or acceptance."""
        atom = WorkAtom.model_validate(atom)
        self.last_evidence_digest = None
        started = time.monotonic()
        deadline = started + self.profile.timeout_seconds
        exchanges: list[dict[str, Any]] = []
        evidence: dict[str, Any] = {
            "profile": self.profile.model_dump(mode="json"),
            "contract_digest": atom.digest(),
            "exchanges": exchanges,
        }
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise ModelError("Model serialization deadline exceeded")
                    time.sleep(0.01)
            self.artifacts.verify(self.profile.deployment_digest)
            if current_inputs() != atom.inputs_digest:
                raise WorkerError("Stale inputs before model turn")
            view = compose_view(
                self.artifacts,
                atom,
                source_digest,
                selected_paths=selected_paths,
                diagnostic_digests=diagnostic_digests,
            )
            evidence["view_digest"] = self.artifacts.publish(view.canonical().encode())
            models = self._request("/v1/models", None, deadline, exchanges)
            if not isinstance(models.get("data"), list) or not any(
                m.get("id") == self.profile.model
                for m in models.get("data", [])
                if isinstance(m, dict)
            ):
                raise ModelError("Configured local model is not served")
            chat = {
                "model": self.profile.model,
                "messages": messages(view),
                "chat_template_kwargs": {"enable_thinking": False},
            }
            tokens = self._request(
                "/tokenize", chat | {"add_generation_prompt": True}, deadline, exchanges
            )
            count = tokens.get("count")
            if tokens.get("max_model_len") != self.profile.context_limit:
                raise ModelError("Served context limit differs from the pinned profile")
            if type(count) is not int or count <= 0:
                raise ModelError("Tokenizer did not return an exact positive token count")
            limit = min(atom.context_budget.total_tokens, self.profile.context_limit)
            reserve = atom.context_budget.output_tokens
            if count + reserve > limit:
                raise ModelError("Worker context exceeds its input/output budget")
            request = chat | {
                "temperature": 0,
                "seed": 42,
                "max_tokens": reserve,
                "response_format": {"type": "json_object"},
                "stream": False,
            }
            manifest = ContextManifest(
                profile_digest=self.profile.digest(),
                view_digest=evidence["view_digest"],
                request_digest=self.artifacts.publish(json.dumps(request, sort_keys=True).encode()),
                prompt_tokens=count,
                output_reserved=reserve,
                total_limit=limit,
            )
            evidence["manifest_digest"] = self.artifacts.publish(manifest.canonical().encode())
            if current_inputs() != atom.inputs_digest:
                raise WorkerError("Stale inputs before generation")
            response = self._request("/v1/chat/completions", request, deadline, exchanges)
            if response.get("model") != self.profile.model:
                raise ModelError("Response model differs from the configured model")
            if current_inputs() != atom.inputs_digest:
                raise WorkerError("Stale inputs after model turn")
            choices = response.get("choices")
            if (
                not isinstance(choices, list)
                or len(choices) != 1
                or not isinstance(choices[0], dict)
            ):
                raise ModelError("Expected exactly one model choice")
            choice = choices[0]
            message = choice.get("message")
            if (
                choice.get("finish_reason") != "stop"
                or not isinstance(message, dict)
                or message.get("role") != "assistant"
                or message.get("tool_calls")
                or message.get("refusal")
                or not isinstance(message.get("content"), str)
            ):
                raise ModelError("Incomplete or unsupported worker response")
            usage = response.get("usage")
            if not isinstance(usage, dict):
                raise ModelError("Missing token accounting")
            prompt, completion, total = (
                usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens")
            )
            if type(prompt) is not int or type(completion) is not int or type(total) is not int:
                raise ModelError("Token usage must contain integers")
            if (
                min(prompt, completion, total) <= 0
                or prompt != count
                or completion > reserve
                or total != prompt + completion
                or total > limit
            ):
                raise ModelError("Token accounting differs from the bounded request")
            result = parse_result(
                message["content"],
                atom,
                SourceBundle.model_validate_json(self.artifacts.read(source_digest)),
            )
            turn = ModelTurn(
                manifest_digest=manifest.digest(),
                response_digest=exchanges[-1]["response_digest"],
                result=result,
                prompt_tokens=prompt,
                completion_tokens=completion,
                elapsed_seconds=time.monotonic() - started,
            )
            evidence["turn_digest"] = self.artifacts.publish(turn.canonical().encode())
            return turn
        except BaseException as exc:
            evidence["error"] = {"type": type(exc).__name__, "message": str(exc)[:2048]}
            raise
        finally:
            os.close(fd)
            evidence["elapsed_seconds"] = time.monotonic() - started
            self.last_evidence_digest = self.artifacts.publish(
                json.dumps(evidence, sort_keys=True).encode()
            )
