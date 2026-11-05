"""Build the public dashboard data from reconciled INEGI editions."""
import json
from collections import Counter, defaultdict
from zipfile import ZipFile

from audit_ed import ROOT
from audit_ed_historica import csv_content, dbf_rows

ANALYTICS = ROOT / "data/analytics"
RAW = ROOT / "data/raw"
OUTPUT = ROOT / "web/public/indicadores.json"


def custody_rows(year, archive, member):
    fields = ("ent_regis", "tipo_div", "custodia", "sexo_div1", "sexo_div2", "hij_men")
    with ZipFile(archive) as bundle:
        if year >= 2023:
            rows = csv_content(bundle, member)
            header = next(rows)
            indexes = [header.index(field) for field in fields]
            for row in rows:
                yield [row[index] for index in indexes]
        else:
            rows = dbf_rows(bundle, member)
            spans = {label: (offset, offset + length) for label, _, length, offset in next(rows)}
            for row in rows:
                if row[:1] == b" ":
                    yield [row[slice(*spans[field])].strip().decode("ascii") for field in fields]


def read_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    historic = read_report(ANALYTICS / "auditoria-ed-historica.json")
    if historic["faltantes"]:
        raise ValueError("Hay paquetes históricos pendientes")
    data = {}
    for year in range(1985, 2026):
        if year <= 2022:
            report = historic["por_anio"][str(year)]
            passed = report["coincide_total_oficial"]
            archive = RAW / report["archivo"]
            member = report["miembro"]
            key = "tipo_div_"
        else:
            report = read_report(ANALYTICS / f"auditoria-ed{year}.json")
            passed = all(report["controles"].values())
            archive = RAW / f"ed{year}.zip"
            member = f"conjunto_de_datos/conjunto_de_datos_ed{year}.csv"
            key = "tramite_"
        if not passed:
            raise ValueError(f"Edición sin conciliar: {year}")

        custody = defaultdict(Counter)
        custody_with_children = defaultdict(Counter)
        children = Counter()
        children_unknown = Counter()
        no_award_unknown = Counter()
        if year >= 2014:
            for state, procedure, code, sex1, sex2, child_count in custody_rows(year, archive, member):
                if procedure == "1":
                    label = code
                    if code in {"1", "2"}:
                        sex = sex1 if code == "1" else sex2
                        label = {"1": "hombre", "2": "mujer"}.get(sex, "sexo_desconocido")
                    state = state.zfill(2)
                    custody[state][label] += 1
                    if child_count in {"98", "99", ""}:
                        children_unknown[state] += 1
                        no_award_unknown[state] += code == "0"
                    elif not child_count.isdecimal() or not 0 <= int(child_count) <= 25:
                        raise ValueError(f"Numero de menores fuera de rango: {year}, {state}, {child_count}")
                    elif int(child_count) > 0:
                        custody_with_children[state][label] += 1
                        children[state] += int(child_count)
        states = {}
        for state, row in report["por_entidad_de_registro"].items():
            judicial = row.get(key + "1", 0)
            administrative = row.get(key + "2", 0)
            if judicial + administrative != row["registros"]:
                raise ValueError(f"Tipos de trámite sin conciliar: {year}, {state}")
            if year >= 2014 and custody[state].total() != judicial:
                raise ValueError(f"Universo judicial sin conciliar: {year}, {state}")
            states[state] = [judicial, administrative, dict(custody[state]) if year >= 2014 else None]
            if year >= 2014:
                states[state].append({
                    "cases": custody_with_children[state].total(),
                    "children": children[state],
                    "unknown": children_unknown[state],
                    "noAwardUnknown": no_award_unknown[state],
                    "custody": dict(custody_with_children[state]),
                })
        if sum(row[0] + row[1] for row in states.values()) != report["registros"]:
            raise ValueError(f"Entidades sin conciliar: {year}")
        data[year] = states
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
