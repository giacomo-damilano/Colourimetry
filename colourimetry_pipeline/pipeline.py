"""High level orchestration for the refactored colourimetry workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

import numpy as np

from .analysis import ColourMetrics, blackbody_illuminant, compute_colour_metrics
from .config import (
    DatasetGroup,
    DirectoryConfig,
    NotebookConfig,
)
from .data import SAMPLE_SPECTRA
from .datasets import DatasetCollection, SpectralRecord
from .plotting import PlotManager, SamplePoint

LOGGER = logging.getLogger(__name__)


@dataclass
class ColourResult:
    name: str
    metrics: ColourMetrics
    decolouring_percentage: float
    white_distance: float

    @property
    def rgb_int(self) -> List[int]:
        return [int(round(channel * 255)) for channel in self.metrics.rgb]


class ColourimetryPipeline:
    """Object oriented wrapper around the original notebook workflow."""

    def __init__(self, config: Optional[NotebookConfig] = None, output_dir: Optional[Path] = None) -> None:
        self.config = config or NotebookConfig()
        self.output_dir = Path(output_dir) if output_dir else None
        self.raw_collections: Dict[str, DatasetCollection] = {}
        self.all_data = DatasetCollection()
        self.averaged_data = DatasetCollection()
        self.groups: Dict[str, DatasetCollection] = {}
        self.results: Dict[str, ColourResult] = {}
        self.plot_manager = PlotManager(self.output_dir)

    # ------------------------------------------------------------------
    # Loading and preparation
    # ------------------------------------------------------------------
    def load_directories(self, directories: Optional[Sequence[DirectoryConfig]] = None) -> None:
        directories = directories or self.config.directories
        for directory in directories:
            if not directory.path.exists():
                LOGGER.warning("Directory %s does not exist; skipping", directory.path)
                continue
            collection = DatasetCollection.from_directory(
                path=directory.path,
                measurement=directory.measurement,
                mode=directory.mode,
                extension=directory.extension,
            )
            self.raw_collections[directory.name] = collection
            self.all_data.extend(collection)
        self._build_averaged_dataset()

    def load_sample_spectra(self) -> None:
        """Load the inline spectra embedded in the original notebook."""

        for index, (wavelengths, absorbances) in enumerate(SAMPLE_SPECTRA, start=1):
            wavelengths_array = np.asarray(wavelengths, dtype=float)
            absorbances_array = np.asarray(absorbances, dtype=float)
            transmittances = 10 ** (-absorbances_array)
            record = SpectralRecord(wavelengths_array, absorbances_array, transmittances)
            name = f"sample_{index:02d}"
            self.all_data.add(name, record, measurement="absorbance", source="inline")
        self._build_averaged_dataset()

    def _build_averaged_dataset(self) -> None:
        if not self.all_data.entries:
            return
        self.averaged_data = self.all_data.averaged()

    def build_groups(self, groups: Optional[Sequence[DatasetGroup]] = None) -> None:
        groups = groups or self.config.groups
        collection_lookup = {
            "all": self.all_data,
            "averaged": self.averaged_data,
        }
        for group in groups:
            source_collection = collection_lookup.get(group.source)
            if source_collection is None:
                raise ValueError(f"Unknown dataset source '{group.source}'")
            subset = DatasetCollection()
            for key in group.keys:
                if key in source_collection:
                    subset.entries[key] = source_collection.entries[key]
                else:
                    LOGGER.warning("Key %s not found in source collection", key)
            for target_key, descriptor in group.extra_assignments.items():
                try:
                    source_name, source_key = descriptor.split(":", 1)
                except ValueError:
                    LOGGER.error("Invalid assignment descriptor '%s'", descriptor)
                    continue
                source = collection_lookup.get(source_name)
                if source and source_key in source:
                    subset.entries[target_key] = source.entries[source_key]
                else:
                    LOGGER.warning("Assignment %s -> %s could not be resolved", descriptor, target_key)
            self.groups[group.name] = subset

    # ------------------------------------------------------------------
    # Analysis utilities
    # ------------------------------------------------------------------
    def analyse_group(
        self,
        group_name: str,
        illuminant: object = "D65",
        absorbance: bool = True,
        reference_lab: Optional[Sequence[float]] = None,
    ) -> Mapping[str, ColourResult]:
        if group_name not in self.groups:
            raise KeyError(f"Group '{group_name}' has not been built")
        reference_lab = reference_lab or self.config.reference_lab
        if isinstance(illuminant, str):
            if illuminant not in self.config.illuminants:
                raise KeyError(f"Illuminant '{illuminant}' not defined")
            illuminant_sd = self.config.illuminants[illuminant]
        else:
            illuminant_sd = illuminant
        group = self.groups[group_name]
        results: Dict[str, ColourResult] = {}
        for key, entry in group.items():
            spectrum = entry.record.as_pairs("absorbance" if absorbance else "transmittance")
            metrics = compute_colour_metrics(spectrum, absorbance, illuminant_sd, reference_lab)
            decolouring, white_distance = self._compute_colour_distances(metrics.rgb)
            result = ColourResult(name=key, metrics=metrics, decolouring_percentage=decolouring, white_distance=white_distance)
            results[key] = result
            self.results[key] = result
        return results

    def analyse_group_under_illuminants(
        self,
        group_name: str,
        illuminants: Sequence[str],
        absorbance: bool = True,
        reference_lab: Optional[Sequence[float]] = None,
    ) -> Mapping[str, Dict[str, ColourResult]]:
        output: Dict[str, Dict[str, ColourResult]] = {}
        for illuminant in illuminants:
            output[illuminant] = dict(
                self.analyse_group(group_name, illuminant=illuminant, absorbance=absorbance, reference_lab=reference_lab)
            )
        return output

    def analyse_blackbody(
        self,
        group_name: str,
        temperature: float,
        absorbance: bool = True,
        reference_lab: Optional[Sequence[float]] = None,
    ) -> Mapping[str, ColourResult]:
        if group_name not in self.groups:
            raise KeyError(f"Group '{group_name}' has not been built")
        reference_lab = reference_lab or self.config.reference_lab
        illuminant_sd = blackbody_illuminant(temperature)
        results: Dict[str, ColourResult] = {}
        for key, entry in self.groups[group_name].items():
            spectrum = entry.record.as_pairs("absorbance" if absorbance else "transmittance")
            metrics = compute_colour_metrics(spectrum, absorbance, illuminant_sd, reference_lab)
            decolouring, white_distance = self._compute_colour_distances(metrics.rgb)
            result = ColourResult(name=key, metrics=metrics, decolouring_percentage=decolouring, white_distance=white_distance)
            results[key] = result
        return results

    def generate_colour_dataset(
        self,
        group_name: str,
        illuminants: Sequence[str],
        absorbance: bool = True,
    ) -> Dict[str, Dict[str, ColourMetrics]]:
        dataset: Dict[str, Dict[str, ColourMetrics]] = {}
        for illuminant in illuminants:
            analysis = self.analyse_group(group_name, illuminant=illuminant, absorbance=absorbance)
            dataset[illuminant] = {key: result.metrics for key, result in analysis.items()}
        return dataset

    # ------------------------------------------------------------------
    # Plotting wrappers
    # ------------------------------------------------------------------
    def create_swatches(self, samples: Iterable[ColourResult], subtitle: str = "Athrospira Platensis") -> List[Path]:
        paths = []
        for sample in samples:
            paths.append(self.plot_manager.save_swatch(sample.name, sample.metrics.rgb, subtitle))
        return paths

    def plot_whiteness_lightness(
        self,
        samples: Iterable[ColourResult],
        label_map: Mapping[str, Optional[str]],
        categories: Mapping[str, tuple],
        highlight: Optional[Sequence[str]] = None,
        filename: Optional[str] = None,
    ) -> Path:
        sample_points = [
            SamplePoint(
                name=sample.name,
                whiteness=sample.metrics.whiteness,
                lightness=sample.metrics.lightness,
                chroma_distance=sample.metrics.delta_c,
                lab=sample.metrics.lab,
                rgb=sample.metrics.rgb,
            )
            for sample in samples
        ]
        return self.plot_manager.plot_whiteness_vs_lightness(sample_points, label_map, categories, highlight=highlight, filename=filename)

    def plot_lab_parameters(
        self,
        samples: Iterable[ColourResult],
        label_map: Mapping[str, Optional[str]],
        categories: Mapping[str, tuple],
        filename: Optional[str] = None,
    ) -> Path:
        sample_points = [
            SamplePoint(
                name=sample.name,
                whiteness=sample.metrics.whiteness,
                lightness=sample.metrics.lightness,
                chroma_distance=sample.metrics.delta_c,
                lab=sample.metrics.lab,
                rgb=sample.metrics.rgb,
            )
            for sample in samples
        ]
        return self.plot_manager.plot_lab_plane(sample_points, label_map, categories, filename=filename)

    # ------------------------------------------------------------------
    @staticmethod
    def _compute_colour_distances(rgb: Sequence[float]) -> tuple:
        reference_rgb = np.array([68, 77, 55], dtype=float) / 255.0
        rgb = np.asarray(rgb)
        decolouring = float(
            (rgb.sum() - reference_rgb.sum()) / (3 - reference_rgb.sum())
        ) * 100
        white_distance = float(1 - rgb.mean()) * 100
        return decolouring, white_distance
