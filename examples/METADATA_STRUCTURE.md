# Yandex.Disk Metadata Structure Documentation

This document describes the structure of metadata returned by the Yandex.Disk Public API when accessing public resources.

## Example Source

The example metadata in `metadata_example.json` was extracted from:
- **URL**: https://disk.yandex.ru/d/4Z0GsDwfR4gkPA
- **Resource Name**: "Примеры" (Examples)
- **Type**: Directory containing 7 PDF files

## Top-Level Structure

The metadata response is a JSON object with the following top-level fields:

### Root Directory Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `path` | string | Path within the resource (root is "/") | `"/"` |
| `type` | string | Resource type: "dir" or "file" | `"dir"` |
| `name` | string | Display name of the resource | `"Примеры"` |
| `created` | string | ISO 8601 timestamp of creation | `"2022-11-25T13:54:32+00:00"` |
| `modified` | string | ISO 8601 timestamp of last modification | `"2022-11-25T13:54:32+00:00"` |
| `public_key` | string | Base64-encoded public key for the resource | `"5Yj0swSPkg/eOi1CRfXpsPOc2ImjQSxEsI9NcgvVYZq+UwZAHcNQLlgDSiytpjBkq/J6bpmRyOJonT3VoXnDag=="` |
| `public_url` | string | Public URL to access the resource | `"https://yadi.sk/d/4Z0GsDwfR4gkPA"` |
| `resource_id` | string | Unique resource identifier | `"5112124:b28990d27d4ac67e984b22bdf3f41180a07f63f57d2db6b06e78202f2f48c782"` |
| `revision` | integer | Revision number for change tracking | `1765814611261919` |
| `comment_ids` | object | Comment thread identifiers | See below |
| `exif` | object | EXIF metadata (usually empty for directories) | `{}` |
| `views_count` | integer | Number of times the resource was viewed | `5` |
| `owner` | object | Owner information | See below |
| `_embedded` | object | Embedded directory contents (only for directories) | See below |

### Comment IDs Object

```json
{
  "public_resource": "5112124:b28990d27d4ac67e984b22bdf3f41180a07f63f57d2db6b06e78202f2f48c782",
  "private_resource": "5112124:b28990d27d4ac67e984b22bdf3f41180a07f63f57d2db6b06e78202f2f48c782"
}
```

### Owner Object

```json
{
  "uid": "5112124",
  "login": "ibegtin",
  "display_name": "Иван Бегтин"
}
```

## Directory Contents (`_embedded`)

When the resource is a directory, it contains an `_embedded` object with the following structure:

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Path of the directory | `"/"` |
| `limit` | integer | Maximum number of items returned per page | `20` |
| `offset` | integer | Offset for pagination | `0` |
| `sort` | string | Sort order (empty string means default) | `""` |
| `total` | integer | Total number of items in the directory | `7` |
| `items` | array | Array of file/directory items | See below |
| `public_key` | string | Public key (same as root level) | Same as root |

## File/Directory Item Structure

Each item in the `items` array can be either a file or a directory. Common fields:

### Common Fields (Both Files and Directories)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `path` | string | Full path of the item | `"/Avia.pdf"` |
| `type` | string | Item type: "file" or "dir" | `"file"` |
| `name` | string | Display name | `"Avia.pdf"` |
| `created` | string | ISO 8601 creation timestamp | `"2022-11-25T13:55:33+00:00"` |
| `modified` | string | ISO 8601 modification timestamp | `"2022-11-25T13:55:33+00:00"` |
| `public_key` | string | Public key for the item | Same as parent |
| `resource_id` | string | Unique resource identifier | `"5112124:937b1815e5841734dfce2c0fa8c1a6444711c0d7a41aa46557b4167ff860302a"` |
| `revision` | integer | Revision number | `1669384533683085` |
| `comment_ids` | object | Comment thread identifiers | Same structure as root |

### File-Specific Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `size` | integer | File size in bytes | `1729622` |
| `mime_type` | string | MIME type of the file | `"application/pdf"` |
| `md5` | string | MD5 hash of the file | `"aba014aea0fff9d8ff042733937b1494"` |
| `sha256` | string | SHA-256 hash of the file | `"6e3c6721f21e0ff01a00c6fa13ace1e63be38bae58126e0bb4fdb459b6a4887c"` |
| `preview` | string | URL to preview image (for supported formats) | `"https://downloader.disk.yandex.ru/preview/..."` |
| `media_type` | string | Media type classification | `"document"` |
| `sizes` | array | Array of preview image sizes | See below |
| `exif` | object | EXIF metadata (usually empty for PDFs) | `{}` |
| `antivirus_status` | string | Antivirus scan status | `"clean"` |
| `file` | string | **Direct download URL** | `"https://downloader.disk.yandex.ru/disk/..."` |

### Preview Sizes Array

The `sizes` array contains objects with different preview image sizes:

```json
{
  "url": "https://downloader.disk.yandex.ru/preview/...",
  "name": "DEFAULT"  // or "XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "C"
}
```

Available size names:
- `DEFAULT` - Default preview size
- `XXXS`, `XXS`, `XS`, `S`, `M`, `L`, `XL`, `XXL`, `XXXL` - Various preview sizes
- `C` - Cropped preview

## Important Fields for Downloading

### For File Downloads

The most important field for downloading files is:
- **`file`**: Contains the direct download URL with authentication tokens. This URL can be used directly to download the file.

Example:
```json
"file": "https://downloader.disk.yandex.ru/disk/45b2417d3f1743f7e2ba6af5c7219de903f0ff321c7a2a8e1667db50419bf7c6/69407f3b/SXGR2fq28bYRgYE-I33Pb2W02lW74FPQhiN0J-hwydQaznnn35Og19qlbKHHiDlokS0DJF3DLmLu96oX3D-HHw%3D%3D?uid=0&filename=Avia.pdf&disposition=attachment&hash=&limit=0&content_type=application%2Fpdf&owner_uid=0&fsize=1729622&hid=c1b9885d540bce143c384ad219869275&media_type=document&tknv=v3&etag=aba014aea0fff9d8ff042733937b1494"
```

### For Directory Traversal

When processing directories recursively:
- Use the `path` field to construct nested paths
- Check `type` to distinguish between files (`"file"`) and directories (`"dir"`)
- For directories, recursively fetch metadata using the `path` parameter in the API request

## Usage in ydiskarc

When using the `sync` command with the `--metadata` flag, ydiskarc saves this metadata structure as `_metadata.json` in each directory. This allows you to:

1. **Track file information**: Access file sizes, checksums, and timestamps
2. **Verify downloads**: Compare MD5/SHA256 hashes to verify file integrity
3. **Resume downloads**: Use file sizes to check if downloads are complete
4. **Access previews**: Use preview URLs for thumbnails
5. **Track changes**: Use revision numbers to detect file changes

## API Endpoint

The metadata is fetched from:
```
GET https://cloud-api.yandex.net/v1/disk/public/resources
```

With query parameters:
- `public_key`: The full public URL (e.g., `https://disk.yandex.ru/d/4Z0GsDwfR4gkPA`)
- `path`: Path within the resource (use `""` or `"/"` for root)
- `limit`: Maximum number of items to return (default: 20, max: 1000)

## Notes

- All timestamps are in ISO 8601 format with timezone information
- File sizes are always in bytes
- The `file` URL contains time-limited authentication tokens
- Preview URLs are only available for supported file types (images, PDFs, etc.)
- The `public_key` field is the same for all items in a shared resource
- Directory items in the `items` array do not have `size`, `mime_type`, `md5`, `sha256`, `preview`, `sizes`, `file`, or `antivirus_status` fields
