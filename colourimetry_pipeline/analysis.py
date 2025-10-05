"""Colour conversions and metrics used by the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence, Tuple

import numpy as np

try:  # pragma: no cover - the colour-science package may be unavailable
    import colour
    from colour import MSDS_CMFS, SpectralDistribution, SpectralShape
except Exception as exc:  # pragma: no cover
    colour = None  # type: ignore
    MSDS_CMFS = None  # type: ignore
    SpectralDistribution = None  # type: ignore
    SpectralShape = None  # type: ignore


@dataclass
class ColourMetrics:
    rgb: np.ndarray
    lab: np.ndarray
    xyz: np.ndarray
    whiteness: float
    tint: float
    lightness: float
    chroma: float
    delta_e: float
    delta_c: float


def calculate_xyz_from_spd(
    spd: Sequence[Tuple[float, float]],
    cie_data: Sequence[Sequence[float]],
) -> Tuple[float, float, float]:
    wavelengths_spd = np.asarray([pair[0] for pair in spd], dtype=float)
    power = np.asarray([pair[1] for pair in spd], dtype=float)
    cie = np.asarray(cie_data, dtype=float)
    wavelengths_cie = cie[:, 0]
    x_cie = cie[:, 1]
    y_cie = cie[:, 2]
    z_cie = cie[:, 3]
    x_interp = np.interp(wavelengths_spd, wavelengths_cie, x_cie)
    y_interp = np.interp(wavelengths_spd, wavelengths_cie, y_cie)
    z_interp = np.interp(wavelengths_spd, wavelengths_cie, z_cie)
    X = np.trapz(power * x_interp, wavelengths_spd)
    Y = np.trapz(power * y_interp, wavelengths_spd)
    Z = np.trapz(power * z_interp, wavelengths_spd)
    return float(X), float(Y), float(Z)


def chromatic_adaptation_matrix(source_wp: Sequence[float], target_wp: Sequence[float]) -> np.ndarray:
    M = np.array(
        [
            [0.8951, -0.7502, 0.0389],
            [0.2664, 1.7135, -0.0685],
            [-0.1614, 0.0367, 1.0296],
        ]
    )
    source_cone = M @ np.asarray(source_wp)
    target_cone = M @ np.asarray(target_wp)
    scaling = np.diag(target_cone / source_cone)
    return np.linalg.inv(M) @ scaling @ M


def xyz_to_rgb_conversion_matrix(xyz: Sequence[float], adaptation_matrix: np.ndarray) -> np.ndarray:
    M_sRGB_to_XYZ = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    adapted_xyz = adaptation_matrix @ np.asarray(xyz)
    M_RGB_to_XYZ = M_sRGB_to_XYZ / np.sum(adapted_xyz)
    return np.linalg.inv(M_RGB_to_XYZ)


def spectrum_to_xyz(
    spectrum: Sequence[Tuple[float, float]],
    absorbance: bool = True,
    illuminant: Optional[SpectralDistribution] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    if colour is None:
        raise RuntimeError("The 'colour' package is required for colourimetric computations.")

    spectrum = np.array(spectrum, dtype=float)
    wavelengths = spectrum[:, 0]
    values = spectrum[:, 1]
    mask = (wavelengths >= 360) & (wavelengths <= 800)
    wavelengths = wavelengths[mask]
    values = values[mask]

    if absorbance:
        transmittance = 10 ** (-values)
    else:
        transmittance = values

    sd_transmittance = SpectralDistribution(dict(zip(wavelengths, transmittance)), name="Transmittance")
    cmfs = MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
    xyz = colour.sd_to_XYZ(sd_transmittance, cmfs, method="Integration", illuminant=illuminant)
    xyz = xyz / 100.0
    lab = colour.XYZ_to_Lab(xyz)
    rgb = colour.XYZ_to_sRGB(xyz)
    rgb = np.clip(rgb, 0, 1)
    return rgb, lab, xyz


def whiteness_and_tint(xyz: Sequence[float], reference_xy: Sequence[float] = (0.3139, 0.3311)) -> Tuple[float, float]:
    if colour is None:
        raise RuntimeError("The 'colour' package is required for colourimetric computations.")

    xyz = np.asarray(xyz)
    xy = colour.XYZ_to_xy(xyz)
    Y = xyz[1]
    whiteness, tint = colour.colorimetry.whiteness_CIE2004(xy, Y, np.asarray(reference_xy))
    return float(whiteness), float(tint)


def delta_e(sample_lab: Sequence[float], reference_lab: Sequence[float]) -> float:
    sample_lab = np.asarray(sample_lab)
    reference_lab = np.asarray(reference_lab)
    return float(np.linalg.norm(sample_lab - reference_lab))


def delta_c(sample_lab: Sequence[float], reference_lab: Sequence[float]) -> float:
    sample_lab = np.asarray(sample_lab)
    reference_lab = np.asarray(reference_lab)
    return float(np.linalg.norm(sample_lab[1:3] - reference_lab[1:3]))


def lightness_chroma(lab: Sequence[float]) -> Tuple[float, float]:
    L, a, b = lab
    chroma = float(np.hypot(a, b))
    return float(L), chroma


def lab_to_rgb(lab: Sequence[float]) -> np.ndarray:
    if colour is None:
        raise RuntimeError("The 'colour' package is required for colourimetric computations.")
    rgb = colour.Lab_to_RGB(np.asarray(lab), illuminant=colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"])
    return np.clip(rgb, 0, 1)


def compute_colour_metrics(
    spectrum: Sequence[Tuple[float, float]],
    absorbance: bool,
    illuminant: SpectralDistribution,
    reference_lab: Sequence[float],
) -> ColourMetrics:
    rgb, lab, xyz = spectrum_to_xyz(spectrum, absorbance=absorbance, illuminant=illuminant)
    whiteness, tint = whiteness_and_tint(xyz)
    lightness, chroma = lightness_chroma(lab)
    delta_e_value = delta_e(lab, reference_lab)
    delta_c_value = delta_c(lab, reference_lab)
    return ColourMetrics(rgb, lab, xyz, whiteness, tint, lightness, chroma, delta_e_value, delta_c_value)


def blackbody_illuminant(temperature: float) -> SpectralDistribution:
    if colour is None:
        raise RuntimeError("The 'colour' package is required for colourimetric computations.")
    spectrum = colour.sd_blackbody(temperature, shape=SpectralShape(300, 850, 1))
    return SpectralDistribution(spectrum, name=f"Illuminant ({temperature}K)")


def rgb_to_hex(rgb: Sequence[float]) -> str:
    rgb = np.clip(np.asarray(rgb), 0, 1)
    return "#{:02x}{:02x}{:02x}".format(*[int(round(val * 255)) for val in rgb])


def process_data_and_get_color(
    data: Sequence[Sequence[float]],
    cie_data: Optional[Sequence[Sequence[float]]] = None,
) -> Tuple[np.ndarray, str]:
    if colour is None:
        raise RuntimeError("The 'colour' package is required for colourimetric computations.")

    wavelengths = np.asarray(data[0], dtype=float)
    absorbances = np.asarray(data[1], dtype=float)
    normalized = absorbances / np.max(absorbances)
    spd = list(zip(wavelengths, normalized))
    if cie_data is None:
        from .data import CIE_1931_2_DEGREE  # local import to avoid circular dependency

        cie_data = CIE_1931_2_DEGREE
    xyz = calculate_xyz_from_spd(spd, cie_data)
    rgb = colour.XYZ_to_sRGB(np.asarray(xyz))
    hex_colour = rgb_to_hex(rgb)
    return rgb, hex_colour
