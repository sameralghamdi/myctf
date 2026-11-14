"""Maps a challenge's ``lab_kind`` to a handler instance.

Adding a new live lab = add a handler class and register it here. ``static`` and
unknown kinds have no live target (the challenge is solved without a lab, e.g. a
downloadable artifact or a pure-analysis task).
"""
from __future__ import annotations

from .bola import BolaApiLab
from .cmdinjection import CommandInjectionLab
from .crypto import EncodingLab
from .fileupload import FileUploadLab
from .httpbasics import HttpBasicsLab
from .idor import IdorBankLab
from .jwtflaw import JwtFlawLab
from .pcap import PcapLab
from .shell_scenarios import SCENARIOS
from .shelllab import ShellLab
from .sqli import SqliLoginLab
from .storedxss import StoredXssLab
from .traversal import PathTraversalLab
from .weakreset import WeakResetLab
from .xss import ReflectedXssLab

_HANDLERS = {
    h.kind: h for h in [
        HttpBasicsLab(),
        EncodingLab(),
        SqliLoginLab(),
        ReflectedXssLab(),
        IdorBankLab(),
        PathTraversalLab(),
        CommandInjectionLab(),
        StoredXssLab(),
        WeakResetLab(),
        JwtFlawLab(),
        BolaApiLab(),
        FileUploadLab(),
        PcapLab(),
        # Terminal challenges are data-driven: one handler per scenario.
        *(ShellLab(scenario) for scenario in SCENARIOS),
    ]
}


def get_handler(lab_kind: str):
    return _HANDLERS.get(lab_kind)


def is_live_lab(lab_kind: str) -> bool:
    return lab_kind in _HANDLERS


def is_shell_lab(lab_kind: str) -> bool:
    """True for labs played in the web terminal instead of an embedded page."""
    return bool(getattr(_HANDLERS.get(lab_kind), "is_shell", False))


def live_kinds() -> list[str]:
    return sorted(_HANDLERS)
