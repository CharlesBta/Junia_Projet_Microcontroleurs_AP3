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


def save_values(values):
    with VALUES_PATH.open("w", encoding="utf-8") as file:
        json.dump(values, file, indent=4)
        file.write("\n")


def ask_float(name, unit="", default=None):
    prompt = f"{name} {unit}"
    if default is not None:
        prompt += f" [{default}]"
    prompt += " = "

    while True:
        value = input(prompt).strip()

        if value == "" and default is not None:
            return float(default)

        try:
            return float(value.replace(",", "."))
        except ValueError:
            print("Valeur invalide, entre un nombre.")


def ask_component(values, case_key, name, json_unit, display_unit, factor):
    case_values = values.setdefault(case_key, {})
    json_key = f"{name}_{json_unit}"
    value = ask_float(name, f"[{display_unit}]", case_values.get(json_key))
    case_values[json_key] = value
    save_values(values)
    return value * factor


def ask_resistance(values, case_key, name):
    return ask_component(values, case_key, name, "kohm", "kΩ", 1e3)


def ask_capacitance(values, case_key, name):
    return ask_component(values, case_key, name, "nf", "nF", 1e-9)


def bode_plot(num, den, title, f_min=1, f_max=1e6, points=2000):
    """
    num, den : coefficients du numérateur et dénominateur en s
    Exemple : H(s) = (a*s + b) / (c*s + d)
    """
    system = signal.TransferFunction(num, den)

    f = np.logspace(np.log10(f_min), np.log10(f_max), points)
    w = 2 * np.pi * f

    w, mag, phase = signal.bode(system, w)

    plt.figure()
    plt.semilogx(f, mag)
    plt.grid(True, which="both")
    plt.xlabel("Fréquence [Hz]")
    plt.ylabel("Gain [dB]")
    plt.title(title + " - Gain")

    plt.figure()
    plt.semilogx(f, phase)
    plt.grid(True, which="both")
    plt.xlabel("Fréquence [Hz]")
    plt.ylabel("Phase [°]")
    plt.title(title + " - Phase")

    plt.show()


def cas_1_passe_bas(values):
    """
    Cas 1 :
    OUT_MIX -- R0 -- noeud -- C0 vers Vref -- buffer

    Fonction de transfert AC :
    H(s) = 1 / (1 + s R0 C0)
    """

    print("\nCas 1 : filtre passe-bas RC + buffer")
    R0 = ask_resistance(values, "cas_1_passe_bas", "R0")
    C0 = ask_capacitance(values, "cas_1_passe_bas", "C0")

    tau = R0 * C0
    fc = 1 / (2 * np.pi * tau)

    print(f"Fréquence de coupure fc = {fc:.2f} Hz")

    # H(s) = 1 / (tau*s + 1)
    num = [1]
    den = [tau, 1]

    bode_plot(num, den, "Cas 1 - Passe-bas")


def cas_2_passe_haut(values):
    """
    Cas 2 :
    OUT_MIX -- C1 -- noeud -- R1 vers Vref -- buffer

    Fonction de transfert AC :
    H(s) = s R1 C1 / (1 + s R1 C1)
    """

    print("\nCas 2 : filtre passe-haut RC + buffer")
    R1 = ask_resistance(values, "cas_2_passe_haut", "R1")
    C1 = ask_capacitance(values, "cas_2_passe_haut", "C1")

    tau = R1 * C1
    fc = 1 / (2 * np.pi * tau)

    print(f"Fréquence de coupure fc = {fc:.2f} Hz")

    # H(s) = tau*s / (tau*s + 1)
    num = [tau, 0]
    den = [tau, 1]

    bode_plot(num, den, "Cas 2 - Passe-haut")


def cas_3_actif(values):
    """
    Cas 3 :
    Ampli-op inverseur autour de Vref.

    Entrée :
        R2 en série avec C2
        Zin = R2 + 1/(s C2)

    Feedback :
        R3 en parallèle avec C3
        Zf = R3 / (1 + s R3 C3)

    Fonction de transfert AC :
        H(s) = - Zf / Zin

    Après simplification :
        H(s) = - s R3 C2 / ((1 + s R2 C2)(1 + s R3 C3))
    """

    print("\nCas 3 : filtre actif inverseur")
    R2 = ask_resistance(values, "cas_3_actif", "R2")
    C2 = ask_capacitance(values, "cas_3_actif", "C2")
    R3 = ask_resistance(values, "cas_3_actif", "R3")
    C3 = ask_capacitance(values, "cas_3_actif", "C3")

    fc_bas = 1 / (2 * np.pi * R2 * C2)
    fc_haut = 1 / (2 * np.pi * R3 * C3)

    gain_milieu = R3 / R2

    print(f"Fréquence de coupure basse approximative  = {fc_bas:.2f} Hz")
    print(f"Fréquence de coupure haute approximative  = {fc_haut:.2f} Hz")
    print(f"Gain en bande moyenne approximatif        = {gain_milieu:.3f}")
    print(f"Gain en bande moyenne approximatif        = {20*np.log10(gain_milieu):.2f} dB")

    # H(s) = - s R3 C2 / ((1 + s R2 C2)(1 + s R3 C3))
    #
    # Dénominateur :
    # (1 + s R2 C2)(1 + s R3 C3)
    # = s² R2 C2 R3 C3 + s(R2 C2 + R3 C3) + 1

    num = [-R3 * C2, 0]
    den = [
        R2 * C2 * R3 * C3,
        R2 * C2 + R3 * C3,
        1
    ]

    bode_plot(num, den, "Cas 3 - Filtre actif inverseur")


def cas_4_actif(values):
    """
    Cas 4 :
    Même montage et même fonction de transfert que le cas 3.

    Entrée :
        R4 en série avec C4
        Zin = R4 + 1/(s C4)

    Feedback :
        R5 en parallèle avec C5
        Zf = R5 / (1 + s R5 C5)

    Après simplification :
        H(s) = - s R5 C4 / ((1 + s R4 C4)(1 + s R5 C5))
    """

    print("\nCas 4 : filtre actif inverseur")
    R4 = ask_resistance(values, "cas_4_actif", "R4")
    C4 = ask_capacitance(values, "cas_4_actif", "C4")
    R5 = ask_resistance(values, "cas_4_actif", "R5")
    C5 = ask_capacitance(values, "cas_4_actif", "C5")

    fc_bas = 1 / (2 * np.pi * R4 * C4)
    fc_haut = 1 / (2 * np.pi * R5 * C5)

    gain_milieu = R5 / R4

    print(f"Fréquence de coupure basse approximative  = {fc_bas:.2f} Hz")
    print(f"Fréquence de coupure haute approximative  = {fc_haut:.2f} Hz")
    print(f"Gain en bande moyenne approximatif        = {gain_milieu:.3f}")
    print(f"Gain en bande moyenne approximatif        = {20*np.log10(gain_milieu):.2f} dB")

    num = [-R5 * C4, 0]
    den = [
        R4 * C4 * R5 * C5,
        R4 * C4 + R5 * C5,
        1
    ]

    bode_plot(num, den, "Cas 4 - Filtre actif inverseur")


def main():
    values = load_values()

    print("Générateur de diagrammes de Bode")
    print("--------------------------------")
    print("1 : Cas 1 - Passe-bas RC + buffer")
    print("2 : Cas 2 - Passe-haut RC + buffer")
    print("3 : Cas 3 - Filtre actif inverseur")
    print("4 : Cas 4 - Filtre actif inverseur")

    choix = input("\nChoisis le cas à tracer : ")

    if choix == "1":
        cas_1_passe_bas(values)
    elif choix == "2":
        cas_2_passe_haut(values)
    elif choix == "3":
        cas_3_actif(values)
    elif choix == "4":
        cas_4_actif(values)
    else:
        print("Choix invalide.")
        return

    save_values(values)
    print(f"Valeurs enregistrées dans {VALUES_PATH.name}.")


if __name__ == "__main__":
    main()
