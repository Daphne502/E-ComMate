"""
E-ComMate 批量评测脚本
用法（在项目根目录）:
    python eval/run_eval.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 项目根目录加入 Python 路径
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from core.workflow import create_workflow  # noqa: E402


def load_test_cases(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_case(final_copy: str, image_data: dict, checks: dict) -> dict:
    """规则打分，返回各项 pass/fail"""
    results = {}

    # 1. 非空
    results["non_empty"] = bool(final_copy and final_copy.strip())

    # 2. 无失败兜底文案
    bad_phrases = checks.get("must_not_contain", ["生成出错"])
    results["no_error_phrase"] = not any(p in final_copy for p in bad_phrases)

    # 3. 长度
    max_chars = checks.get("max_chars")
    if max_chars:
        results["length_ok"] = len(final_copy) <= max_chars
    else:
        results["length_ok"] = True

    # 4. 备注关键词
    keywords = checks.get("must_contain_any", [])
    if keywords:
        results["keyword_ok"] = any(k in final_copy for k in keywords)
    else:
        results["keyword_ok"] = True

    # 5. Vision 有效
    desc = image_data.get("description", "")
    results["vision_ok"] = desc not in ("", "图片解析失败", "未知商品")

    # 综合
    results["passed"] = all(results.values())
    return results


def run_one_case(workflow, case: dict) -> dict:
    image_path = case["image_path"]
    if not os.path.exists(image_path):
        return {
            "id": case["id"],
            "passed": False,
            "error": f"图片不存在: {image_path}",
        }

    inputs = {
        "image_path": image_path,
        "user_style": case["user_style"],
        "words_limit": str(case["words_limit"]),
        "user_note": case.get("user_note", ""),
        "image_data": {},
        "retrieved_examples": [],
        "final_copy": "",
        "timings": {},
    }

    t0 = time.perf_counter()
    try:
        result = workflow.invoke(inputs)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
    except Exception as e:
        return {
            "id": case["id"],
            "passed": False,
            "error": str(e),
        }

    final_copy = result.get("final_copy", "")
    image_data = result.get("image_data", {})
    timings = result.get("timings", {})
    checks = case.get("checks", {})
    check_results = check_case(final_copy, image_data, checks)

    return {
        "id": case["id"],
        "user_style": case["user_style"],
        "user_note": case.get("user_note", ""),
        "passed": check_results["passed"],
        "checks": check_results,
        "copy_preview": final_copy[:80] + ("..." if len(final_copy) > 80 else ""),
        "timings": timings,
        "elapsed_ms": elapsed_ms,
    }


def summarize(results: list) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    errors = [r for r in results if "error" in r]

    avg_elapsed = 0
    avg_retrieve = 0
    valid = [r for r in results if "elapsed_ms" in r]
    if valid:
        avg_elapsed = sum(r["elapsed_ms"] for r in valid) // len(valid)
        retrieves = [r["timings"].get("retrieve_ms", 0) for r in valid if r.get("timings")]
        if retrieves:
            avg_retrieve = sum(retrieves) // len(retrieves)

    return {
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "error_cases": len(errors),
        "avg_elapsed_ms": avg_elapsed,
        "avg_retrieve_ms": avg_retrieve,
    }


def main():
    cases_path = ROOT / "eval" / "test_cases.json"
    report_path = ROOT / "eval" / "eval_report.json"

    print(f"加载测试用例: {cases_path}")
    cases = load_test_cases(cases_path)
    print(f"共 {len(cases)} 条，开始评测...\n")

    workflow = create_workflow()
    results = []

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] 运行 {case['id']} ({case['user_style']}) ...")
        result = run_one_case(workflow, case)
        status = "PASS" if result.get("passed") else "FAIL"
        print(f"    -> {status}")
        if not result.get("passed") and result.get("checks"):
            failed = [k for k, v in result["checks"].items() if k != "passed" and not v]
            print(f"    失败项: {failed}")
        results.append(result)

    summary = summarize(results)
    report = {
        "project": "E-ComMate",
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "results": results,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n========== 评测摘要 ==========")
    print(f"通过率: {summary['pass_rate']}% ({summary['passed_cases']}/{summary['total_cases']})")
    print(f"平均耗时: {summary['avg_elapsed_ms']} ms")
    print(f"平均 retrieve_ms: {summary['avg_retrieve_ms']} ms")
    print(f"报告已写入: {report_path}")


if __name__ == "__main__":
    main()