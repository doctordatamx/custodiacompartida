"""Audit INEGI ED 2023 to 2025. Requires only Python's standard library."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://www.inegi.org.mx/contenidos/programas/ed/datosabiertos/conjunto_de_datos_ed{year}_csv.zip"
REFERENCE = {2023: (163587, 90.0), 2024: (161932, 89.6), 2025: (155254, 88.3)}
CUSTODY_REFERENCE = {"0": 79956, "1": 28311, "2": 27159, "3": 8547, "4": 76, "98": 16889, "99": 994}
GEOGRAPHIES = (
    ("ent_regis", "mun_regis", "loc_regis"),
    ("ent_mat", "mun_mat", "local_mat"),
    ("ent_rhdiv1", "mun_rhdiv1", "loc_rhdiv1"),
    ("ent_rhdiv2", "mun_rhdiv2", "loc_rhdiv2"),
)


def read_table(bundle, name):
    with bundle.open(name) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")))


def in_range(value, intervals):
    return value.isascii() and value.isdecimal() and any(
        low <= int(value) <= high for low, high in intervals
    )


def parse_ranges(expression):
    intervals = []
    for term in expression.split(","):
        low, _, high = term.strip().partition("..")
        intervals.append((int(low), int(high or low)))
    return intervals


def audit(path, year):
    expected_count, expected_judicial = REFERENCE[year]
    dictionary_dir = "diccionario_datos" if year == 2025 else "diccionario_de_datos"
    with ZipFile(path) as bundle:
        bad_member = bundle.testzip()
        if bad_member:
            raise ValueError(f"CRC incorrecto: {bad_member}")
        dictionary = read_table(bundle, f"{dictionary_dir}/diccionario_datos_ed{year}.csv")
        columns = [field["nemonico"] for field in dictionary]
        ranges = [parse_ranges(field["rango_claves"]) for field in dictionary]
        geography = read_table(bundle, f"catalogos/entidad_municipio_localidad_{year}.csv")
        geographic_keys = {(row["cve_ent"], row["cve_mun"], row["cve_loc"]) for row in geography}
        catalog_codes = {}
        for field in dictionary:
            name = field["catalogo"].strip()
            if name.startswith("entidad_municipio"):
                continue
            # The 2025 dictionary double-encodes the accent in these references.
            name = name.replace("a\u00c3\u00b1o_", "a\u00f1o_")
            rows = read_table(bundle, f"catalogos/{name}.csv")
            catalog_codes[field["nemonico"]] = {int(next(iter(row.values()))) for row in rows}

        observed = {column: Counter() for column in columns}
        duplicates = 0
        seen = set()
        by_state = defaultdict(Counter)
        geography_gaps = {keys[0]: Counter() for keys in GEOGRAPHIES}
        custody_by_sex = Counter()
        with bundle.open(f"conjunto_de_datos/conjunto_de_datos_ed{year}.csv") as raw:
            records = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), strict=True)
            header = next(records)
            if len(columns) != 64 or len(set(columns)) != 64 or header != columns:
                raise ValueError("El encabezado no coincide con los 64 campos del diccionario")
            count = 0
            for count, row in enumerate(records, 1):
                if len(row) != len(header):
                    raise ValueError(f"Longitud de fila inesperada en registro {count}")
                signature = tuple(row)
                duplicates += signature in seen
                seen.add(signature)
                record = dict(zip(columns, row))
                for column, value in record.items():
                    observed[column][value] += 1
                for keys in GEOGRAPHIES:
                    code = tuple(record[key] for key in keys)
                    if code not in geographic_keys:
                        geography_gaps[keys[0]]["/".join(code)] += 1
                state = by_state[record["ent_regis"]]
                state["registros"] += 1
                state[f"tramite_{record['tipo_div']}"] += 1
                state[f"custodia_{record['custodia']}"] += 1
                if record["tipo_div"] == "1" and record["hij_men"] in POSITIVE_COUNTS:
                    custody = record["custodia"]
                    if custody in {"1", "2"}:
                        sex = record[f"sexo_div{custody}"]
                        custody_by_sex[f"divorciante_asignado_sexo_{sex}"] += 1
                    else:
                        custody_by_sex[f"custodia_{custody}"] += 1

        outside_ranges = {}
        outside_catalogs = {}
        for column, intervals in zip(columns, ranges):
            outside = {code: n for code, n in observed[column].items() if not in_range(code, intervals)}
            if outside:
                outside_ranges[column] = outside
            if column in catalog_codes:
                outside = {
                    code: n for code, n in observed[column].items()
                    if not code.isdecimal() or int(code) not in catalog_codes[column]
                }
                if outside:
                    outside_catalogs[column] = outside

        with path.open("rb") as archive:
            sha256 = hashlib.file_digest(archive, "sha256").hexdigest()

        return {
            "anio": year,
            "fuente": SOURCE.format(year=year),
            "archivo_bytes": path.stat().st_size,
            "sha256": sha256,
            "auditoria_utc": datetime.now(timezone.utc).isoformat(),
            "integridad_zip": True,
            "registros": count,
            "variables": dictionary,
            "controles": {
                "total_inegi": count == expected_count,
                **({"custodia_rnm": observed["custodia"] == CUSTODY_REFERENCE} if year == 2024 else {}),
                "proporcion_judicial_boletin": count > 0 and round(100 * observed["tipo_div"]["1"] / count, 1) == expected_judicial,
                "32_entidades": set(by_state) == {f"{code:02d}" for code in range(1, 33)},
            },
            "filas_identicas_adicionales": duplicates,
            "fuera_de_rango": outside_ranges,
            "fuera_de_catalogo": outside_catalogs,
            "geografia_sin_coincidencia": geography_gaps,
            "por_entidad_de_registro": by_state,
            "frecuencias_por_variable": observed,
            "custodia_judicial_con_menores": custody_by_sex,
        }


POSITIVE_COUNTS = {str(number) for number in range(1, 26)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Obtener el ZIP oficial si no existe localmente")
    parser.add_argument("--year", type=int, choices=REFERENCE, default=2024)
    args = parser.parse_args()
    year = args.year
    archive = ROOT / f"data/raw/ed{year}.zip"
    report = ROOT / f"data/analytics/auditoria-ed{year}.json"
    if args.download and not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=archive.parent, suffix=".part", delete=False) as temp:
            pending = Path(temp.name)
        try:
            with urlopen(SOURCE.format(year=year), timeout=60) as response, pending.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            result = audit(pending, year)
            if not all(result["controles"].values()):
                raise ValueError("La descarga no concuerda con las cifras oficiales de referencia")
            pending.replace(archive)
        finally:
            pending.unlink(missing_ok=True)
    else:
        result = audit(archive, year)

    result["estado"] = (
        "conciliado_con_observaciones" if all(result["controles"].values()) else "no_conciliado"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['registros']:,} registros | {result['estado']} | {report}")
    return int(result["estado"] == "no_conciliado")


if __name__ == "__main__":
    raise SystemExit(main())
