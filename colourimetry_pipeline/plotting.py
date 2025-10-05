"""Plotting helpers for the colourimetry pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.patches import Rectangle
from skimage.color import lab2rgb


@dataclass
class SamplePoint:
    name: str
    whiteness: float
    lightness: float
    chroma_distance: float
    lab: Sequence[float]
    rgb: Sequence[float]


class PlotManager:
    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = Path(output_dir) if output_dir else None

    # ------------------------------------------------------------------
    # Swatch generation
    # ------------------------------------------------------------------
    def save_swatch(self, name: str, rgb: Sequence[float], subtitle: str = "", filename: Optional[str] = None) -> Path:
        figure, ax = plt.subplots(figsize=(3, 4.5))
        ax.imshow([[np.clip(rgb, 0, 1)]], aspect="auto")
        ax.add_patch(Rectangle((0, 0), 1, 0.25, transform=ax.transAxes, color="white"))
        ax.text(
            0.5,
            0.125,
            f"{name}\n{subtitle}\n{[int(c * 255) for c in rgb]}",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="black",
            fontsize=12,
            weight="bold",
        )
        ax.axis("off")
        if filename is None:
            filename = name.replace(" ", "_") + ".png"
        path = self._resolve(filename)
        figure.savefig(path, bbox_inches="tight", pad_inches=0)
        plt.close(figure)
        return path

    # ------------------------------------------------------------------
    # Scatter plots
    # ------------------------------------------------------------------
    def plot_whiteness_vs_lightness(
        self,
        samples: Iterable[SamplePoint],
        label_map: Mapping[str, Optional[str]],
        categories: Mapping[str, Tuple[str, str]],
        highlight: Optional[Sequence[str]] = None,
        title: str = "ΔChroma vs Lightness",
        xlabel: str = "ΔChroma",
        ylabel: str = "Lightness",
        filename: Optional[str] = None,
    ) -> Path:
        figure, ax = plt.subplots(figsize=(10, 8))
        for key, (marker, colour) in categories.items():
            group_points = [sample for sample in samples if key in sample.name]
            if not group_points:
                continue
            ax.scatter(
                [sample.chroma_distance for sample in group_points],
                [sample.lightness for sample in group_points],
                marker=marker,
                s=100,
                color=[sample.rgb for sample in group_points],
                edgecolors="black",
                label=key,
            )
            for sample in group_points:
                label = label_map.get(sample.name, sample.name)
                if label:
                    ax.text(sample.chroma_distance + 1.5, sample.lightness, label, fontsize=10)

        if highlight:
            highlighted = [sample for sample in samples if sample.name in highlight]
            ax.scatter(
                [sample.chroma_distance for sample in highlighted],
                [sample.lightness for sample in highlighted],
                marker="*",
                s=200,
                color=[sample.rgb for sample in highlighted],
                edgecolors="black",
                label="highlight",
            )

        ax.set_title(title, fontsize=18)
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.grid(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(fontsize=12, frameon=False)
        figure.tight_layout()
        path = self._resolve(filename or "whiteness_vs_lightness.png")
        figure.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(figure)
        return path

    # ------------------------------------------------------------------
    # Lab plane visualisation
    # ------------------------------------------------------------------
    def plot_lab_plane(
        self,
        samples: Iterable[SamplePoint],
        label_map: Mapping[str, Optional[str]],
        categories: Mapping[str, Tuple[str, str]],
        L_value: float = 99.0,
        filename: Optional[str] = None,
    ) -> Path:
        figure, ax = plt.subplots(figsize=(10, 10))
        lab_background = self._create_lab_background((-100, 100), (-100, 100), L_value)
        ax.imshow(lab_background, extent=(-100, 100, -100, 100), origin="lower")

        for key, (marker, colour) in categories.items():
            group_points = [sample for sample in samples if key in sample.name]
            if not group_points:
                continue
            ax.scatter(
                [sample.lab[1] for sample in group_points],
                [sample.lab[2] for sample in group_points],
                marker=marker,
                s=100,
                color=[sample.rgb for sample in group_points],
                edgecolors="black",
                label=key,
            )
            for sample in group_points:
                label = label_map.get(sample.name, sample.name)
                if label:
                    ax.text(sample.lab[1] + 1.5, sample.lab[2], label, fontsize=10)

        ax.set_xlabel("Lab parameter (a)", fontsize=14)
        ax.set_ylabel("Lab parameter (b)", fontsize=14)
        ax.set_title("Lab parameters with background", fontsize=18)
        ax.legend(loc="best", fontsize=12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        figure.tight_layout()
        path = self._resolve(filename or "lab_plane.png")
        figure.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(figure)
        return path

    # ------------------------------------------------------------------
    # Gradient curves for LAS study
    # ------------------------------------------------------------------
    def plot_gradient_curves(
        self,
        data_150: Mapping[str, Sequence[float]],
        data_170: Mapping[str, Sequence[float]],
        param: str,
        ylabel: str,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        filename: Optional[str] = None,
    ) -> Path:
        figure, ax = plt.subplots(figsize=(8, 6))
        gradient = self._generate_gradient(param, x_range, y_range)
        ax.imshow(gradient, extent=(x_range[0], x_range[1], y_range[0], y_range[1]), origin="lower", aspect="auto", cmap="coolwarm", alpha=0.3)
        ax.plot(data_150["LAS %"], data_150[param], marker="o", linestyle="-", linewidth=1.5, label="150 °C, 45 min", color="#0072B2")
        ax.plot(data_170["LAS %"], data_170[param], marker="s", linestyle="--", linewidth=1.5, label="170 °C, 45 min", color="#D55E00")
        ax.set_title(f"{ylabel} vs LAS %", fontsize=16, pad=15)
        ax.set_xlabel("LAS %", fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
        ax.tick_params(axis="both", labelsize=12)
        ax.legend(fontsize=12, frameon=False)
        figure.tight_layout()
        path = self._resolve(filename or f"gradient_{param}.png")
        figure.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(figure)
        return path

    # ------------------------------------------------------------------
    def _resolve(self, filename: str) -> Path:
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return self.output_dir / filename
        return Path(filename)

    @staticmethod
    def _create_lab_background(a_range: Tuple[float, float], b_range: Tuple[float, float], L_value: float, resolution: int = 500) -> np.ndarray:
        a_values = np.linspace(a_range[0], a_range[1], resolution)
        b_values = np.linspace(b_range[0], b_range[1], resolution)
        a_grid, b_grid = np.meshgrid(a_values, b_values)
        lab_plane = np.dstack((np.full_like(a_grid, L_value), a_grid, b_grid))
        return lab2rgb(lab_plane)

    @staticmethod
    def _generate_gradient(param: str, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> np.ndarray:
        x = np.linspace(x_range[0], x_range[1], 300)
        y = np.linspace(y_range[0], y_range[1], 300)
        xx, yy = np.meshgrid(x, y)
        if param == "Lightness":
            gradient = 100 - np.sqrt(xx**2 + yy**2)
        else:
            gradient = yy
        gradient = np.clip(gradient, 0, 100)
        norm = colors.Normalize(vmin=np.min(gradient), vmax=np.max(gradient))
        cmap = plt.get_cmap("coolwarm")
        return cmap(norm(gradient))
