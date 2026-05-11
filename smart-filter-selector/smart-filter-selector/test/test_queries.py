import json
import logging
from difflib import SequenceMatcher
from pandas import DataFrame

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def similar(a: str, b: str) -> float:
    """Returns a similarity ratio between two strings."""
    return round(SequenceMatcher(None, a.lower(), b.lower()).ratio(), 2)

def compare_filters(detected, expected):
    """
    Compare detected vs expected filters (case-insensitive fuzzy match).
    Returns (true_positives, false_positives, false_negatives)
    """
    tp, fp, fn = [], [], []

    detected_lower = [d.lower().replace(" ", "") for d in detected]
    expected_lower = [e.lower().replace(" ", "") for e in expected]

    for e in expected_lower:
        if any(similar(e, d) >= 0.9 for d in detected_lower):
            tp.append(e)
        else:
            fn.append(e)

    for d in detected_lower:
        if not any(similar(d, e) >= 0.9 for e in expected_lower):
            fp.append(d)

    return tp, len(tp), fp, len(fp), fn, len(fn)

def precision_recall_f1(detected, expected):
    """
        Compute precision, recall, and F1-score.
            Precision:
                * “Of all the filters the model selected, how many were actually correct?”
                * how clean the filter selection is (few wrong filters).

            Recall:
                * “Of all the correct filters that exist, how many did the model find?”
                * how complete it is (few missing filters).

            F1-score:
                * “A balance between precision and recall.”
                * combined efficiency.
    """
    tp, tp_count, fp, fp_count, fn, fn_count = compare_filters(detected, expected)
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return round(precision, 2), round(recall, 2), round(f1, 2)


def main():
    results = []

    with open('test/test_queries.json', 'r') as f:
        test_queries = json.load(f)
        # test_queries = [
        #     {
        #         "query": "We’re designing the civil engineering layout for railway infrastructure.",
        #         "language": "en",
        #         "expected": ["Infrastructure", "Fixed Installations / Civil Engineering"]
        #     },
        #     {
        #         "query": "Le système SCADA contrôle la distribution électrique.",
        #         "language": "fr",
        #         "expected": ["SCADA", "Energy", "Electrical Systems"]
        #     },
        #     {
        #         "query": "We are developing a SCADA system for industrial automation.",
        #         "language": "en",
        #         "expected": ["Automation", "SCADA"]
        #     },
        #     {
        #         "query": "We’re testing the safety of railway communication systems.",
        #         "language": "en",
        #         "expected": ["Railway", "Safety", "Communication"]
        #     },
        #     {
        #         "query": "Nous concevons un système de cybersécurité pour les réseaux ferroviaires.",
        #         "language": "fr",
        #         "expected": ["Cybersecurity", "Railway", "Network"]
        #     },
        # ]
        logger.info(f"🔍 Running Smart Filter Selector tests, Number of tests: {len(test_queries)}...\n")

        for i, test in enumerate(test_queries, start=1):
            logger.info(f"🧠 [{i}] Testing query ({test['language']}): {test['query']}")
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/api/filter/analyze-query",
                    headers={"Content-Type": "application/json"},
                    json={"query": test["query"]},
                    timeout=200
                )

                if response.status_code != 200:
                    logger.info(f" ❌ API Error {response.status_code}: {response.text}\n")
                    continue

                data = response.json()
                detected_filters = list(
                    set(f["name"] for f in data.get("reducedFilters", [])).union(
                        set(f["subcategory"] for f in data.get("reducedFilters", []) if f.get("subcategory"))
                ))

                precision, recall, f1 = precision_recall_f1(
                    detected_filters,
                    test["expected"]
                )

                response_time = round(sum(float(str(v).replace('s', '')) for v in data.get('stages', {}).values()), 2)
                results.append(
                    {
                        "Query": test["query"],
                        "Translated query": data.get("translatedQuery", ""),
                        "Calculation Time (s)": response_time,
                        "Detected filters": '\n'.join(detected_filters),
                        "Expected_filters": '\n'.join(test["expected"]),
                        "Precision": precision,
                        "Recall": recall,
                        "F1": f1
                    }
                )
                logger.info(f"   ⏱ Response time: {response_time}s")
                logger.info(f"   ✅ Expected: {test['expected']}")
                logger.info(f"   🧩 Detected: {detected_filters}")
                logger.info(f"   📊 Precision: {precision}, Recall: {recall}, F1: {f1}\n")

            except Exception as e:
                logger.info(f" ❌ Exception: {e}\n")

    return results


if __name__ == "__main__":
    results = main()
    # INFO:__main__:📈 SUMMARY REPORT: Average Precision: 0.71, Average Recall: 0.92, Average F1-score: 0.78
    if results:
        avg_precision = round(sum(r["Precision"] for r in results) / len(results), 2)
        avg_recall = round(sum(r["Recall"] for r in results) / len(results), 2)
        avg_f1 = round(sum(r["F1"] for r in results) / len(results), 2)

        logger.info(f"📈 SUMMARY REPORT: Average Precision: {avg_precision}, Average Recall: {avg_recall}, Average F1-score: {avg_f1}")

        # Save results to Excel file
        excel_path = "test/test_queries_results.xlsx"
        DataFrame(results).to_excel(excel_path, index=False)
        logger.info(f"📊 Results saved to {excel_path}")
    else:
        logger.info("⚠️ No valid responses were tested.")
