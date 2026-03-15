from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent
LRN_PATH = BASE_DIR / "aktywnosci.lrn"
SOURCE_PATH = BASE_DIR / "zrod003.zw"
DESCRIPTIONS_PATH = BASE_DIR / "coto_aktywnosci.txt"
RULE_EXPLANATIONS_PATH = BASE_DIR / "metafory_aktywnosci.txt"


def normalize_token(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned


def pretty_token(value: str) -> str:
    return value.replace("_", " ")


def parse_lrn(path: Path) -> tuple[list[str], dict[tuple[str, str, str], str], dict[str, list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Brak pliku: {path}")

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError("Plik LRN ma za mało danych.")

    headers = [column.lstrip("#") for column in lines[1].split("\t")]
    if len(headers) != 4:
        raise ValueError("Plik LRN powinien mieć dokładnie 4 kolumny.")

    input_headers = headers[:3]
    data_map: Dict[Tuple[str, str, str], str] = {}
    options: Dict[str, list[str]] = {name: [] for name in input_headers}

    for raw_line in lines[2:]:
        parts = raw_line.split("\t")
        if len(parts) != 4:
            raise ValueError(f"Niepoprawny wiersz LRN: {raw_line}")

        typ, miejsce, towarzystwo, aktywnosc = (normalize_token(item) for item in parts)
        key = (typ, miejsce, towarzystwo)
        data_map[key] = aktywnosc

        for header, value in zip(input_headers, key):
            if value not in options[header]:
                options[header].append(value)

    return input_headers, data_map, options


def parse_descriptions(path: Path) -> dict[str, str]:
    descriptions: Dict[str, str] = {}
    if not path.exists():
        return descriptions

    lines = path.read_text(encoding="utf-8").splitlines()
    current_key: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("##") and "=" in line:
            _, right = line.split("=", 1)
            current_key = normalize_token(right)
            continue

        if current_key is not None:
            descriptions[current_key] = line
            current_key = None

    return descriptions


def parse_rule_explanations(path: Path) -> dict[str, str]:
    explanations: Dict[str, str] = {}
    if not path.exists():
        return explanations

    lines = path.read_text(encoding="utf-8").splitlines()
    current_rule: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("##") and line[2:].isdigit():
            current_rule = line[2:]
            continue

        if current_rule is not None:
            explanations[current_rule] = line
            current_rule = None

    return explanations


def parse_rule_ids(path: Path) -> dict[tuple[str, str, str], str]:
    rule_map: Dict[Tuple[str, str, str], str] = {}
    if not path.exists():
        return rule_map

    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        r"(?P<id>\d+)\s*:\s*polecana_aktywnosc\s*=\s*\"(?P<activity>[^\"]+)\"\s*if(?P<body>.*?);",
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        rule_id = match.group("id")
        body = match.group("body")

        cond_pairs = re.findall(r"(typ_aktywnosci|miejsce|towarzystwo)\s*=\s*\"([^\"]+)\"", body)
        cond_dict = {name: normalize_token(value) for name, value in cond_pairs}

        if {"typ_aktywnosci", "miejsce", "towarzystwo"}.issubset(cond_dict):
            key = (
                cond_dict["typ_aktywnosci"],
                cond_dict["miejsce"],
                cond_dict["towarzystwo"],
            )
            rule_map[key] = rule_id

    return rule_map


def ask_choice(question: str, options: List[str]) -> str:
    print(f"\n{question}")
    for idx, option in enumerate(options, start=1):
        print(f"  {idx}. {pretty_token(option)}")

    while True:
        choice = input("Wpisz numer lub nazwę: ").strip()

        if choice.isdigit():
            number = int(choice)
            if 1 <= number <= len(options):
                return options[number - 1]

        normalized = normalize_token(choice)
        for option in options:
            if normalized == option:
                return option

        print("Niepoprawny wybór. Spróbuj ponownie.")


def run_expert_system() -> None:
    headers, rule_data, options = parse_lrn(LRN_PATH)
    descriptions = parse_descriptions(DESCRIPTIONS_PATH)
    rule_explanations = parse_rule_explanations(RULE_EXPLANATIONS_PATH)
    rule_ids = parse_rule_ids(SOURCE_PATH)

    selected_typ = ask_choice("Wybierz typ aktywności:", options[headers[0]])
    selected_place = ask_choice("Wybierz miejsce:", options[headers[1]])
    selected_companion = ask_choice("Wybierz towarzystwo:", options[headers[2]])

    key = (selected_typ, selected_place, selected_companion)
    activity = rule_data.get(key)

    print("\n" + "=" * 60)
    print("WYNIK SYSTEMU EKSPERCKIEGO")
    print("=" * 60)

    if not activity:
        print("Brak rekomendacji dla podanej kombinacji.")
        return

    print(f"Polecana aktywność: {pretty_token(activity)}")

    for fact in [selected_typ, selected_place, selected_companion, activity]:
        if fact in descriptions:
            print(f"- {descriptions[fact]}")

    rule_id = rule_ids.get(key)
    if rule_id:
        print(f"Aktywowana reguła: {rule_id}")
        if rule_id in rule_explanations:
            print(rule_explanations[rule_id])


def main() -> None:
    try:
        run_expert_system()
    except (FileNotFoundError, ValueError) as error:
        print(f"Błąd: {error}")


if __name__ == "__main__":
    main()
