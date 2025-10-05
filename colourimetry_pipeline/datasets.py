"""Data structures for organising spectra and derived datasets."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np

from .spectrum_parser import SpectralRecord, SpcFileParser


@dataclass
class DatasetEntry:
    """Represents a stored spectrum together with metadata."""

    record: SpectralRecord
    measurement: str = "transmittance"
    metadata: MutableMapping[str, object] = field(default_factory=dict)

    def as_array(self, quantity: str = "transmittance") -> np.ndarray:
        pairs = list(self.record.as_pairs(quantity))
        return np.array(pairs, dtype=float)


class DatasetCollection:
    """Container for multiple :class:`DatasetEntry` objects."""

    def __init__(self) -> None:
        self.entries: Dict[str, DatasetEntry] = {}

    def __contains__(self, key: str) -> bool:  # pragma: no cover - convenience
        return key in self.entries

    def __iter__(self) -> Iterator[str]:  # pragma: no cover - convenience
        yield from self.entries

    def add(self, name: str, record: SpectralRecord, measurement: str = "transmittance", **metadata: object) -> None:
        self.entries[name] = DatasetEntry(record=record, measurement=measurement, metadata=dict(metadata))

    def subset(self, keys: Sequence[str]) -> "DatasetCollection":
        subset = DatasetCollection()
        for key in keys:
            subset.entries[key] = self.entries[key]
        return subset

    def extend(self, other: "DatasetCollection") -> None:
        self.entries.update(other.entries)

    def items(self) -> Iterable[Tuple[str, DatasetEntry]]:  # pragma: no cover
        return self.entries.items()

    def averaged(self, suffix: str = "#") -> "DatasetCollection":
        """Return a collection where measurements ending with a numbered suffix are averaged."""

        grouped: Dict[str, List[DatasetEntry]] = defaultdict(list)
        for key, entry in self.entries.items():
            if suffix and suffix in key:
                root = key.split(suffix)[0]
            else:
                root = key
            grouped[root].append(entry)

        averaged_collection = DatasetCollection()
        for root, entries in grouped.items():
            if len(entries) == 1:
                averaged_collection.entries[root] = entries[0]
                continue

            wavelengths = np.stack([entry.record.wavelengths for entry in entries], axis=0)
            values = np.stack([entry.record.transmittances for entry in entries], axis=0)
            mean_wavelengths = wavelengths.mean(axis=0)
            mean_values = values.mean(axis=0)
            absorbances = -np.log10(np.clip(mean_values, 1e-12, None))
            averaged_collection.entries[root] = DatasetEntry(
                record=SpectralRecord(mean_wavelengths, absorbances, mean_values),
                measurement="transmittance",
                metadata=dict(entries[0].metadata),
            )
        return averaged_collection

    @classmethod
    def from_directory(
        cls,
        path: Path,
        measurement: str = "transmittance",
        mode: str = "A",
        extension: str = ".sp",
    ) -> "DatasetCollection":
        """Load all SPC files from ``path`` into a new collection."""

        collection = cls()
        for item in sorted(Path(path).iterdir()):
            if item.suffix.lower() != extension.lower():
                continue
            parser = SpcFileParser(item, mode=mode)
            record = parser.parse()
            collection.add(item.stem, record, measurement=measurement)
        return collection


def merge_collections(collections: Mapping[str, DatasetCollection]) -> DatasetCollection:
    merged = DatasetCollection()
    for collection in collections.values():
        merged.extend(collection)
    return merged
