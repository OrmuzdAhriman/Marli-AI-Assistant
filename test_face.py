import face


def test_face_noops_without_hardware(monkeypatch):
    # Force device construction to fail -> Face must degrade, not raise.
    monkeypatch.setattr(face, "_open_device", lambda *a, **k: None)
    f = face.Face()
    assert f.enabled is False
    # All methods must be safe no-ops.
    f.start()
    f.set_state("speaking")
    f.stop()


def test_set_state_validates(monkeypatch):
    monkeypatch.setattr(face, "_open_device", lambda *a, **k: None)
    f = face.Face()
    f.set_state("bogus")
    assert f.state == "idle"      # unknown falls back to idle
    f.set_state("thinking")
    assert f.state == "thinking"
