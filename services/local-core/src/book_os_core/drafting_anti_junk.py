from __future__ import annotations

from pathlib import Path

from .anti_junk import AntiJunkService
from .drafting import DraftingService
from .model_gateway import ModelGateway
from .model_gateway_anti_junk import AntiJunkModelGateway


def install_drafting_anti_junk_extension() -> None:
    if getattr(DraftingService, "_anti_junk_extension_installed", False):
        return

    original_init = DraftingService.__init__

    def init(self: DraftingService, data_dir: Path, gateway: ModelGateway) -> None:
        original_init(self, data_dir, AntiJunkModelGateway(gateway, AntiJunkService(data_dir)))

    DraftingService.__init__ = init
    DraftingService._anti_junk_extension_installed = True


install_drafting_anti_junk_extension()
