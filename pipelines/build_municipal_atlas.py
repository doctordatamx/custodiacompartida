"""Join audited divorce registrations to the matching INEGI municipal maps."""
import argparse
import csv
import io
import json
from collections import Counter, defaultdict
from urllib.parse import urlencode
from urllib.request import urlopen
from zipfile import ZipFile

from shapely.geometry import shape

from audit_ed import ROOT

RAW = ROOT / "data/raw"
PUBLIC = ROOT / "web/public/atlas"
THRESHOLD = 5
HOST = "https://lcidsig.inegi.org.mx/server/rest/services/Hosted"
LAYERS = {2024: "%C3%81reas_geoestad%C3%ADsticas_municipales_2024", 2025: "Municipios_2025"}


def load_geometry(year, download):
    features = {}
    for part in (1, 2):
        path = RAW / f"municipios-{year}-{part}.geojson"
        downloading = download and not path.exists()
        if downloading:
            operator = "<=" if part == 1 else ">"
            query = urlencode({
                "where": f"cve_ent {operator} '16'",
                "outFields": "cvegeo,cve_ent,cve_mun,nomgeo",
                "outSR": 4326,
                "maxAllowableOffset": 0.001,
                "geometryPrecision": 4,
                "f": "geojson",
            })
            with urlopen(f"{HOST}/{LAYERS[year]}/FeatureServer/0/query?{query}", timeout=90) as response:
                payload = response.read()
        else:
            payload = path.read_bytes()
        source = json.loads(payload)
        if source.get("type") != "FeatureCollection" or source.get("exceededTransferLimit"):
            raise ValueError(f"Respuesta cartografica incompleta: {part}")
        for feature in source["features"]:
            props = feature["properties"]
            code = props["cvegeo"]
            if code in features or code != props["cve_ent"] + props["cve_mun"]:
                raise ValueError(f"Clave cartografica invalida: {code}")
            if feature["geometry"]["type"] not in {"Polygon", "MultiPolygon"}:
                raise ValueError(f"Geometria no municipal: {code}")
            features[code] = feature
        if downloading:
            path.write_bytes(payload)
    if len(features) != 2478:
        raise ValueError(f"El Marco Geoestadistico {year} debe contener 2478 municipios: {len(features)}")
    return features


def annual_indicators(year, features):
    totals, eligible, both = Counter(), Counter(), Counter()
    with ZipFile(RAW / f"ed{year}.zip") as bundle:
        with bundle.open(f"catalogos/entidad_municipio_localidad_{year}.csv") as raw:
            catalog = {
                row["cve_ent"] + row["cve_mun"] for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))
                if row["cve_loc"] == "0000"
            }
        with bundle.open(f"conjunto_de_datos/conjunto_de_datos_ed{year}.csv") as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")):
                code = row["ent_regis"] + row["mun_regis"]
                totals[code] += 1
                if row["tipo_div"] == "1" and 1 <= int(row["hij_men"]) <= 25:
                    eligible[code] += 1
                    both[code] += row["custodia"] == "3"
    audit = json.loads((ROOT / f"data/analytics/auditoria-ed{year}.json").read_text(encoding="utf8"))
    if not all(audit["controles"].values()):
        raise ValueError(f"La auditoria de {year} no esta conciliada")
    state_totals = Counter()
    for code, count in totals.items():
        state_totals[code[:2]] += count
    expected = {state: row["registros"] for state, row in audit["por_entidad_de_registro"].items()}
    if state_totals != expected:
        raise ValueError("Los microdatos municipales no concuerdan con el total estatal auditado")

    indicators = {}
    unmatched = totals.keys() - (features.keys() & catalog)
    print("Claves sin correspondencia", {code: totals[code] for code in sorted(unmatched)})
    suppressed = {code for code, count in totals.items() if 0 < count < THRESHOLD}
    for state in expected:
        hidden = [code for code in (suppressed | unmatched) if code.startswith(state)]
        if len(hidden) == 1:
            candidates = [code for code in totals if code.startswith(state) and code not in hidden]
            if candidates:
                suppressed.add(min(candidates, key=lambda code: (totals[code], code)))

    visible_custody = {
        code for code in features.keys() & catalog - suppressed
        if min(both[code], eligible[code] - both[code]) >= THRESHOLD
    }
    for state in expected:
        hidden = [code for code in eligible.keys() - visible_custody if code.startswith(state)]
        candidates = [code for code in visible_custody if code.startswith(state)]
        if len(hidden) == 1 and candidates:
            visible_custody.remove(min(candidates, key=lambda code: (eligible[code], code)))

    for code in features:
        available = code in catalog
        count = totals[code]
        share = None
        if code in visible_custody:
            share = round(100 * both[code] / eligible[code], 1)
        indicators[code] = {
            "total": count if available and code not in suppressed else None,
            "share": share,
            "both": both[code] if share is not None else None,
            "eligible": eligible[code] if share is not None else None,
            "matched": available,
        }
    if {code[:2] for code in features} != expected.keys():
        raise ValueError("Cobertura estatal de la cartografia incompleta")
    print(f"{year}: {len(features)} poligonos, {sum(totals.values())} registros, {len(suppressed)} claves con conteo reservado")
    return indicators


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Descarga las partes cartograficas faltantes")
    args = parser.parse_args()
    geometry = {year: load_geometry(year, args.download) for year in LAYERS}
    annual = {year: annual_indicators(year, features) for year, features in geometry.items()}
    comparable = {
        code for code in geometry[2024].keys() & geometry[2025].keys()
        if shape(geometry[2024][code]["geometry"]).equals_exact(
            shape(geometry[2025][code]["geometry"]), 0, normalize=True
        )
    }
    for year, features in geometry.items():
        grouped = defaultdict(list)
        for code, feature in features.items():
            earlier = annual[2024].get(code)
            later = annual[2025].get(code)
            stable = code in comparable
            comparison = {}
            for metric in ("total", "share"):
                before = earlier[metric] if earlier else None
                after = later[metric] if later else None
                comparison[f"{metric}Change"] = (
                    round(after - before, 1) if stable and before is not None and after is not None else None
                )
            feature["properties"] = {
                "code": code,
                "name": feature["properties"]["nomgeo"],
                **annual[year][code],
                **comparison,
                "comparable": stable,
                "otherYear": later if year == 2024 else earlier,
            }
            grouped[code[:2]].append(feature)
        destination = PUBLIC if year == 2025 else PUBLIC / str(year)
        destination.mkdir(parents=True, exist_ok=True)
        for state, items in grouped.items():
            (destination / f"{state}.geojson").write_text(
                json.dumps({"type": "FeatureCollection", "features": items}, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
    print(f"{len(comparable)} claves con geometria comparable")


if __name__ == "__main__":
    main()
