import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


VALUES_PATH = Path(__file__).with_name("valeurs_bode.json")


def load_values():
    if not VALUES_PATH.exists():
        return {}

    try:
        with VALUES_PATH.open("r", encoding="utf-8") as file:
            values = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Impossible de lire {VALUES_PATH.name} : {error}")
        return {}

    if not isinstance(values, dict):
        print(f"{VALUES_PATH.name} doit contenir un objet JSON.")
        return {}

    return values


def _require_case(values: dict, case_key: str) -> dict:
    case_values = values.get(case_key)
    if not isinstance(case_values, dict):
        raise ValueError(
            f"Dans {VALUES_PATH.name}, la clé '{case_key}' doit contenir un objet JSON."
        )
    return case_values


def _require_float(case_values: dict, key: str, label: str) -> float:
    raw_value = case_values.get(key)
    if raw_value is None:
        raise ValueError(f"Valeur manquante dans {VALUES_PATH.name} : '{key}' ({label}).")
    try:
        return float(raw_value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Valeur invalide dans {VALUES_PATH.name} pour '{key}' ({label}) : {raw_value!r}."
        ) from error


def plot_gain(systems, title="Diagramme de Bode - Gain", f_min=1, f_max=1e6, points=2000):
    """Trace le gain (dB) de plusieurs fonctions de transfert sur un seul graphe."""

    f = np.logspace(np.log10(f_min), np.log10(f_max), points)
    w = 2 * np.pi * f

    plt.figure()
    for label, system in systems:
        _, mag, _ = signal.bode(system, w)
        plt.semilogx(f, mag, label=label)

    plt.grid(True, which="both")
    plt.xlabel("Fréquence [Hz]")
    plt.ylabel("Gain [dB]")
    plt.title(title)
    plt.legend()
    plt.show()


def build_filtre_1(values):
    case_values = _require_case(values, "filtre_1")
    R0 = _require_float(case_values, "R0_kohm", "R0 [kΩ]") * 1e3
    C0 = _require_float(case_values, "C0_nf", "C0 [nF]") * 1e-9

    tau = R0 * C0
    num = [1]
    den = [tau, 1]
    return "OUT_FILTER1", signal.TransferFunction(num, den)


def build_filtre_2(values):
    case_values = _require_case(values, "filtre_2")
    R1 = _require_float(case_values, "R1_kohm", "R1 [kΩ]") * 1e3
    C1 = _require_float(case_values, "C1_nf", "C1 [nF]") * 1e-9

    tau = R1 * C1
    num = [tau, 0]
    den = [tau, 1]
    return "OUT_FILTER2", signal.TransferFunction(num, den)


def build_filtre_3(values):
    case_values = _require_case(values, "filtre_3")
    R2 = _require_float(case_values, "R2_kohm", "R2 [kΩ]") * 1e3
    C2 = _require_float(case_values, "C2_nf", "C2 [nF]") * 1e-9
    R3 = _require_float(case_values, "R3_kohm", "R3 [kΩ]") * 1e3
    C3 = _require_float(case_values, "C3_nf", "C3 [nF]") * 1e-9

    num = [-R3 * C2, 0]
    den = [
        R2 * C2 * R3 * C3,
        R2 * C2 + R3 * C3,
        1,
    ]
    return "OUT_FILTER3", signal.TransferFunction(num, den)


def build_filtre_4(values):
    case_values = _require_case(values, "filtre_4")
    R4 = _require_float(case_values, "R4_kohm", "R4 [kΩ]") * 1e3
    C4 = _require_float(case_values, "C4_nf", "C4 [nF]") * 1e-9
    R5 = _require_float(case_values, "R5_kohm", "R5 [kΩ]") * 1e3
    C5 = _require_float(case_values, "C5_nf", "C5 [nF]") * 1e-9

    num = [-R5 * C4, 0]
    den = [
        R4 * C4 * R5 * C5,
        R4 * C4 + R5 * C5,
        1,
    ]
    return "OUT_FILTER4", signal.TransferFunction(num, den)


def main():
    values = load_values()

    if not values:
        print(
            f"Aucune valeur chargée depuis {VALUES_PATH.name}. "
            "Renseigne le fichier JSON puis relance."
        )
        return

    try:
        systems = [
            build_filtre_1(values),
            build_filtre_2(values),
            build_filtre_3(values),
            build_filtre_4(values),
        ]
    except ValueError as error:
        print(error)
        return

    plot_gain(systems)


if __name__ == "__main__":
    main()
