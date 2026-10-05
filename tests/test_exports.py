"""Tests for module __all__ declarations.

See openspec/changes/add-public-api-exports.
"""

import importlib
import sys


def _import_fresh(module_name: str):
    """Import a module fresh (in case earlier tests have cached it)."""
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        return sys.modules[module_name]
    return importlib.import_module(module_name)


def test_package_all_declares_metadata():
    pkg = _import_fresh("ydiskarc")
    assert hasattr(pkg, "__all__")
    assert "__version__" in pkg.__all__
    assert "__author__" in pkg.__all__
    assert "__licence__" in pkg.__all__


def test_cmds_all_exports_project():
    cmds = _import_fresh("ydiskarc.cmds")
    assert hasattr(cmds, "__all__")
    assert "Project" in cmds.__all__
    assert hasattr(cmds, "Project")


def test_client_all_exports_yandex_disk_client():
    client_mod = _import_fresh("ydiskarc.client")
    assert hasattr(client_mod, "__all__")
    assert "YandexDiskClient" in client_mod.__all__
    assert hasattr(client_mod, "YandexDiskClient")


def test_downloader_all_exports_resource_downloader_and_format_size():
    dl = _import_fresh("ydiskarc.downloader")
    assert hasattr(dl, "__all__")
    assert "ResourceDownloader" in dl.__all__
    assert "format_size" in dl.__all__
    assert hasattr(dl, "ResourceDownloader")
    assert hasattr(dl, "format_size")


def test_models_all_exports_resource_classes():
    models = _import_fresh("ydiskarc.models")
    assert hasattr(models, "__all__")
    assert "ResourceItem" in models.__all__
    assert "ResourceList" in models.__all__
    assert "ResourceInfo" in models.__all__


def test_internal_helpers_not_in_public_api():
    """Things that look internal must NOT leak via __all__."""
    client_mod = _import_fresh("ydiskarc.client")
    # _create_session_with_retries is private; __all__ should not advertise it.
    assert "_create_session_with_retries" not in client_mod.__all__

    dl = _import_fresh("ydiskarc.downloader")
    # No backdoors.
    assert "_request_with_backoff" not in dl.__all__
