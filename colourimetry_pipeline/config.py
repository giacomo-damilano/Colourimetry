"""Configuration objects describing the datasets and plotting options."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence

from .data import CUSTOM_ILLUMINANTS


@dataclass
class DirectoryConfig:
    name: str
    path: Path
    mode: str = "A"
    measurement: str = "transmittance"
    extension: str = ".sp"
    replicate_suffix: str = "#"


@dataclass
class DatasetGroup:
    name: str
    source: str  # "all" or "averaged"
    keys: Sequence[str]
    extra_assignments: Mapping[str, str] = field(default_factory=dict)


LABEL_KEYS_GENERAL: Dict[str, str] = {
    '240514_biomass_baseline': 'Biomass baseline (Athrospira Platensis, dry biomass)',
    '240417_EtOH_Ac_soxhlet': 'EtOH:Ac, soxhlet, 24h',
    '240417_EtOH_soxhlet': 'EtOH, soxhlet, 24h',
    '240417_MeOH_soxhlet': 'MeOH, soxhlet, 24h',
    '240514_powderised_MeOH_soxhlet': 'MeOH, powderised biomass, soxhlet, 24h',
    '240701_MeOH_48h_soxhlet': 'MeOH, soxhlet, 48h',
    '240417_EtOH_macerate': 'EtOH, macerate, RT, weeks',
    '240417_MeOH_macerate': 'MeOH, macerate, RT, weeks',
    '240514_EtOH-NaOH_10.1_MeOH_clean': 'EtOH, NaOH, macerate, 24h (x5)',
    '240701_EtOH.Ac_5x1h_1400': 'EtOH:Ac, macerate, 60C, 1h (x5)',
    '240712_EtOH.Ac_5x2h_1400': 'EtOH:Ac, macerate, 60C, 2h (x5)',
    '240712_EtOH.Ac_5x2h_1400_2': 'EtOH:Ac, macerate, 60C, 2h (x5)',
    '240701_EtOH.Ac_5x24h_1400': 'EtOH:Ac, macerate, 60C, 24h (x5)',
    '240701_EtOH_5x1h_1400': 'EtOH, macerate, 60C, 1h (x5)',
    '240712_EtOH_5x2h_1400': 'EtOH, macerate, 60C, 2h (x5)',
    '240701_EtOH_5x24h_1400': 'EtOH, macerate, 60C, 24h (x5)',
    '240701_MeOH_5x1h_1400': 'MeOH, macerate, 60C, 1h (x5)',
    '240712_MeOH_5x2h_1400': 'MeOH, macerate, 60C, 2h (x5)',
    '240701_MeOH_5x24h_1400': 'MeOH, macerate, 60C, 24h (x5)',
    '240701_MeOH_5x24_MeOH_12.5%_ChMeSO3': 'MeOH, ChMeSO3(12.5%), macerate, 60C, 24h (x5)',
    '240712_BaSO4_direct': 'White standard (Barium Sulphate)',
    '240730_ChCl1M_1x20m_EtOH_5x24h_1400_RT': None,
    '240701_EtOH_5x24_EtOH_10%_ChMeSO3': 'EtOH, ChMeSO3(10%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_EtOH_12..5%_ChMeSO3': 'EtOH, ChMeSO3(12.5%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_EtOH_15%_ChMeSO3': 'EtOH, ChMeSO3(15%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_EtOH_5%_ChMeSO3': 'EtOH, ChMeSO3(5%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_EtOH_7.5%_ChMeSO3': 'EtOH, ChMeSO3(7.5%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_MeOH_12.5%_ChMeSO3': 'MeOH, ChMeSO3(12.5%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_MeOH_50%_ChMeSO3': 'MeOH, ChMeSO3(50%), macerate, 60C, 24h (x5)',
    '240701_EtOH_5x24_MeOH_6.25%_ChMeSO3': 'MeOH, ChMeSO3(6.25%), macerate, 60C, 24h (x5)'
}

LABEL_KEYS_LAS: Dict[str, str] = {
    '240801_ISABEL_IF1_170C_45_0LAS': '170 °C, 45 min, 0% LAS',
    '240801_ISABEL_IF2_150C_45_2LAS': '150 °C, 45 min, 2% LAS',
    '240801_ISABEL_IF2_150C_45_4LAS': '150 °C, 45 min, 4% LAS',
    '240801_ISABEL_IF2_170C_45_2LAS': '170 °C, 45 min, 2% LAS',
    '240801_ISABEL_IF2_170C_45_4LAS': '170 °C, 45 min, 4% LAS',
    '240801_ISABEL_IF3_170C_45_0LAS': '170 °C, 45 min, 0% LAS',
    '240801_ISABEL_IF4_150C_45_10LAS': '150 °C, 45 min, 10% LAS',
    '240912_ISABEL_IF1_150C_45_0LAS': '150 °C, 45 min, 0% LAS',
    '240912_ISABEL_IF3_150C_45_6LAS': '150 °C, 45 min, 6% LAS',
    '240912_ISABEL_IF3_170C_45_6LAS': '170 °C, 45 min, 6% LAS',
}


RAINBOW_COLOURS = ['#FF0000', '#FF7F00', '#00FF00', '#0000FF', '#8B00FF']


REFERENCE_LAB = [9.97798957e+01, 3.74284143e-02, -7.90433837e+00]


DEFAULT_GROUPS: Sequence[DatasetGroup] = (
    DatasetGroup(
        name="MeOH_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240417_MeOH_soxhlet_#1",
            "240417_MeOH_soxhlet_#2",
            "240417_MeOH_soxhlet_#3",
        ],
    ),
    DatasetGroup(
        name="EtOH_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240417_EtOH_soxhlet_#1",
            "240417_EtOH_soxhlet_#2",
            "240417_EtOH_soxhlet_#3",
        ],
    ),
    DatasetGroup(
        name="EtOH_Ac_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240417_EtOH_Ac_soxhlet_#1",
            "240417_EtOH_Ac_soxhlet_#2",
            "240417_EtOH_Ac_soxhlet_#3",
            "240417_EtOH_Ac_soxhlet_#4",
        ],
    ),
    DatasetGroup(
        name="MeOH_clean_data",
        source="averaged",
        keys=[
            "240514_biomass_baseline",
            "240417_MeOH_macerate",
            "240514_powderised_MeOH_soxhlet",
            "240417_MeOH_soxhlet",
        ],
    ),
    DatasetGroup(
        name="clean_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240417_MeOH_macerate",
            "240514_powderised_MeOH_soxhlet",
            "240514_EtOH-NaOH_10.1_MeOH_clean",
            "240417_EtOH_macerate",
        ],
        extra_assignments={
            "240417_EtOH_Ac_soxhlet": "averaged:240417_EtOH_Ac_soxhlet",
        },
    ),
    DatasetGroup(
        name="acetone_ethanol_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240417_MeOH_macerate",
            "240417_EtOH_macerate",
        ],
        extra_assignments={
            "240417_EtOH_Ac_soxhlet": "averaged:240417_EtOH_Ac_soxhlet",
            "240417_EtOH_soxhlet": "averaged:240417_EtOH_soxhlet",
        },
    ),
    DatasetGroup(
        name="acetone_methanol_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240417_MeOH_macerate",
            "240514_powderised_MeOH_soxhlet",
        ],
        extra_assignments={
            "240417_EtOH_Ac_soxhlet": "averaged:240417_EtOH_Ac_soxhlet",
            "240417_MeOH_soxhlet": "averaged:240417_MeOH_soxhlet",
        },
    ),
    DatasetGroup(
        name="soxhlet_data",
        source="all",
        keys=[
            "240514_biomass_baseline",
            "240514_powderised_MeOH_soxhlet",
        ],
        extra_assignments={
            "240417_EtOH_Ac_soxhlet": "averaged:240417_EtOH_Ac_soxhlet",
            "240417_MeOH_soxhlet": "averaged:240417_MeOH_soxhlet",
            "240417_EtOH_soxhlet": "averaged:240417_EtOH_soxhlet",
        },
    ),
    DatasetGroup(
        name="maceration_data",
        source="all",
        keys=[
            "240701_EtOH.Ac_5x1h_1400",
            "240701_EtOH.Ac_5x24h_1400",
            "240701_EtOH_5x1h_1400",
            "240701_EtOH_5x24h_1400",
            "240701_MeOH_5x1h_1400",
            "240701_MeOH_5x24h_1400",
            "240712_EtOH_5x2h_1400",
            "240712_MeOH_5x2h_1400",
            "240712_EtOH.Ac_5x2h_1400_2",
        ],
    ),
    DatasetGroup(
        name="IL_maceration_data",
        source="all",
        keys=[
            "240701_MeOH_5x24_MeOH_12.5%_ChMeSO3",
            "240701_EtOH_5x24_EtOH_5%_ChMeSO3",
            "240701_EtOH_5x24_EtOH_7.5%_ChMeSO3",
            "240701_EtOH_5x24_EtOH_10%_ChMeSO3",
            "240701_EtOH_5x24_EtOH_12..5%_ChMeSO3",
            "240701_EtOH_5x24_EtOH_15%_ChMeSO3",
            "240701_EtOH_5x24_MeOH_50%_ChMeSO3",
            "240701_EtOH_5x24_MeOH_12.5%_ChMeSO3",
            "240701_EtOH_5x24_MeOH_6.25%_ChMeSO3",
        ],
    ),
    DatasetGroup(
        name="calibration_data",
        source="all",
        keys=[
            "240712_BaSO4_direct",
            "240730_ChCl1M_1x20m_EtOH_5x24h_1400_RT",
        ],
    ),
)


@dataclass
class NotebookConfig:
    required_packages: Sequence[str] = ("scipy", "numpy")
    directories: Sequence[DirectoryConfig] = ()
    groups: Sequence[DatasetGroup] = DEFAULT_GROUPS
    illuminants: Mapping[str, object] = field(default_factory=lambda: CUSTOM_ILLUMINANTS)
    label_maps: Mapping[str, Mapping[str, Optional[str]]] = field(
        default_factory=lambda: {
            "general": LABEL_KEYS_GENERAL,
            "las": LABEL_KEYS_LAS,
        }
    )
    rainbow_colours: Sequence[str] = RAINBOW_COLOURS
    reference_lab: Sequence[float] = REFERENCE_LAB
