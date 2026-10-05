from dataclasses import dataclass
from typing import Any, Dict, List, Optional

__all__ = ["ResourceItem", "ResourceList", "ResourceInfo"]


@dataclass
class ResourceItem:
    """Represents an item within a Yandex.Disk directory."""

    name: str
    path: str
    type: str  # "file" or "dir"
    created: Optional[str] = None
    modified: Optional[str] = None
    size: Optional[int] = None
    md5: Optional[str] = None
    sha256: Optional[str] = None
    mime_type: Optional[str] = None
    file: Optional[str] = None  # direct download URL if available

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceItem":
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            type=data.get("type", "file"),
            created=data.get("created"),
            modified=data.get("modified"),
            size=data.get("size"),
            md5=data.get("md5"),
            sha256=data.get("sha256"),
            mime_type=data.get("mime_type"),
            file=data.get("file"),
        )


@dataclass
class ResourceList:
    """Represents a list of items within a directory."""

    items: List[ResourceItem]
    limit: Optional[int] = None
    offset: Optional[int] = None
    path: Optional[str] = None
    total: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceList":
        items = [ResourceItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            items=items,
            limit=data.get("limit"),
            offset=data.get("offset"),
            path=data.get("path"),
            total=data.get("total"),
        )


@dataclass
class ResourceInfo:
    """Represents metadata of a Yandex.Disk public resource."""

    name: str
    type: str
    public_key: str
    public_url: str
    path: str
    created: str
    modified: str
    views_count: Optional[int] = None
    downloads_count: Optional[int] = None
    size: Optional[int] = None
    md5: Optional[str] = None
    sha256: Optional[str] = None
    mime_type: Optional[str] = None
    _embedded: Optional[ResourceList] = None
    file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceInfo":
        embedded_data = data.get("_embedded")
        embedded = ResourceList.from_dict(embedded_data) if embedded_data else None

        return cls(
            name=data.get("name", ""),
            type=data.get("type", "file"),
            public_key=data.get("public_key", ""),
            public_url=data.get("public_url", ""),
            path=data.get("path", ""),
            created=data.get("created", ""),
            modified=data.get("modified", ""),
            views_count=data.get("views_count"),
            downloads_count=data.get("downloads_count"),
            size=data.get("size"),
            md5=data.get("md5"),
            sha256=data.get("sha256"),
            mime_type=data.get("mime_type"),
            _embedded=embedded,
            file=data.get("file"),
        )
