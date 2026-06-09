from __future__ import annotations

from ssot_core.desktopcam import (
    DesktopCamService,
    DesktopCamRecorder,
    export_forensic_bundle,
    start_desktopcam,
    stop_desktopcam,
    verify_event_chain,
)
from ssot_core.models import DesktopCamState


class _StaticFrameSource:
    def __init__(self, frames: list[bytes]) -> None:
        self.frames = frames
        self.idx = 0

    def next_frame(self) -> bytes:
        frame = self.frames[self.idx % len(self.frames)]
        self.idx += 1
        return frame


def test_desktopcam_capture_and_verify_chain():
    source = _StaticFrameSource([b"frame-1", b"frame-2", b"frame-3"])
    recorder = DesktopCamRecorder(source, device_id="device-1", fps=10)
    service = DesktopCamService(recorder)

    start = service.start_desktopcam(max_frames=3)
    assert start.state == DesktopCamState.running

    stop = service.stop_desktopcam()
    assert stop.state == DesktopCamState.stopped
    assert stop.frame_count == 3

    assert service.verify_event_chain() is True
    bundle = service.export_forensic_bundle()
    assert bundle.chain_valid is True
    assert len(bundle.events) == 3
    assert len(bundle.frames) == 3


def test_desktopcam_detects_tampered_chain():
    source = _StaticFrameSource([b"f-a", b"f-b"])
    recorder = DesktopCamRecorder(source, device_id="device-2", fps=10)

    start_desktopcam(recorder, max_frames=2)
    stop_desktopcam(recorder)

    # Tamper with an event hash to simulate forensic break.
    recorder.events[1] = recorder.events[1].__class__(
        event_id=recorder.events[1].event_id,
        timestamp_uuid7=recorder.events[1].timestamp_uuid7,
        blake3_hash=recorder.events[1].blake3_hash,
        frame_id=recorder.events[1].frame_id,
        previous_event_hash=recorder.events[1].previous_event_hash,
        event_hash="0" * len(recorder.events[1].event_hash),
        created_at=recorder.events[1].created_at,
    )

    assert verify_event_chain(recorder) is False
    assert recorder.recover_partial_sequences() == 1
