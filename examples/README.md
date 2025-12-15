# Examples Directory

This directory contains example files and documentation for understanding the Yandex.Disk API metadata structure.

## Files

- **`metadata_example.json`**: A real-world example of metadata returned by the Yandex.Disk Public API for a directory resource containing 7 PDF files. This metadata was extracted from https://disk.yandex.ru/d/4Z0GsDwfR4gkPA

- **`METADATA_STRUCTURE.md`**: Comprehensive documentation describing the structure of the metadata JSON response, including all fields, their types, descriptions, and usage examples.

## Usage

These examples are useful for:

1. **Understanding the API**: See what data is available from Yandex.Disk public resources
2. **Development**: Reference when working with metadata in ydiskarc or other tools
3. **Testing**: Use as test data for parsing and processing metadata
4. **Documentation**: Reference for understanding what fields are available and how to use them

## Extracting Metadata

To extract metadata from a Yandex.Disk public resource, use:

```bash
# Extract metadata only (no file downloads)
ydiskarc sync https://disk.yandex.ru/d/RESOURCE_ID --nofiles

# Or extract metadata along with files
ydiskarc sync https://disk.yandex.ru/d/RESOURCE_ID --metadata
```

The metadata will be saved as `_metadata.json` in each directory.

## Example Resource

The example metadata comes from:
- **URL**: https://disk.yandex.ru/d/4Z0GsDwfR4gkPA
- **Name**: "Примеры" (Examples)
- **Type**: Directory
- **Contents**: 7 PDF files (Avia.pdf, Ecology.pdf, Education.pdf, Finance.pdf, Heath.pdf, Law.pdf, Oil.pdf)
