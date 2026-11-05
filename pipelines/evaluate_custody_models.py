"""Compare custody models on audited INEGI editions, with a held-out 2025 test."""
import csv
import io
import json
from collections import Counter
from importlib.metadata import version
from zipfile import ZipFile

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from audit_ed import ROOT
from audit_ed_historica import csv_content, dbf_rows

RAW = ROOT / "data/raw"
ANALYTICS = ROOT / "data/analytics"
CLASSES = ["ambas", "hombre", "mujer"]
CATEGORICAL = ["sexo_pareja", "entidad_matrimonio"]
NUMERICAL = ["edad_aprox_a", "edad_aprox_b", "anios_matrimonio_demanda"]
FEATURES = CATEGORICAL + NUMERICAL
FIELDS = (
    "ent_regis", "tipo_div", "hij_men", "custodia", "sexo_div1", "sexo_div2",
    "nacim_div1", "nacim_div2", "anio_reg", "anio_mat", "ent_mat",
)


def source_rows(year, report, columns=FIELDS):
    if year >= 2023:
        with ZipFile(RAW / f"ed{year}.zip") as bundle:
            rows = csv_content(bundle, f"conjunto_de_datos/conjunto_de_datos_ed{year}.csv")
            header = next(rows)
            indexes = [header.index(field) for field in columns]
            for row in rows:
                yield [row[index].strip() for index in indexes]
    else:
        with ZipFile(RAW / report["archivo"]) as bundle:
            rows = dbf_rows(bundle, report["miembro"])
            fields = {name: slice(offset, offset + width) for name, _, width, offset in next(rows)}
            for row in rows:
                if row[:1] == b" ":
                    yield [row[fields[field]].strip().decode("ascii") for field in columns]


def integer(value):
    return int(value) if value.isdecimal() else -1


def difference(end, start, lower, upper):
    value = end - start
    return value if start >= 1900 and lower <= value <= upper else np.nan


def residence_codes(year):
    archive = RAW / (f"ed{year}.zip" if year >= 2023 else f"conjunto_de_datos_divorcios_{year}_csv.zip")
    with ZipFile(archive) as bundle:
        name, = [name for name in bundle.namelist() if name.startswith("catalogos/entidad_municipio_localidad_")]
        with bundle.open(name) as stream:
            rows = csv.DictReader(io.TextIOWrapper(stream, encoding="latin1"))
            return {(row["cve_ent"], row["cve_mun"]) for row in rows
                    if row["cve_loc"] == "0000" and 1 <= int(row["cve_ent"]) <= 32
                    and row["cve_mun"] not in {"000", "998", "999"}}


def residence_group(values, valid):
    first, second = tuple(values[:2]), tuple(values[2:])
    if first not in valid or second not in valid:
        return "sin-dato"
    if first == second:
        return "mismo"
    return "otro-municipio" if first[0] == second[0] else "otro-estado"


def load_records(include_residence=False):
    historic = json.loads((ANALYTICS / "auditoria-ed-historica.json").read_text(encoding="utf8"))
    coverage, records = {}, []
    residence_fields = ("ent_rhdiv1", "mun_rhdiv1", "ent_rhdiv2", "mun_rhdiv2")
    fields = FIELDS + residence_fields if include_residence else FIELDS
    for year in range(2018 if include_residence else 2017, 2026):
        if year < 2023:
            report = historic["por_anio"][str(year)]
            valid = report["coincide_total_oficial"]
        else:
            report = json.loads((ANALYTICS / f"auditoria-ed{year}.json").read_text(encoding="utf8"))
            valid = all(report["controles"].values())
        if not valid:
            raise ValueError(f"Edicion sin conciliar: {year}")
        counts = Counter()
        valid_residences = residence_codes(year) if include_residence else set()
        for state, procedure, minors, custody, sex1, sex2, birth1, birth2, demand, marriage, marriage_state, *residences in source_rows(year, report, fields):
            counts["filas"] += 1
            if procedure != "1" or not 1 <= integer(minors) <= 25:
                continue
            counts["judiciales_con_menores"] += 1
            if custody == "3":
                target = "ambas"
            elif custody in {"1", "2"}:
                recipient = sex1 if custody == "1" else sex2
                target = {"1": "hombre", "2": "mujer"}.get(recipient)
            else:
                target = None
            if target is None:
                counts[f"excluidos_custodia_{custody}"] += 1
                continue
            demand_year = integer(demand)
            if not 1900 <= demand_year <= year:
                demand_year = -1
            people = sorted((sex, integer(birth)) for sex, birth in [(sex1, birth1), (sex2, birth2)])
            ages = [difference(demand_year, birth, 12, 100) for _, birth in people]
            sex_pair = "".join(sex if sex in {"1", "2"} else "?" for sex, _ in people)
            marriage_state = marriage_state.zfill(2)
            if not 1 <= integer(marriage_state) <= 32:
                marriage_state = "?"
            counts[target] += 1
            record = [year, state.zfill(2), demand_year, target, sex_pair, marriage_state, *ages,
                      difference(demand_year, integer(marriage), 0, 90)]
            if include_residence:
                record.append(residence_group(residences, valid_residences))
            records.append(record)
        if counts["filas"] != report["registros"]:
            raise ValueError(f"Conteo anual incompatible: {year}")
        coverage[year] = counts
    columns = ["year", "state", "demand_year", "target", *FEATURES]
    if include_residence:
        columns.append("residence")
    return pd.DataFrame(records, columns=columns), coverage


def probabilities(model, frame):
    return model.predict_proba(frame[FEATURES])


def calibrate(probs, temperature):
    return softmax(np.log(np.clip(probs, 1e-12, 1)) / temperature, axis=1)


def scores(y, probs):
    actual = np.column_stack([y == name for name in CLASSES])
    predicted = np.asarray(CLASSES)[probs.argmax(axis=1)]
    calibration = {}
    for i, name in enumerate(CLASSES):
        bins = np.minimum((probs[:, i] * 10).astype(int), 9)
        error = 0
        for bucket in np.unique(bins):
            mask = bins == bucket
            error += mask.mean() * abs(probs[mask, i].mean() - actual[mask, i].mean())
        calibration[name] = float(error)
    return {
        "n": len(y), "log_loss": log_loss(y, probs, labels=CLASSES),
        "brier_multiclase": float(np.square(probs - actual).sum(axis=1).mean()),
        "exactitud": accuracy_score(y, predicted),
        "f1_macro": f1_score(y, predicted, labels=CLASSES, average="macro", zero_division=0),
        "ece_por_clase": calibration,
        "confusion": confusion_matrix(y, predicted, labels=CLASSES).tolist(),
    }


def group_scores(frame, probs, field):
    return {str(key): scores(frame.target.iloc[index].to_numpy(), probs[index])
            for key, index in frame.groupby(field).indices.items() if len(index) >= 100}


def main():
    frame, coverage = load_records()
    train = frame[frame.year.between(2018, 2022)]
    validation = frame[frame.year.between(2023, 2024)]
    test = frame[frame.year == 2025]
    baseline = train.target.value_counts(normalize=True).reindex(CLASSES).to_numpy()

    preprocessing = ColumnTransformer([
        ("category", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("number", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), NUMERICAL),
    ])
    logistic = make_pipeline(preprocessing, LogisticRegression(max_iter=250))
    catboost = CatBoostClassifier(
        iterations=240, depth=5, learning_rate=0.12, loss_function="MultiClass",
        cat_features=CATEGORICAL, random_seed=42, thread_count=4, verbose=False,
        allow_writing_files=False,
    )
    models = {"logistica": logistic, "catboost": catboost}
    validation_results, temperatures = {}, {}
    validation_results["frecuencias"] = scores(validation.target.to_numpy(), np.tile(baseline, (len(validation), 1)))
    for name, model in models.items():
        model.fit(train[FEATURES], train.target)
        if list(model.classes_) != CLASSES:
            raise ValueError(f"Orden de clases inesperado: {name}")
        raw = probabilities(model, validation)
        temperature = minimize_scalar(
            lambda t: log_loss(validation.target, calibrate(raw, t), labels=CLASSES),
            bounds=(0.3, 3), method="bounded",
        ).x
        temperatures[name] = float(temperature)
        validation_results[name] = scores(validation.target.to_numpy(), calibrate(raw, temperature))
        print(name, validation_results[name]["log_loss"], flush=True)
    selected = min(models, key=lambda name: validation_results[name]["log_loss"])

    test_probs = {"frecuencias": np.tile(baseline, (len(test), 1))}
    for name, model in models.items():
        test_probs[name] = calibrate(probabilities(model, test), temperatures[name])
    test_results = {name: scores(test.target.to_numpy(), probs) for name, probs in test_probs.items()}
    new_demands = (test.demand_year == 2025).to_numpy()
    sensitivity = {
        name: scores(test.target.to_numpy()[new_demands], probs[new_demands])
        for name, probs in test_probs.items()
    }
    chosen = test_results[selected]
    improvement = 1 - chosen["log_loss"] / test_results["frecuencias"]["log_loss"]
    gate = {
        "reduccion_log_loss_al_menos_1_por_ciento": improvement >= 0.01,
        "ece_por_clase_hasta_3_puntos": max(chosen["ece_por_clase"].values()) <= 0.03,
        "mejora_en_demandas_2025": sensitivity[selected]["log_loss"] < sensitivity["frecuencias"]["log_loss"],
    }

    sample = test[FEATURES].sample(n=400, random_state=42)
    shap = catboost.get_feature_importance(Pool(sample, cat_features=CATEGORICAL), type="ShapValues")
    importance = dict(zip(FEATURES, np.abs(shap[:, :, :-1]).mean(axis=(0, 1)).tolist()))
    report = {
        "versiones": {package: version(package) for package in ("numpy", "pandas", "scikit-learn", "catboost", "scipy")},
        "orden_clases": CLASSES, "cobertura_por_anio": coverage,
        "ediciones_excluidas_del_entrenamiento": {"2017": "Ruptura en la distribucion por sexo del destinatario"},
        "periodos": {"entrenamiento": [2018, 2022], "calibracion_y_seleccion": [2023, 2024], "prueba": [2025]},
        "n": {"entrenamiento": len(train), "validacion": len(validation), "prueba": len(test)},
        "temperaturas": temperatures, "validacion": validation_results, "modelo_seleccionado": selected,
        "prueba": test_results, "prueba_demandas_2025": sensitivity, "mejora_relativa_log_loss": improvement,
        "criterios_exploratorios": gate,
        "prueba_por_entidad": group_scores(test, test_probs[selected], "state"),
        "prueba_por_composicion_sexo": group_scores(test, test_probs[selected], "sexo_pareja"),
        "shap_catboost_media_absoluta": importance,
    }
    (ANALYTICS / "laboratorio-custodia.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf8",
    )
    print(selected, improvement, gate, flush=True)


if __name__ == "__main__":
    main()
