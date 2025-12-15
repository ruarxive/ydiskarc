# ydiskarc

ydiskarc (pronounced *Ai-disk-arc*) is a command line tool used to backup Yandex.Disk public resources.
Public resources are only shared files and folders from Yandex.Disk service.
Yandex provides free-to-use API that allow to download the data.

## Main features

* **Metadata extraction** - Automatically saves metadata as `_metadata.json` files
* **Download any public resource** - Files or entire directories
* **Resume support** - Automatically resumes interrupted downloads
* **Retry logic** - Handles transient network failures automatically
* **Rate limiting handling** - Respects API rate limits
* **Progress tracking** - Visual progress bars for downloads using tqdm
* **Pre-download statistics** - Shows total file count and estimated size before downloading
* **Quiet by default** - Logs only appear when verbose mode is enabled
* **Update mode** - Only download files that don't already exist locally

## Installation

### Any OS

A universal installation method (that works on Windows, Mac OS X, Linux, …,
and always provides the latest version) is to use pip:

```bash
# Make sure we have an up-to-date version of pip and setuptools:
$ pip install --upgrade pip setuptools

$ pip install --upgrade ydiskarc
```

(If ``pip`` installation fails for some reason, you can try
``easy_install ydiskarc`` as a fallback.)

### Python version

Python version 3.6 or greater is required.

## Usage

Synopsis:

```bash
$ ydiskarc [command] [URL] [flags]
```

**Examples:**
```bash
# Sync command - URL is a positional argument
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o output

# Full command - URL is a positional argument  
$ ydiskarc full https://disk.yandex.ru/i/XYZ789 -o output
```

See also ``python -m ydiskarc`` and ``ydiskarc [command] --help`` for help for each command.

## Commands

### Sync command

Synchronizes files and metadata from public resource of directory type to the local directory.
Maintains directory structure and saves metadata for each directory level.

**Basic usage:**
```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle
```

**Update mode (only download new files):**
```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle --update
```

**Metadata only (no file downloads):**
```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle --nofiles
```

**Options:**
- `URL` - Public resource URL (required, positional argument)
- `--output`, `-o` - Output directory (defaults to resource ID)
- `--update` - Update mode: only download files that don't exist locally
- `--nofiles`, `-n` - Metadata-only mode: save metadata without downloading files
- `--verbose`, `-v` - Enable verbose logging (logs are hidden by default)

**Note:** The command now displays total file count and estimated size before starting downloads.

### Full command

Downloads single file or directory. Single files are downloaded with their original format.
Directories are downloaded as ZIP files containing all files inside.

**Basic usage:**
```bash
$ ydiskarc full https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files
```

**With metadata:**
```bash
$ ydiskarc full https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files -m
```

**Verbose output:**
```bash
$ ydiskarc full https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files -v -m
```

**Options:**
- `URL` - Public resource URL (required, positional argument)
- `--output`, `-o` - Output directory
- `--filename`, `-f` - Output filename (defaults to `dump.zip` if not specified)
- `--metadata`, `-m` - Extract and save metadata as `_metadata.json`
- `--verbose`, `-v` - Enable verbose logging (logs are hidden by default)

**Note:** 
- Single files are downloaded with their original format
- Directories are downloaded as ZIP files (default filename: `dump.zip`)
- The command displays file count and size information before downloading

### Version command

Check the installed version:
```bash
$ ydiskarc version
```

## Configuration

ydiskarc can be configured using a `.ydiskarc` YAML file in your project directory.

**Example configuration:**
```yaml
keys:
  yandex_oauth: your_oauth_key_here
```

To configure:
```bash
$ ydiskarc configure --key YOUR_OAUTH_KEY
```

## Troubleshooting

### Common Issues

**"No download url. Probably wrong public url/key?"**
- Verify the URL is correct and the resource is publicly accessible
- Check that the URL format matches: `https://disk.yandex.ru/d/...` or `https://disk.yandex.ru/i/...`

**"Failed to download file" or network errors**
- Check your internet connection
- The tool automatically retries on transient failures
- For rate limiting, the tool will wait and retry automatically

**"Failed to create directory"**
- Check file system permissions
- Ensure you have write access to the output directory

**Resume interrupted downloads**
- Downloads automatically resume if interrupted
- Partial files are detected and resumed from the last byte

### Verbose Mode

By default, ydiskarc runs quietly and only shows progress bars and essential information. For detailed debugging information, use the `--verbose` or `-v` flag:
```bash
$ ydiskarc sync https://disk.yandex.ru/d/... -o output -v
```

When verbose mode is enabled, you'll see:
- Detailed logging of all operations
- File-by-file download progress
- API request details
- Error stack traces

## Examples

**Download a public folder:**
```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o my_backup
```

**Download a single file with metadata:**
```bash
$ ydiskarc full https://disk.yandex.ru/i/XYZ789 -o downloads -m
```

**Update existing backup (skip existing files):**
```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o my_backup --update
```

**Get metadata only:**
```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o metadata_only --nofiles
```

**Example output:**
```
Total files to download: 7
Total size: 10.12 MB
Downloading: 100%|████████████| 1.72M/1.72M [00:05<00:00, 345KB/s]
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Follow code style** - the project uses:
   - Black for formatting (line length: 100)
   - flake8 and ruff for linting
   - isort for import sorting
   - Type hints for better code clarity
   - All code must pass linting checks before submission
4. **Run tests** before submitting:
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```
5. **Run linting** to ensure code quality:
   ```bash
   black ydiskarc/
   isort ydiskarc/
   flake8 ydiskarc/
   ruff check ydiskarc/
   ```
6. **Install pre-commit hooks** (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```
7. **Submit a pull request** with a clear description

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ruarxive/ydiskarc.git
cd ydiskarc

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 ydiskarc/
ruff check ydiskarc/
black --check ydiskarc/
isort --check-only ydiskarc/
```

## Metadata Documentation

For detailed information about the Yandex.Disk API metadata structure, see:
- [Examples Directory](examples/) - Contains example metadata file and documentation
- [Metadata Structure Documentation](examples/METADATA_STRUCTURE.md) - Complete reference of metadata fields

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/ruarxive/ydiskarc/
- **Issues**: https://github.com/ruarxive/ydiskarc/issues
- **Yandex.Disk API**: https://yandex.com/dev/disk/api/
