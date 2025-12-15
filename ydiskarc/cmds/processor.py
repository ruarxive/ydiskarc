import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Dict, Optional

import requests
import yaml
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from ..config import config

# Use config values
YD_API = config.api_resources_url
YD_API_DOWNLOAD = config.api_download_url
REQUEST_HEADER: Dict[str, str] = {"User-Agent": config.user_agent or ""}
DEFAULT_CHUNK_SIZE = config.chunk_size


def validate_yandex_url(url: str) -> bool:
    """Validate Yandex.Disk public resource URL.

    Args:
        url: URL to validate

    Returns:
        bool: True if URL is a valid Yandex.Disk public resource URL, False otherwise
    """
    patterns = [
        r"https://disk\.yandex\.ru/d/[A-Za-z0-9_-]+",
        r"https://disk\.yandex\.ru/i/[A-Za-z0-9_-]+",
        r"https://disk\.yandex\.com/d/[A-Za-z0-9_-]+",  # Alternative domain
        r"https://disk\.yandex\.com/i/[A-Za-z0-9_-]+",  # Alternative domain
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def create_session_with_retries() -> requests.Session:
    """Create a requests session with retry logic and rate limiting handling.

    Returns:
        requests.Session: Configured session with retry adapter
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=config.max_retries,
        backoff_factor=config.retry_backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(REQUEST_HEADER)
    return session


def handle_rate_limit(resp: requests.Response, verbose: bool = False) -> None:
    """Handle rate limiting by waiting for the specified time.

    Args:
        resp: Response object that may contain rate limit information
        verbose: Whether to show log messages
    """
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        if verbose:
            logging.warning(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)


def get_file(
    url: str,
    filepath: Optional[str] = None,
    filename: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    aria2: bool = False,
    aria2path: Optional[str] = None,
    makedirs: bool = True,
    filesize: Optional[int] = None,
    resume: bool = True,
    verbose: bool = False,
) -> None:
    """Download a file from a URL with progress tracking and resume support.

    Args:
        url: The URL to download from
        filepath: Optional directory to save the file
        filename: Optional filename (auto-detected if not provided)
        params: Optional query parameters for the request
        aria2: Whether to use aria2 for downloading
        aria2path: Path to aria2 executable
        makedirs: Whether to create directories if needed
        filesize: Expected file size for progress tracking
        resume: Whether to resume interrupted downloads (default: True)

    Raises:
        requests.RequestException: If download fails
        IOError: If file write fails
        ValueError: If aria2 is requested but aria2path is not provided
    """
    session = create_session_with_retries()

    # Make initial request to determine filename and check for resume
    headers: Dict[str, str] = {}
    try:
        if params:
            page = session.get(
                url,
                params=params,
                headers=headers,
                stream=True,
                verify=True,
                timeout=config.timeout,
            )
        else:
            page = session.get(
                url, headers=headers, stream=True, verify=True, timeout=config.timeout
            )

        # Handle rate limiting
        if page.status_code == 429:
            handle_rate_limit(page, verbose)
            # Retry the request after waiting
            if params:
                page = session.get(
                    url,
                    params=params,
                    headers=headers,
                    stream=True,
                    verify=True,
                    timeout=config.timeout,
                )
            else:
                page = session.get(
                    url, headers=headers, stream=True, verify=True, timeout=config.timeout
                )

        page.raise_for_status()  # Raise exception for bad status codes
    except requests.exceptions.RequestException as e:
        if verbose:
            logging.error(f"Failed to download file from {url}: {e}")
        raise

    # Determine filename
    if filename is None:
        if "Content-Disposition" in page.headers.keys():
            try:
                fname = (
                    re.findall("filename=(.+)", page.headers["Content-Disposition"])[0]
                    .strip('"')
                    .encode("latin-1")
                    .decode("utf-8")
                )
            except (IndexError, UnicodeDecodeError) as e:
                if verbose:
                    logging.warning(f"Failed to parse Content-Disposition header: {e}")
                fname = url.split("/")[-1]
        else:
            fname = url.split("/")[-1]
        if filepath:
            filename = os.path.join(filepath, fname)
        else:
            filename = fname
    elif filepath is not None:
        filename = os.path.join(filepath, filename)

    # Check for existing file for resume
    existing_size = 0
    if resume and filename and os.path.exists(filename):
        existing_size = os.path.getsize(filename)
        # If file exists and we want to resume, close current connection
        # and restart with Range header
        page.close()
        headers["Range"] = f"bytes={existing_size}-"
        if verbose:
            logging.info(f"Resuming download from byte {existing_size}")

        # Make new request with Range header
        try:
            if params:
                page = session.get(
                    url,
                    params=params,
                    headers=headers,
                    stream=True,
                    verify=True,
                    timeout=config.timeout,
                )
            else:
                page = session.get(
                    url, headers=headers, stream=True, verify=True, timeout=config.timeout
                )

            if page.status_code == 429:
                handle_rate_limit(page, verbose)
                if params:
                    page = session.get(
                        url,
                        params=params,
                        headers=headers,
                        stream=True,
                        verify=True,
                        timeout=config.timeout,
                    )
                else:
                    page = session.get(
                        url, headers=headers, stream=True, verify=True, timeout=config.timeout
                    )

            page.raise_for_status()
        except requests.exceptions.RequestException as e:
            if verbose:
                logging.error(f"Failed to resume download from {url}: {e}")
            raise

    # Create directory if needed
    if makedirs and filepath:
        try:
            os.makedirs(filepath, exist_ok=True)
        except OSError as e:
            if verbose:
                logging.error(f"Failed to create directory {filepath}: {e}")
            raise

    if not aria2:
        # Use progress bar if filesize is known
        remaining = (
            filesize - existing_size
            if existing_size > 0 and filesize is not None
            else (filesize if filesize is not None else None)
        )
        desc = "Downloading" + (" (resuming)" if existing_size > 0 else "")

        if verbose:
            msg = (
                "Retrieving file from %s" % (url)
                if filesize is None
                else "Retrieving file from %s with size %d" % (url, filesize)
            )
            if existing_size > 0:
                msg += f" (resuming from {existing_size} bytes)"
            logging.info(msg)

        try:
            mode = "ab" if existing_size > 0 and resume else "wb"
            with open(filename, mode) as f:
                total = existing_size
                chunk = 0
                # Always show progress bar when filesize is known, regardless of verbose mode
                with tqdm(
                    total=remaining, desc=desc, unit="B", unit_scale=True, disable=filesize is None
                ) as pbar:
                    for line in page.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                        chunk += 1
                        if line:
                            f.write(line)
                        total += len(line)
                        if filesize is not None:
                            pbar.update(len(line))
                        if verbose and chunk % 1000 == 0:
                            logging.info("File %s to size %d" % (filename, total))
                if verbose:
                    logging.info(f"Successfully downloaded {filename} ({total} bytes)")
        except IOError as e:
            if verbose:
                logging.error(f"Failed to write file {filename}: {e}")
            raise
    else:
        # Use aria2 for downloading
        if aria2path is None:
            raise ValueError("aria2path must be provided when using aria2")

        dirpath = os.path.dirname(filename)
        basename = os.path.basename(filename)

        try:
            if len(dirpath) > 0:
                subprocess.run(
                    [aria2path, "--retry-wait=10", "-d", dirpath, "--out", basename, url],
                    check=True,
                    timeout=3600,  # 1 hour timeout
                )
            else:
                subprocess.run(
                    [aria2path, "--retry-wait=10", "--out", basename, url], check=True, timeout=3600
                )
            if verbose:
                logging.info(f"Successfully downloaded {filename} using aria2")
        except subprocess.CalledProcessError as e:
            if verbose:
                logging.error(f"aria2 download failed: {e}")
            raise
        except FileNotFoundError:
            if verbose:
                logging.error(f"aria2 executable not found at {aria2path}")
            raise


def yd_get_full(
    url: str, output: Optional[str], filename: Optional[str], metadata: bool, verbose: bool = False
) -> None:
    """Download a full resource (file or directory) from Yandex.Disk.

    Args:
        url: Public resource URL
        output: Output directory
        filename: Optional output filename
        metadata: Whether to save metadata

    Raises:
        requests.RequestException: If API request fails
        ValueError: If URL is invalid or download link not found
        IOError: If file operations fail
    """
    try:
        if output:
            os.makedirs(output, exist_ok=True)
    except OSError as e:
        if verbose:
            logging.error(f"Failed to create output directory {output}: {e}")
        raise

    session = create_session_with_retries()

    # Fetch metadata to determine if it's a file or directory and get statistics
    metadata_data = None
    try:
        resp = session.get(YD_API, params={"public_key": url}, timeout=config.timeout)
        if resp.status_code == 429:
            handle_rate_limit(resp, verbose)
            resp = session.get(YD_API, params={"public_key": url}, timeout=config.timeout)
        resp.raise_for_status()
        try:
            metadata_data: Optional[Dict[str, Any]] = resp.json()  # type: ignore[assignment]
        except json.JSONDecodeError:
            pass  # If JSON parsing fails, continue without metadata

        # Save metadata if requested
        if metadata and output:
            metadata_file = os.path.join(output, "_metadata.json")
            try:
                with open(metadata_file, "w", encoding="utf8") as f:
                    f.write(resp.text)
                if verbose:
                    logging.info(f"Metadata saved to {metadata_file}")
            except IOError as e:
                if verbose:
                    logging.error(f"Failed to write metadata file {metadata_file}: {e}")
                raise
    except requests.exceptions.RequestException as e:
        if verbose:
            logging.error(f"Failed to fetch metadata: {e}")
        raise

    id = url.rsplit("/", 1)[-1]
    if output is None:
        output = id

    # Use "dump.zip" as default filename if not specified
    if filename is None:
        filename = "dump.zip"

    # Determine if resource is a directory or file and display statistics
    # Note: "full" command always downloads 1 file
    # (either the file itself or a ZIP of the directory)
    if metadata_data:
        resource_type = metadata_data.get("type", "file")

        if resource_type == "dir":
            # It's a directory - will be downloaded as a ZIP file
            # Scan to get total files count and total size for information
            try:
                file_count, total_size = scan_directory_for_stats(
                    url, "", output, update=False, nofiles=False, verbose=verbose
                )
                size_str = format_size(total_size) if total_size > 0 else "0 B"
                print(f"Total files to download: 1 (ZIP archive containing {file_count} file(s))")
                print(f"Total size: {size_str}")
            except Exception as e:
                if verbose:
                    logging.warning(f"Failed to scan directory for stats: {e}")
                print("Total files to download: 1 (ZIP archive)")
                print("Total size: unknown")
        else:
            # It's a single file
            filesize = metadata_data.get("size")
            if filesize is not None:
                size_str = format_size(filesize)
                print("Total files to download: 1")
                print(f"Total size: {size_str}")
            else:
                print("Total files to download: 1")
                print("Total size: unknown")

    # Get download link
    try:
        resp = session.get(YD_API_DOWNLOAD, params={"public_key": url}, timeout=config.timeout)
        if resp.status_code == 429:
            handle_rate_limit(resp, verbose)
            resp = session.get(YD_API_DOWNLOAD, params={"public_key": url}, timeout=config.timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        if verbose:
            logging.error(f"Failed to get download link: {e}")
        raise
    except json.JSONDecodeError as e:
        if verbose:
            logging.error(f"Invalid JSON response: {e}")
        raise ValueError(f"Invalid response from API: {e}")

    if "href" in data.keys():
        # Try to get file size from download link response or metadata
        filesize = None
        if "size" in data.keys():
            filesize = data["size"]
        elif metadata_data and "size" in metadata_data.keys():
            filesize = metadata_data["size"]

        get_file(
            data["href"], filepath=output, filename=filename, filesize=filesize, verbose=verbose
        )
    else:
        error_msg = (
            f"No download URL found for {url}. "
            "Please verify that the URL is correct and the resource is publicly accessible."
        )
        if verbose:
            logging.error(error_msg)
        raise ValueError(error_msg)


def scan_directory_for_stats(
    url: str,
    path: str,
    output: str,
    update: bool = True,
    nofiles: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    """Scan directory structure to count files and calculate total size.

    Args:
        url: Public resource URL
        path: Path within the resource
        output: Output directory
        update: Whether to skip existing files
        nofiles: If True, only count metadata, not files
        verbose: Whether to show log messages

    Returns:
        tuple: (file_count, total_size_in_bytes)

    Raises:
        requests.RequestException: If API request fails
    """
    session = create_session_with_retries()
    file_count = 0
    total_size = 0

    try:
        resp = session.get(
            YD_API, params={"public_key": url, "path": path, "limit": 1000}, timeout=config.timeout
        )
        if resp.status_code == 429:
            handle_rate_limit(resp, verbose)
            resp = session.get(
                YD_API,
                params={"public_key": url, "path": path, "limit": 1000},
                timeout=config.timeout,
            )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        if verbose:
            logging.error(f"Failed to fetch directory metadata for {path}: {e}")
        raise

    try:
        data: Dict[str, Any] = resp.json()  # type: ignore[assignment]
    except json.JSONDecodeError as e:
        if verbose:
            logging.error(f"Invalid JSON response: {e}")
        raise ValueError(f"Invalid response from API: {e}")

    if "_embedded" in data.keys() and "items" in data["_embedded"]:
        for row in data["_embedded"]["items"]:
            if "path" not in row.keys():
                continue

            if row["type"] == "dir":
                # Recursively scan subdirectories
                try:
                    sub_count, sub_size = scan_directory_for_stats(
                        url, row["path"], output, update, nofiles, verbose
                    )
                    file_count += sub_count
                    total_size += sub_size
                except Exception as e:
                    if verbose:
                        logging.error(f"Failed to scan subdirectory {row['path']}: {e}")
                    continue

            elif row["type"] == "file":
                if nofiles:
                    continue

                # Check if file exists and should be skipped
                arr = [
                    output,
                ]
                arr.extend([i.rstrip() for i in row["path"].split("/") if i.strip()])
                file_path = os.path.join(*arr[:-1])
                file_name = arr[-1]
                full_file_path = os.path.join(file_path, file_name)

                if os.path.exists(full_file_path) and update:
                    continue  # Skip existing files

                file_count += 1
                if "size" in row and row["size"] is not None:
                    total_size += row["size"]

    return file_count, total_size


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string
    """
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def yd_get_and_store_dir(
    url: str,
    path: str,
    output: str,
    update: bool = True,
    nofiles: bool = False,
    iterative: bool = False,
    verbose: bool = False,
) -> Optional[Dict[str, Any]]:
    """Get and store directory contents from Yandex.Disk.

    Args:
        url: Public resource URL
        path: Path within the resource
        output: Output directory
        update: Whether to update existing files
        nofiles: If True, only save metadata, not files
        iterative: If True, recursively process subdirectories

    Returns:
        dict: JSON response data if not iterative, None otherwise

    Raises:
        requests.RequestException: If API request fails
        IOError: If file operations fail
    """
    session = create_session_with_retries()
    try:
        resp = session.get(
            YD_API, params={"public_key": url, "path": path, "limit": 1000}, timeout=config.timeout
        )
        if resp.status_code == 429:
            handle_rate_limit(resp, verbose)
            resp = session.get(
                YD_API,
                params={"public_key": url, "path": path, "limit": 1000},
                timeout=config.timeout,
            )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        if verbose:
            logging.error(f"Failed to fetch directory metadata for {path}: {e}")
        raise

    try:
        data: Dict[str, Any] = resp.json()  # type: ignore[assignment]
    except json.JSONDecodeError as e:
        if verbose:
            logging.error(f"Invalid JSON response: {e}")
        raise ValueError(f"Invalid response from API: {e}")

    # Create output directory structure
    arr = [
        output,
    ]
    arr.extend([i.rstrip() for i in path.split("/") if i.strip()])
    dir_path = os.path.join(*arr)

    try:
        os.makedirs(dir_path, exist_ok=True)
    except OSError as e:
        if verbose:
            logging.error(f"Failed to create directory {dir_path}: {e}")
        raise

    # Save metadata
    metadata_file = os.path.join(dir_path, "_metadata.json")
    if verbose:
        logging.info(f"Saving metadata of {dir_path}")
    try:
        with open(metadata_file, "w", encoding="utf8") as f:
            f.write(resp.text)
    except IOError as e:
        if verbose:
            logging.error(f"Failed to write metadata file {metadata_file}: {e}")
        raise

    if not iterative:
        return data
    else:
        if "_embedded" in data.keys() and "items" in data["_embedded"]:
            for row in data["_embedded"]["items"]:
                if "path" not in row.keys():
                    continue

                if row["type"] == "dir":
                    arr = [
                        output,
                    ]
                    arr.extend([i.rstrip() for i in path.split("/") if i.strip()])
                    row_path = os.path.join(*arr)
                    try:
                        os.makedirs(row_path, exist_ok=True)
                    except OSError as e:
                        logging.error(f"Failed to create directory {row_path}: {e}")
                        continue

                    if iterative:
                        try:
                            yd_get_and_store_dir(
                                url,
                                row["path"],
                                output,
                                update,
                                nofiles,
                                iterative=iterative,
                                verbose=verbose,
                            )
                        except Exception as e:
                            if verbose:
                                logging.error(f"Failed to process subdirectory {row['path']}: {e}")
                            continue

                elif row["type"] == "file":
                    if nofiles:
                        continue

                    arr = [
                        output,
                    ]
                    arr.extend([i.rstrip() for i in row["path"].split("/") if i.strip()])
                    file_path = os.path.join(*arr[:-1])
                    file_name = arr[-1]
                    full_file_path = os.path.join(file_path, file_name)

                    # Check if file exists and should be skipped
                    if os.path.exists(full_file_path) and update:
                        if verbose:
                            logging.info("Already stored %s" % (row["path"]))
                        continue

                    try:
                        get_file(
                            row["file"],
                            file_path,
                            filename=file_name,
                            filesize=row.get("size"),
                            verbose=verbose,
                        )
                        if verbose:
                            logging.info("Saved %s" % (row["path"]))
                    except Exception as e:
                        if verbose:
                            logging.error(f"Failed to download file {row['path']}: {e}")
                        continue

        return None


class Project:
    """Disk files extractor. Yandex.Disk only right now"""

    def __init__(self) -> None:
        pass

    def configure(self, key: str, projectdir: Optional[str] = None) -> None:
        """Configure Yandex OAuth key.

        Args:
            key: Yandex OAuth key
            projectdir: Directory to save configuration (defaults to current directory)

        Raises:
            IOError: If configuration file cannot be read or written
            yaml.YAMLError: If configuration file is invalid YAML
        """
        if projectdir is None:
            projectdir = os.getcwd()
        filepath = os.path.join(projectdir, ".ydiskarc")

        conf = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf8") as f:
                    conf = yaml.safe_load(f)  # SECURITY FIX: Use safe_load instead of load
                    if conf is None:
                        conf = {}
            except IOError as e:
                logging.error(f"Failed to read configuration file {filepath}: {e}")
                raise
            except yaml.YAMLError as e:
                logging.error(f"Invalid YAML in configuration file {filepath}: {e}")
                raise

        if "keys" not in conf.keys():
            conf["keys"] = {}
        conf["keys"]["yandex_oauth"] = key

        try:
            with open(filepath, "w", encoding="utf8") as f:
                yaml.safe_dump(conf, f)
            logging.info(f"Configuration saved at {filepath}")
        except IOError as e:
            logging.error(f"Failed to write configuration file {filepath}: {e}")
            raise

    def __store(
        self,
        url: str,
        metapath: str,
        update: bool = False,
        nofiles: bool = False,
        verbose: bool = False,
    ) -> None:
        """Store resource from URL.

        Args:
            url: Public resource URL
            metapath: Path to store metadata and files
            update: Whether to update existing files
            nofiles: If True, only save metadata
            verbose: Whether to show log messages

        Raises:
            requests.RequestException: If API request fails
            IOError: If file operations fail
        """
        path = ""
        if verbose:
            logging.info("Saving %s" % (url))
        try:
            os.makedirs(metapath, exist_ok=True)
        except OSError as e:
            if verbose:
                logging.error(f"Failed to create directory {metapath}: {e}")
            raise

        # Scan directory structure to get file count and total size before downloading
        if not nofiles:
            try:
                file_count, total_size = scan_directory_for_stats(
                    url, path, metapath, update, nofiles, verbose
                )
                if file_count > 0:
                    size_str = format_size(total_size)
                    print(f"Total files to download: {file_count}")
                    print(f"Total size: {size_str}")
                elif update:
                    print("All files are already up to date.")
                    return
                else:
                    print("No files found to download.")
                    return
            except Exception as e:
                if verbose:
                    logging.warning(f"Failed to scan directory for stats: {e}")
                # Continue with download even if scanning fails

        yd_get_and_store_dir(
            url, path, metapath, update=update, nofiles=nofiles, iterative=True, verbose=verbose
        )

    def sync(
        self,
        url: str,
        output: str,
        update: bool = False,
        nofiles: bool = False,
        verbose: bool = False,
    ) -> None:
        self.__store(url, output, update, nofiles, verbose)

    def full(
        self,
        url: str,
        output: Optional[str],
        filename: Optional[str],
        metadata: bool,
        verbose: bool = False,
    ) -> None:
        yd_get_full(url, output, filename, metadata, verbose)
