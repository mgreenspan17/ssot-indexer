from __future__ import annotations

import json
import threading
import time
from hashlib import blake2b
from dataclasses import dataclass
from typing import Callable, Protocol

from ssot_core.models import (
    AuditEvent,
    CanonicalFile,
    DesktopCamFrame,
    DesktopCamSession,
    DesktopCamState,
    FileInstance,
    FileVersion,
    ForensicBundle,
)
from uuid import uuid7_str

try:  # pragma: no cover - environment dependent
    from blake3 import blake3 as _blake3
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    _blake3 = None


class FrameSource(Protocol):
    def next_frame(self) -> bytes:
        """Return the next frame bytes (PNG/JPEG/raw encoded by source implementation)."""


@dataclass(frozen=True)
class DesktopCamCaptureResult:
    frame: DesktopCamFrame
    version: FileVersion
    instance: FileInstance
    canonical: CanonicalFile
    event: AuditEvent


class DesktopCamRecorder:
    """Forensic-grade append-only screen recorder with chain-of-custody events."""

    def __init__(
        self,
        frame_source: FrameSource,
        *,
        device_id: str,
        fps: int = 2,
        flush_event: Callable[[AuditEvent], None] | None = None,
    ) -> None:
        if fps < 1 or fps > 10:
            raise ValueError("fps must be between 1 and 10")
        self.frame_source = frame_source
        self.device_id = device_id
        self.fps = fps
        self.flush_event = flush_event

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.frames: list[DesktopCamFrame] = []
        self.events: list[AuditEvent] = []
        self.captures: list[DesktopCamCaptureResult] = []

        self.session = DesktopCamSession(
            session_id=uuid7_str(),
            device_id=device_id,
            fps=fps,
            state=DesktopCamState.stopped,
            started_at=None,
            stopped_at=None,
            frame_count=0,
            last_error=None,
        )

    def start_desktopcam(self, max_frames: int | None = None) -> DesktopCamSession:
        if self.session.state == DesktopCamState.running:
            return self.session

        self._stop_event.clear()
        self.session = DesktopCamSession(
            session_id=self.session.session_id,
            device_id=self.session.device_id,
            fps=self.session.fps,
            state=DesktopCamState.running,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            stopped_at=None,
            frame_count=self.session.frame_count,
            last_error=None,
        )

        self._thread = threading.Thread(
            target=self._capture_loop,
            kwargs={"max_frames": max_frames},
            daemon=True,
        )
        self._thread.start()
        if max_frames is not None:
            self._thread.join()
        return self.session

    def stop_desktopcam(self) -> DesktopCamSession:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self.session = DesktopCamSession(
            session_id=self.session.session_id,
            device_id=self.session.device_id,
            fps=self.session.fps,
            state=DesktopCamState.stopped,
            started_at=self.session.started_at,
            stopped_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            frame_count=len(self.frames),
            last_error=self.session.last_error,
        )
        return self.session

    def verify_event_chain(self) -> bool:
        previous_event_hash: str | None = None
        for event in self.events:
            payload = _event_payload(event.timestamp_uuid7, event.blake3_hash, event.frame_id, previous_event_hash)
            expected = _hash_bytes(payload).digest
            if event.event_hash != expected:
                return False
            previous_event_hash = event.event_hash
        return True

    def export_forensic_bundle(self) -> ForensicBundle:
        return ForensicBundle(
            session=self.session,
            frames=tuple(self.frames),
            events=tuple(self.events),
            chain_valid=self.verify_event_chain(),
        )

    def recover_partial_sequences(self) -> int:
        """Return number of valid chain events from sequence start for crash recovery."""
        previous_event_hash: str | None = None
        for index, event in enumerate(self.events):
            payload = _event_payload(event.timestamp_uuid7, event.blake3_hash, event.frame_id, previous_event_hash)
            expected = _hash_bytes(payload).digest
            if event.event_hash != expected:
                return index
            previous_event_hash = event.event_hash
        return len(self.events)

    def _capture_loop(self, max_frames: int | None = None) -> None:
        interval = 1.0 / float(self.fps)
        captured = 0
        while not self._stop_event.is_set():
            try:
                raw_frame = self.frame_source.next_frame()
                previous_event_hash = self.events[-1].event_hash if self.events else None
                result = materialize_frame_for_ssot(
                    raw_frame,
                    provider="desktopcam",
                    source_id=f"{self.device_id}:{captured}",
                    path=f"desktopcam://{self.device_id}/{captured}",
                    device_id=self.device_id,
                    previous_event_hash=previous_event_hash,
                )
                self.frames.append(result.frame)
                self.events.append(result.event)
                self.captures.append(result)

                # Immediate durability hook for append-only audit semantics.
                if self.flush_event is not None:
                    self.flush_event(result.event)

                captured += 1
                self.session = DesktopCamSession(
                    session_id=self.session.session_id,
                    device_id=self.session.device_id,
                    fps=self.session.fps,
                    state=self.session.state,
                    started_at=self.session.started_at,
                    stopped_at=self.session.stopped_at,
                    frame_count=len(self.frames),
                    last_error=None,
                )

                if max_frames is not None and captured >= max_frames:
                    self._stop_event.set()
                    break

                time.sleep(interval)
            except Exception as exc:  # pragma: no cover - defensive runtime safety
                self.session = DesktopCamSession(
                    session_id=self.session.session_id,
                    device_id=self.session.device_id,
                    fps=self.session.fps,
                    state=self.session.state,
                    started_at=self.session.started_at,
                    stopped_at=self.session.stopped_at,
                    frame_count=len(self.frames),
                    last_error=str(exc),
                )
                self._stop_event.set()


class DesktopCamService:
    """Service wrapper exposing stable API methods for DesktopCam operations."""

    def __init__(self, recorder: DesktopCamRecorder) -> None:
        self.recorder = recorder

    def start_desktopcam(self, max_frames: int | None = None) -> DesktopCamSession:
        return self.recorder.start_desktopcam(max_frames=max_frames)

    def stop_desktopcam(self) -> DesktopCamSession:
        return self.recorder.stop_desktopcam()

    def verify_event_chain(self) -> bool:
        return self.recorder.verify_event_chain()

    def export_forensic_bundle(self) -> ForensicBundle:
        return self.recorder.export_forensic_bundle()


def materialize_frame_for_ssot(
    frame_bytes: bytes,
    *,
    provider: str,
    source_id: str,
    path: str,
    device_id: str,
    mime_type: str = "image/png",
    previous_event_hash: str | None = None,
) -> DesktopCamCaptureResult:
    """Convert a captured frame into canonical/version/instance and append-only audit event."""
    digest = _hash_bytes(frame_bytes)
    timestamp_uuid7 = uuid7_str()

    canonical = CanonicalFile.create(digest.digest, digest.size, mime_type)
    version = FileVersion.create(
        canonical_id=canonical.canonical_id,
        blake3_hash=digest.digest,
        size=digest.size,
        provider=provider,
        path=path,
    )

    frame = DesktopCamFrame.create(
        timestamp_uuid7=timestamp_uuid7,
        blake3_hash=digest.digest,
        bytes_size=digest.size,
        canonical_file_id=canonical.canonical_id,
        version_id=version.version_id,
        mime_type=mime_type,
    )

    instance = FileInstance.create(
        source_id=source_id,
        provider=provider,
        path=path,
        blake3_hash=digest.digest,
        size=digest.size,
        mime_type=mime_type,
        modified_at=frame.captured_at,
        canonical_id=canonical.canonical_id,
        version_id=version.version_id,
        device_id=device_id,
    )

    payload = _event_payload(timestamp_uuid7, digest.digest, frame.frame_id, previous_event_hash)
    event_hash = _hash_bytes(payload).digest
    event = AuditEvent.create(
        timestamp_uuid7=timestamp_uuid7,
        blake3_hash=digest.digest,
        frame_id=frame.frame_id,
        previous_event_hash=previous_event_hash,
        event_hash=event_hash,
    )

    return DesktopCamCaptureResult(
        frame=frame,
        version=version,
        instance=instance,
        canonical=canonical,
        event=event,
    )


def _event_payload(
    timestamp_uuid7: str,
    blake3_hash: str,
    frame_id: str,
    previous_event_hash: str | None,
) -> bytes:
    return json.dumps(
        {
            "timestamp_uuid7": timestamp_uuid7,
            "blake3_hash": blake3_hash,
            "frame_id": frame_id,
            "previous_event_hash": previous_event_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class _Digest:
    digest: str
    size: int


def _hash_bytes(payload: bytes) -> _Digest:
    if _blake3 is not None:
        hasher = _blake3()
        hasher.update(payload)
        return _Digest(digest=hasher.hexdigest(), size=len(payload))

    # Fallback path for environments where the blake3 wheel is unavailable.
    fallback = blake2b(payload, digest_size=32)
    return _Digest(digest=fallback.hexdigest(), size=len(payload))


def start_desktopcam(recorder: DesktopCamRecorder, max_frames: int | None = None) -> DesktopCamSession:
    return recorder.start_desktopcam(max_frames=max_frames)


def stop_desktopcam(recorder: DesktopCamRecorder) -> DesktopCamSession:
    return recorder.stop_desktopcam()


def verify_event_chain(recorder: DesktopCamRecorder) -> bool:
    return recorder.verify_event_chain()


def export_forensic_bundle(recorder: DesktopCamRecorder) -> ForensicBundle:
    return recorder.export_forensic_bundle()
