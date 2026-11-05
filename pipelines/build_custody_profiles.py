"""Build public counts for the retrospective custody profiler."""
import json

from evaluate_custody_models import CLASSES, ROOT, load_records

OUTPUT = ROOT / "web/public/perfiles-custodia.json"
MIN_CASES = 100
MIN_PER_CLASS = 10


def main():
    records, _ = load_records(include_residence=True)
    records = records.loc[records.year.between(2018, 2025) & records.sexo_pareja.eq("12")].copy()
    records = records.dropna(subset=["edad_aprox_a", "edad_aprox_b", "anios_matrimonio_demanda"])
    younger = records[["edad_aprox_a", "edad_aprox_b"]].min(axis=1)
    records["age"] = (younger >= 30).astype(int) + (younger >= 40).astype(int)
    duration = records.anios_matrimonio_demanda
    records["duration"] = (duration >= 5).astype(int) + (duration >= 10).astype(int)
    records["period"] = records.year.ge(2023).astype(int)
    groups = ["period", "age", "duration"]
    by_residence = records.groupby([*groups, "state", "residence", "target"]).size().unstack(fill_value=0)
    by_residence = by_residence.reindex(columns=CLASSES, fill_value=0)
    counts = by_residence.groupby(level=[*groups, "state"]).sum()
    published = {}
    for (period, age, duration), subset in counts.groupby(level=groups):
        national = [int(count) for count in subset.sum()]
        visible = {}
        hidden = 0
        for (_, _, _, state), row in subset.iterrows():
            values = [int(count) for count in row]
            if sum(values) >= MIN_CASES and min(values) >= MIN_PER_CLASS:
                visible[state] = values
            else:
                hidden += 1
        # Avoid exposing a single withheld state by subtraction from the national row.
        if hidden == 1 and visible:
            visible.pop(min(visible, key=lambda state: (sum(visible[state]), state)))
        if sum(national) >= MIN_CASES and min(national) >= MIN_PER_CLASS:
            visible["00"] = national
        for state, values in visible.items():
            published[f"{period}:{state}:{age}:{duration}"] = values
        detail = by_residence.loc[(period, age, duration)]
        eligible_by_state = {}
        for state, rows in detail.groupby(level="state"):
            eligible = {
                index: [int(count) for count in row] for index, row in rows.iterrows()
                if sum(row) >= MIN_CASES and min(row) >= MIN_PER_CLASS
            }
            if len(rows) - len(eligible) == 1 and eligible:
                eligible.pop(min(eligible, key=lambda index: (sum(eligible[index]), index)))
            eligible_by_state[state] = eligible

        # Two states reserved across all categories prevent national margins
        # from revealing withheld cells by subtraction.
        national_residence = detail.groupby(level="residence").sum()
        reserve_candidates = [
            state for state, rows in detail.groupby(level="state")
            if len(rows) == len(national_residence)
        ]
        can_publish_national = (
            len(reserve_candidates) >= 2
            and all(sum(row) >= MIN_CASES and min(row) >= MIN_PER_CLASS for _, row in national_residence.iterrows())
        )
        if can_publish_national:
            reserve_candidates.sort(key=lambda state: (len(eligible_by_state[state]), state))
            for state in reserve_candidates[:2]:
                eligible_by_state.pop(state)
            for residence, row in national_residence.iterrows():
                published[f"{period}:00:{age}:{duration}:{residence}"] = [int(count) for count in row]
        for eligible in eligible_by_state.values():
            for (state, residence), values in eligible.items():
                published[f"{period}:{state}:{age}:{duration}:{residence}"] = values
    OUTPUT.write_text(json.dumps(published, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf8")
    print(f"{len(records):,} registros completos; {len(published)} perfiles disponibles")


if __name__ == "__main__":
    main()
