"""Audit the historical ED packages listed by the public INEGI catalog."""
import argparse
import csv
import hashlib
import io
import json
import re
import struct
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from audit_ed import GEOGRAPHIES, ROOT, in_range, parse_ranges

RAW = ROOT / "data/raw"
OUTPUT = ROOT / "data/analytics"
HOST = "https://www.inegi.org.mx/contenidos"
INDEX_URL = (
    "https://www.inegi.org.mx/app/api/descarga/componente/descargamasiva/lista/archivoscompaginacion"
    "?tema=0&subtema=0&areaGeografica=0&proyecto=0&anio=0&tipodocto={category}"
    "&agrupacion=VG9kYXM%3D&idBiinegi=3356&desde=1&hasta=200&textoBuscar="
    "&ordenar=orden&ingles=0&datosAbiertos=0&orden="
)
# INEGI: Anuario 1996 (2.11), Anuario 2019 (2.14), ED 2023 (graph 1).
REFERENCE = dict(enumerate((
    34114, 38827, 45323, 47464, 46039, 46481, 50001, 51953, 32483, 35029,
    37455, 38545, 40792, 45889, 49271, 52358, 57370, 60641, 64248, 67575,
    70184, 72396, 77255, 81851, 84302, 86042, 91285, 99509, 108727,
    113478, 123883, 139807, 147581, 156556, 160107, 92739, 149675, 166766,
), 1985))
LEGACY_RESIDENCE = (
    ("ent_resel", "mun_resel", "loc_rhel"),
    ("ent_resla", "mun_resla", "loc_rhla"),
)
KEY_FIELDS = {
    "tipo_div", "custodia", "cus_hij", "pat_pot", "pat_hij", "pension", "pen_hij",
    "hijos", "hij_men", "sexo_div1", "sexo_div2", "t_dvante", "anio_eje",
}


def dbf_rows(bundle, name):
    with bundle.open(name) as stream:
        header = stream.read(32)
        count, header_size, row_size = struct.unpack_from("<IHH", header, 4)
        descriptors = stream.read(header_size - 32)
        fields = []
        offset = 1
        for index in range(0, len(descriptors), 32):
            if descriptors[index] == 13:
                break
            field = descriptors[index:index + 32]
            label = field[:11].split(b"\0")[0].decode("ascii").lower()
            length = field[16]
            fields.append((label, chr(field[11]), length, offset))
            offset += length
        if offset != row_size or len({field[0] for field in fields}) != len(fields):
            raise ValueError(f"Invalid DBF layout: {name}")
        yield fields
        for index in range(count):
            row = stream.read(row_size)
            if len(row) != row_size or row[:1] not in {b" ", b"*"}:
                raise ValueError(f"Invalid row {index + 1}: {name}")
            yield row
        if stream.read() not in {b"", b"\x1a"}:
            raise ValueError(f"Unexpected bytes after DBF records: {name}")


def csv_content(bundle, name):
    with bundle.open(name) as stream:
        with io.TextIOWrapper(stream, encoding="utf-8-sig", newline="") as handle:
            yield from csv.reader(handle, strict=True)


def audit_dbf(bundle, name, geo_members):
    rows = dbf_rows(bundle, name)
    fields = next(rows)
    lookup = {label: (offset, offset + length) for label, _, length, offset in fields}
    if "ent_regis" not in lookup:
        raise ValueError(f"Missing state field: {name}")

    def value(row, label):
        start, end = lookup[label]
        return row[start:end].strip().decode("ascii")

    keys = set()
    geography_width = 0
    if len(geo_members) == 1:
        catalog = dbf_rows(bundle, geo_members[0])
        catalog_fields = {label: (offset, offset + length) for label, _, length, offset in next(catalog)}
        if {"cve_ent", "cve_mun"} <= catalog_fields.keys():
            labels = [label for label in ("cve_ent", "cve_mun", "cve_loc") if label in catalog_fields]
            geography_width = len(labels)
            spans = [catalog_fields[label] for label in labels]
            keys = {tuple(row[a:b].strip().decode("ascii") for a, b in spans)
                    for row in catalog if row[:1] == b" "}

    tracked = sorted(KEY_FIELDS & lookup.keys())
    counts = {label: Counter() for label in tracked}
    states = defaultdict(Counter)
    geography = [labels[:geography_width] for labels in (*GEOGRAPHIES, *LEGACY_RESIDENCE) if keys]
    gaps = {labels[0]: Counter() for labels in geography if all(k in lookup for k in labels)}
    seen = set()
    total = duplicates = deleted = 0
    for row in rows:
        if row[:1] == b"*":
            deleted += 1
            continue
        total += 1
        duplicates += row in seen
        seen.add(row)
        state = states[value(row, "ent_regis").zfill(2)]
        state["registros"] += 1
        for label in tracked:
            code = value(row, label)
            counts[label][code] += 1
            if label in {"tipo_div", "custodia"}:
                state[f"{label}_{code}"] += 1
        for labels in geography:
            if labels[0] in gaps:
                code = tuple(value(row, label).zfill(width) for label, width in zip(labels, (2, 3, 4)))
                if code not in keys:
                    gaps[labels[0]]["/".join(code)] += 1
    return {
        "registros": total, "filas_marcadas_borradas": deleted,
        "filas_identicas_adicionales": duplicates, "por_entidad_de_registro": states,
        "campos": [{"nombre": label, "tipo": kind, "ancho": length} for label, kind, length, _ in fields],
        "frecuencias_clave": counts, "catalogo_geografico": geo_members,
        "nivel_catalogo_geografico": geography_width, "geografia_sin_coincidencia": gaps,
    }


def audit_csv(bundle, name, dbf):
    rows = csv_content(bundle, name)
    header = [column.strip().lower() for column in next(rows)]
    if len(header) != len(set(header)):
        raise ValueError(f"Duplicate CSV headers: {name}")
    indexes = {label: header.index(label) for label in dbf["frecuencias_clave"] if label in header}
    state_index = header.index("ent_regis")
    counts = {label: Counter() for label in indexes}
    states = Counter()
    total = 0
    for total, row in enumerate(rows, 1):
        if len(row) != len(header):
            raise ValueError(f"Invalid CSV width: {name}, row {total}")
        states[row[state_index].strip().zfill(2)] += 1
        for label, index in indexes.items():
            counts[label][row[index].strip()] += 1
    dictionary_name, = [member for member in bundle.namelist()
                        if member.lower().startswith("diccionario_de_datos/") and member.lower().endswith(".csv")]
    dictionary_bytes = bundle.read(dictionary_name)
    try:
        dictionary_text = dictionary_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        dictionary_text = dictionary_bytes.decode("cp1252")
    dictionary = [field for field in csv.DictReader(io.StringIO(dictionary_text)) if field["nemonico"]]
    range_exceptions = {}
    for field in dictionary:
        label = field["nemonico"].strip().lower()
        if label in counts:
            intervals = parse_ranges(field["rango_claves"].replace("\u2026", ".."))
            exceptions = {code: n for code, n in counts[label].items() if not in_range(code, intervals)}
            if exceptions:
                range_exceptions[label] = exceptions
    dbf_states = {code: values["registros"] for code, values in dbf["por_entidad_de_registro"].items()}
    return {
        "registros": total, "campos": header, "total_coincide_dbf": total == dbf["registros"],
        "encabezado_coincide_diccionario": header == [field["nemonico"].strip().lower() for field in dictionary],
        "fuera_de_rango_campos_clave": range_exceptions,
        "entidades_coinciden_dbf": states == dbf_states,
        "frecuencias_clave_coinciden_dbf": {
            label: counts[label] == dbf["frecuencias_clave"][label] for label in counts
        },
    }


def packages(category):
    inventory = json.loads((RAW / f"indice-ed-{category}.json").read_text(encoding="utf-8-sig"))
    for item in inventory:
        first, last = item["anioInformacion"].split("|")
        end = int(last)
        if end > 2022:
            continue
        logical = item["pathLogico"]
        suffix = item["formato"].split("&")[0]
        yield range(int(first or last), end + 1), RAW / (Path(logical).name + suffix), HOST + logical + suffix


def manifest(path, url, bundle):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    bad = bundle.testzip()
    if bad:
        raise ValueError(f"CRC mismatch: {bad}")
    return {"url": url, "archivo": path.name, "bytes": path.stat().st_size,
            "sha256": digest, "crc_correcto": True, "miembros": bundle.namelist()}


def download(path, url):
    with NamedTemporaryFile(dir=RAW, suffix=".part", delete=False) as temporary:
        pending = Path(temporary.name)
    try:
        with urlopen(url, timeout=90) as response, pending.open("wb") as stream:
            copyfileobj(response, stream)
        if path.suffix == ".zip":
            with ZipFile(pending) as bundle:
                bad = bundle.testzip()
                if bad:
                    raise ValueError(f"CRC mismatch: {bad}")
        else:
            json.loads(pending.read_text(encoding="utf-8-sig"))
        pending.replace(path)
    finally:
        pending.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Descarga el inventario y los ZIP faltantes")
    args = parser.parse_args()
    if args.download:
        RAW.mkdir(parents=True, exist_ok=True)
        for category in (4, 12):
            index = RAW / f"indice-ed-{category}.json"
            if not index.exists():
                download(index, INDEX_URL.format(category=category))
            for _, path, url in packages(category):
                if not path.exists():
                    download(path, url)
    audits = {}
    manifests = []
    missing = []
    for years, path, url in packages(4):
        if not path.exists():
            missing.append(url)
            continue
        with ZipFile(path) as bundle:
            manifests.append(manifest(path, url, bundle))
            for year in years:
                names = bundle.namelist()
                pattern = rf"divor(?:{year}|{year % 100:02d})\.dbf"
                candidates = [name for name in names if re.fullmatch(pattern, Path(name).name, re.I)]
                if len(candidates) != 1:
                    raise ValueError(f"Cannot locate annual DBF for {year}: {names}")
                parent = Path(candidates[0]).parent
                geo = [name for name in names if Path(name).parent == parent and
                       re.fullmatch(r"(?:catemld[a-z]*\d{2}|entmun)\.dbf", Path(name).name, re.I)]
                report = audit_dbf(bundle, candidates[0], geo)
                expected = REFERENCE.get(year)
                report.update({"archivo": path.name, "miembro": candidates[0], "total_oficial": expected,
                               "coincide_total_oficial": None if expected is None else report["registros"] == expected})
                audits[year] = report
                print(year, report["registros"], flush=True)
    for years, path, url in packages(12):
        year = years.start
        if not path.exists():
            missing.append(url)
            continue
        with ZipFile(path) as bundle:
            manifests.append(manifest(path, url, bundle))
            candidates = [name for name in bundle.namelist() if name.lower().startswith("conjunto_de_datos/")
                          and name.lower().endswith(".csv")]
            if len(candidates) != 1:
                raise ValueError(f"Cannot locate annual CSV for {year}: {candidates}")
            if year in audits:
                audits[year]["csv"] = audit_csv(bundle, candidates[0], audits[year])
    output = {"auditoria_utc": datetime.now(timezone.utc).isoformat(),
              "archivos": manifests, "faltantes": missing, "por_anio": audits}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "auditoria-ed-historica.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return bool(missing) or set(audits) != set(REFERENCE) or any(
        not report["coincide_total_oficial"] for report in audits.values()
    )


if __name__ == "__main__":
    raise SystemExit(main())
