import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import yaml

from ydiskarc import constants
from ydiskarc.client import YandexDiskClient
from ydiskarc.downloader import ResourceDownloader, format_size


class PathTraversalError(ValueError):
    """Raised when an API-supplied path would resolve outside the user's
    output directory."""


__all__ = ["PathTraversalError", "Project", "safe_join"]


def safe_join(base: str, *parts: str) -> str:
    """Join ``base`` with the supplied path parts and ensure the result stays
    within ``base``.

    Each part is split on ``/`` and ``\\``, leading/trailing whitespace is
    stripped, and empty or ``.`` segments are dropped. ``..`` segments and
    drive letters raise :class:`PathTraversalError`. The joined path is
    resolved with :func:`os.path.realpath` against a realpathed ``base``;
    a final containment check via :func:`os.path.commonpath` ensures the
    result lives under ``base`` even in the presence of symlinks.

    Args:
        base: The output directory chosen by the user.
        *parts: Path components, typically derived from the Yandex.Disk API's
            ``path`` field for an embedded item.

    Returns:
        An absolute, normalized path guaranteed to live under ``base``.

    Raises:
        PathTraversalError: If the resulting path would resolve outside
            ``base`` (e.g. parts containing ``..`` or drive letters).
    """
    if base is None or base == "":
        raise PathTraversalError("base directory is empty")

    base_abs = os.path.realpath(base)

    cleaned: list[str] = []
    for part in parts:
        if part is None:
            continue
        # Normalize separators and strip whitespace from each sub-segment.
        # The Yandex API returns paths like "/SubDir/file.pdf" — a leading
        # slash is just a separator, not an absolute path.
        normalized = str(part).strip().replace("\\", "/")
        for sub in normalized.split("/"):
            if not sub or sub == ".":
                continue
            if sub == "..":
                raise PathTraversalError(f"traversal segment rejected: {part!r}")
            # Windows drive letter ("C:") would let a path escape the
            # base directory on Windows hosts.
            if len(sub) == 2 and sub[1] == ":" and sub[0].isalpha():
                raise PathTraversalError(f"drive letter rejected: {part!r}")
            cleaned.append(sub)

    candidate = os.path.realpath(os.path.join(base_abs, *cleaned))
    # Containment check using realpath so symlinks at the boundary are honored.
    try:
        common = os.path.commonpath([base_abs, candidate])
    except ValueError:
        # commonpath raises on different drives (Windows).
        raise PathTraversalError(
            f"path resolves outside base: {candidate!r} not under {base_abs!r}"
        )

    if common != base_abs:
        raise PathTraversalError(f"path traversal detected: {candidate!r} escapes {base_abs!r}")

    return candidate


def _yd_get_full(
    url: str, output: Optional[str], filename: Optional[str], metadata: bool, verbose: bool = False
) -> None:
    client = YandexDiskClient(verbose=verbose)
    downloader = ResourceDownloader(client, verbose=verbose)

    if output:
        os.makedirs(output, exist_ok=True)

    try:
        resp = client.get_resource_metadata(url)
        metadata_data = resp.json()

        if metadata and output:
            metadata_file = os.path.join(output, constants.METADATA_FILENAME)
            with open(metadata_file, "w", encoding="utf8") as f:
                f.write(resp.text)
            if verbose:
                logging.info(f"Metadata saved to {metadata_file}")
    except Exception as e:
        if verbose:
            logging.error(f"Failed to fetch metadata: {e}")
        # Proceed without metadata
        metadata_data = None

    resource_id = url.rsplit("/", 1)[-1]
    if output is None:
        output = resource_id

    if filename is None:
        filename = constants.DEFAULT_FULL_FILENAME

    resource_type = (
        metadata_data.get(constants.JSON_TYPE, constants.JSON_TYPE_FILE)
        if metadata_data
        else constants.JSON_TYPE_FILE
    )
    filesize = metadata_data.get(constants.JSON_SIZE) if metadata_data else None
    direct_file_url = metadata_data.get(constants.JSON_FILE) if metadata_data else None

    if resource_type == constants.JSON_TYPE_DIR:
        try:
            file_count, total_size = _scan_directory_for_stats(
                url, "", output, update=False, nofiles=False, verbose=verbose
            )
            size_str = format_size(total_size) if total_size > 0 else "0 B"
            print(f"Total files to download: 1 (ZIP archive containing {file_count} file(s))")
            print(f"Total size: {size_str}")
        except Exception:
            print("Total files to download: 1 (ZIP archive)")
            print("Total size: unknown")
    else:
        if filesize is not None:
            print("Total files to download: 1")
            print(f"Total size: {format_size(filesize)}")
        else:
            print("Total files to download: 1")
            print("Total size: unknown")

    try:
        # Skip the second API call if we already have a direct download URL
        # from the metadata response. This is the case for single-file
        # resources where the listing endpoint returns the `file` field.
        if resource_type == constants.JSON_TYPE_FILE and direct_file_url:
            download_url = direct_file_url
        else:
            download_url = client.get_download_link(url)
        downloader.get_file(download_url, filepath=output, filename=filename, filesize=filesize)
    except Exception as e:
        if verbose:
            logging.error(f"Failed to get file: {e}")
        raise ValueError(f"Failed to download resource: {e}")


def _scan_directory_for_stats(
    url: str,
    path: str,
    output: str,
    update: bool = True,
    nofiles: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    client = YandexDiskClient(verbose=verbose)
    file_count = 0
    total_size = 0

    resp = client.get_resource_metadata(url, path=path, limit=constants.DEFAULT_API_LIST_LIMIT)
    data = resp.json()

    embedded = data.get(constants.JSON_EMBEDDED)
    if embedded and constants.JSON_ITEMS in embedded:
        for row in embedded[constants.JSON_ITEMS]:
            if constants.JSON_PATH not in row:
                continue

            if row[constants.JSON_TYPE] == constants.JSON_TYPE_DIR:
                try:
                    sub_count, sub_size = _scan_directory_for_stats(
                        url, row[constants.JSON_PATH], output, update, nofiles, verbose
                    )
                    file_count += sub_count
                    total_size += sub_size
                except Exception as e:
                    if verbose:
                        logging.error(
                            f"Failed to scan subdirectory {row[constants.JSON_PATH]}: {e}"
                        )
            elif row[constants.JSON_TYPE] == constants.JSON_TYPE_FILE:
                if nofiles:
                    continue

                try:
                    full_file_path = safe_join(output, *row[constants.JSON_PATH].split("/"))
                except PathTraversalError as e:
                    if verbose:
                        logging.error(f"Skipping unsafe path {row[constants.JSON_PATH]!r}: {e}")
                    continue

                if os.path.exists(full_file_path) and update:
                    continue

                file_count += 1
                size = row.get(constants.JSON_SIZE)
                if size is not None:
                    total_size += size

    return file_count, total_size


def _yd_get_and_store_dir(
    url: str,
    path: str,
    output: str,
    update: bool = True,
    nofiles: bool = False,
    iterative: bool = False,
    verbose: bool = False,
    parallel: int = 1,
):
    client = YandexDiskClient(verbose=verbose)
    downloader = ResourceDownloader(client, verbose=verbose)

    resp = client.get_resource_metadata(url, path=path, limit=constants.DEFAULT_API_LIST_LIMIT)
    data = resp.json()

    try:
        dir_path = safe_join(output, *path.split("/")) if path else output
    except PathTraversalError as e:
        raise PathTraversalError(f"refusing to write outside {output!r}: {e}") from e

    os.makedirs(dir_path, exist_ok=True)

    metadata_file = os.path.join(dir_path, constants.METADATA_FILENAME)
    with open(metadata_file, "w", encoding="utf8") as f:
        f.write(resp.text)

    if not iterative:
        return data

    embedded = data.get(constants.JSON_EMBEDDED)
    if not (embedded and constants.JSON_ITEMS in embedded):
        return data

    # Pre-compute file download jobs so we can dispatch them concurrently
    # when --parallel > 1.
    # Each job is (file_url, file_path, filename, filesize).
    file_jobs: list[tuple[str, str, str, Optional[int]]] = []
    subdirs: list[str] = []  # paths to recurse into
    skipped_files: list[tuple[str, PathTraversalError]] = []  # (path, error) for verbose logging

    for row in embedded[constants.JSON_ITEMS]:
        if constants.JSON_PATH not in row:
            continue

        if row[constants.JSON_TYPE] == constants.JSON_TYPE_DIR:
            subdirs.append(row[constants.JSON_PATH])

        elif row[constants.JSON_TYPE] == constants.JSON_TYPE_FILE:
            if nofiles:
                continue
            try:
                file_name = row[constants.JSON_PATH].rsplit("/", 1)[-1].strip()
                parent_parts = row[constants.JSON_PATH].rsplit("/", 1)[:-1] or [""]
                file_path = (
                    safe_join(output, *parent_parts[0].split("/")) if parent_parts[0] else output
                )
                full_file_path = safe_join(output, *row[constants.JSON_PATH].split("/"))
            except PathTraversalError as e:
                skipped_files.append((row[constants.JSON_PATH], e))
                continue

            if os.path.exists(full_file_path) and update:
                continue

            file_jobs.append(
                (
                    row[constants.JSON_FILE],
                    file_path,
                    file_name,
                    row.get(constants.JSON_SIZE),
                )
            )

    if verbose and skipped_files:
        for path_value, err in skipped_files:
            logging.error(f"Skipping unsafe file path {path_value!r}: {err}")

    # Recurse into subdirectories first (sequential — they may add their
    # own file jobs; we don't parallelise recursion itself).
    for sub_path in subdirs:
        try:
            row_path = safe_join(output, *sub_path.split("/"))
        except PathTraversalError as e:
            if verbose:
                logging.error(f"Skipping unsafe subdirectory {sub_path!r}: {e}")
            continue
        os.makedirs(row_path, exist_ok=True)
        try:
            _yd_get_and_store_dir(
                url,
                sub_path,
                output,
                update,
                nofiles,
                iterative=True,
                verbose=verbose,
                parallel=parallel,
            )
        except Exception as e:
            if verbose:
                logging.error(f"Failed to process subdirectory {sub_path}: {e}")

    # Dispatch file downloads.
    if not file_jobs:
        return data

    def _do_download(job: tuple[str, str, str, Optional[int]]) -> None:
        dl_url, dl_path, dl_name, dl_size = job
        try:
            downloader.get_file(dl_url, dl_path, filename=dl_name, filesize=dl_size)
        except Exception as e:
            if verbose:
                logging.error(f"Failed to download file {dl_name}: {e}")

    if parallel <= 1:
        for job in file_jobs:
            _do_download(job)
    else:
        with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
            list(pool.map(_do_download, file_jobs))


class Project:
    """Disk files extractor. Yandex.Disk only right now"""

    def __init__(self) -> None:
        pass

    def configure(self, key: str, projectdir: Optional[str] = None) -> None:
        if projectdir is None:
            projectdir = os.getcwd()
        filepath = os.path.join(projectdir, ".ydiskarc")

        conf: dict = {}
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf8") as f:
                conf = yaml.safe_load(f) or {}

        if "keys" not in conf:
            conf["keys"] = {}
        conf["keys"]["yandex_oauth"] = key

        with open(filepath, "w", encoding="utf8") as f:
            yaml.safe_dump(conf, f)
        # Restrict permissions on POSIX so the OAuth token is not
        # world-readable. Best-effort; ignored on Windows.
        try:
            os.chmod(filepath, 0o600)
        except OSError:
            pass
        logging.info(f"Configuration saved at {filepath}")

    def __store(
        self,
        url: str,
        metapath: str,
        update: bool = False,
        nofiles: bool = False,
        verbose: bool = False,
        parallel: int = 1,
    ) -> None:
        os.makedirs(metapath, exist_ok=True)

        if not nofiles:
            try:
                file_count, total_size = _scan_directory_for_stats(
                    url, "", metapath, update, nofiles, verbose
                )
                if file_count > 0:
                    print(f"Total files to download: {file_count}")
                    print(f"Total size: {format_size(total_size)}")
                elif update:
                    print("All files are already up to date.")
                    return
                else:
                    print("No files found to download.")
                    return
            except Exception as e:
                if verbose:
                    logging.warning(f"Failed to scan directory for stats: {e}")

        _yd_get_and_store_dir(
            url,
            "",
            metapath,
            update=update,
            nofiles=nofiles,
            iterative=True,
            verbose=verbose,
            parallel=parallel,
        )

    def sync(
        self,
        url: str,
        output: str,
        update: bool = False,
        nofiles: bool = False,
        verbose: bool = False,
        parallel: int = 1,
    ) -> None:
        self.__store(url, output, update, nofiles, verbose, parallel=parallel)

    def full(
        self,
        url: str,
        output: Optional[str],
        filename: Optional[str],
        metadata: bool,
        verbose: bool = False,
    ) -> None:
        _yd_get_full(url, output, filename, metadata, verbose)
