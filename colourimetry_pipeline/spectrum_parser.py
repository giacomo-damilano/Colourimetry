"""Utilities for reading SPC spectral files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np

try:  # Optional dependency, retained for compatibility with the notebook
    from specio import specread  # type: ignore
except Exception:  # pragma: no cover - handled gracefully at runtime
    specread = None


@dataclass
class SpectralRecord:
    """Container representing a single spectral acquisition."""

    wavelengths: np.ndarray
    absorbances: np.ndarray
    transmittances: np.ndarray

    def as_pairs(self, quantity: str = "absorbance") -> Iterable[Tuple[float, float]]:
        """Yield wavelength/value pairs for the requested quantity."""

        data = {
            "absorbance": self.absorbances,
            "transmittance": self.transmittances,
        }[quantity.lower()]
        for wl, value in zip(self.wavelengths, data):
            yield float(wl), float(value)


class SpcFileParser:
    """Parse SPC spectral files and return processed :class:`SpectralRecord` objects."""

    def __init__(self, filename: Path, mode: str = "A") -> None:
        self.filename = Path(filename)
        self.mode = mode.upper()
        if self.mode not in {"A", "T", "R"}:
            raise ValueError("mode must be 'A' (absorbance), 'T' (transmittance) or 'R' (reflectance)")

    def parse(self) -> SpectralRecord:
        if specread is None:
            raise RuntimeError(
                "specio is not available in this environment. Install it to parse SPC files."
            )

        spectra = specread(str(self.filename))
        wavelengths = np.asarray(spectra.wavelength, dtype=float)
        amplitudes = np.asarray(spectra.amplitudes, dtype=float)

        if self.mode == "A":
            absorbances = amplitudes
            transmittances = 10 ** (-amplitudes)
        elif self.mode == "T":
            transmittances = amplitudes
            absorbances = -np.log10(np.clip(amplitudes, 1e-12, None))
        else:  # Reflectance
            absorbances = 1 - amplitudes
            transmittances = 10 ** (-absorbances)

        selector = (wavelengths % 1 == 0) & (wavelengths >= 250) & (wavelengths <= 800)
        sort_idx = np.argsort(wavelengths[selector])
        return SpectralRecord(
            wavelengths=wavelengths[selector][sort_idx],
            absorbances=absorbances[selector][sort_idx],
            transmittances=transmittances[selector][sort_idx],
        )
