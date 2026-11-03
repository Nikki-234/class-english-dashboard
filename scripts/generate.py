#!/usr/bin/env python3
"""
Class English Dashboard Generator
从成绩表 xlsx 生成单文件 HTML 班级英语学习仪表盘。

用法:
  python3 scripts/generate.py <成绩表.xlsx> <输出.html> [--title "自定义标题"] [--class-name "高二(5)班"]

成绩表 xlsx 格式见 references/roster-schema.md

依赖: openpyxl (pip install openpyxl)
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from collections import Counter

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("缺少依赖 openpyxl,请先运行: pip3 install openpyxl")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATE_PATH = os.path.join(SKILL_DIR, "assets", "dashboard-template.html")

PLACEHOLDER = "/*STUDENT_DATA_PLACEHOLDER*/"

# 分项列在成绩表中的位置(0-indexed)
COL_ID, COL_NAME, COL_TIER = 0, 1, 2
COL_SCORE, COL_TARGET = 3, 4
COL_VOCAB, COL_VOCAB_T = 5, 6
COL_L, COL_L_T = 7, 8
COL_R, COL_R_T = 9, 10
COL_W, COL_W_T = 11, 12
COL_WEAK = 13


def split_score(text):
    """'23/30' -> (23, 30)"""
    if text is None:
        return 0, 0
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)", str(text))
    if not m:
        return 0, 0
    return int(m.group(1)), int(m.group(2))


def find_header_row(ws):
    """找到表头行(含 'ID' 和 'Name' 的那行),返回 1-indexed 行号."""
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 20), values_only=True):
        cells = [str(c).strip() if c is not None else "" for c in row]
        if any(c.upper() == "ID" for c in cells) and any(
            c.lower().startswith("name") for c in cells
        ):
            return row
    return None


def find_class_name(ws):
    """从表格标题行提取班级名称,如 '高二(5)班'。找不到则返回 None。"""
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 5), values_only=True):
        for c in row:
            if not c:
                continue
            text = str(c)
            m = re.search(r"([\u4e00-\u9fff]{1,6}\(\d+\)班|[\u4e00-\u9fff]{2,8}班)", text)
            if m:
                return m.group(1)
    return None


def read_roster(path):
    """读取成绩表 xlsx,返回 (学生列表, 自动识别的班级名)。"""
    wb = load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]

    class_name = find_class_name(ws)

    header = find_header_row(ws)
    if header is None:
        raise ValueError(
            "未能在表格中找到表头行(需含 'ID' 与 'Name' 两列)。"
            "请检查成绩表格式,参考 references/roster-schema.md"
        )

    # 表头里 'ID' 所在的列偏移
    id_offset = None
    for i, c in enumerate(header):
        if c is not None and str(c).strip().upper() == "ID":
            id_offset = i
            break
    if id_offset is None:
        raise ValueError("表头缺少 'ID' 列")

    students = []
    for row in ws.iter_rows(min_row=ws.max_row, max_row=ws.max_row, values_only=True):
        pass  # placeholder to keep mypy quiet

    for row in ws.iter_rows(values_only=True):
        if row is None or id_offset >= len(row):
            continue
        rid = row[id_offset]
        if rid is None or str(rid).strip() == "":
            continue
        if not re.match(r"^[A-Za-z]*\d+$", str(rid).strip()):
            continue  # 跳过非学生行(标题/说明)

        def cell(idx, default=None):
            if idx < len(row):
                return row[idx]
            return default

        def num(idx, default=0):
            v = cell(idx)
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        L_cur, L_max = split_score(cell(COL_L))
        R_cur, R_max = split_score(cell(COL_R))
        W_cur, W_max = split_score(cell(COL_W))
        L_t, _ = split_score(cell(COL_L_T))
        R_t, _ = split_score(cell(COL_R_T))
        W_t, _ = split_score(cell(COL_W_T))

        weak = cell(COL_WEAK) or "Writing"
        weak = str(weak).strip()
        if weak not in ("Writing", "Listening", "Reading"):
            weak = "Writing"

        students.append({
            "id": str(rid).strip(),
            "name": str(cell(COL_NAME, "")).strip(),
            "tier": str(cell(COL_TIER, "B")).strip(),
            "score": num(COL_SCORE),
            "target": num(COL_TARGET),
            "vocab": num(COL_VOCAB),
            "vocab_t": num(COL_VOCAB_T, 5500),
            "L_cur": L_cur, "L_t": L_t, "L_max": L_max,
            "R_cur": R_cur, "R_t": R_t, "R_max": R_max,
            "W_cur": W_cur, "W_t": W_t, "W_max": W_max,
            "weakness": weak,
            "progress_L": 0, "progress_R": 0,
            "progress_W": 0, "progress_V": 0,
            "note": "",
        })

    if not students:
        raise ValueError("未读取到任何学生数据,请检查成绩表内容")
    return students, class_name


def analyze(students):
    """计算班级统计指标,用于控制台输出与可选的 --report。"""
    n = len(students)
    scores = [s["score"] for s in students]
    weak = Counter(s["weakness"] for s in students)
    tiers = Counter(s["tier"] for s in students)

    def rate(cur_key, max_key):
        cur = sum(s[cur_key] for s in students)
        mx = sum(s[max_key] for s in students)
        return round(cur / mx * 100, 1) if mx else 0.0

    vocab_avg = round(statistics.mean(s["vocab"] for s in students))
    bands = {
        ">=135": sum(1 for s in students if s["score"] >= 135),
        "125-134": sum(1 for s in students if 125 <= s["score"] < 135),
        "115-124": sum(1 for s in students if 115 <= s["score"] < 125),
        "<115": sum(1 for s in students if s["score"] < 115),
    }
    return {
        "n": n,
        "avg": round(statistics.mean(scores), 1),
        "median": round(statistics.median(scores), 1),
        "max": max(scores), "min": min(scores),
        "stdev": round(statistics.pstdev(scores), 1),
        "tiers": dict(tiers),
        "weakness": dict(weak),
        "bands": bands,
        "L_pct": rate("L_cur", "L_max"),
        "R_pct": rate("R_cur", "R_max"),
        "W_pct": rate("W_cur", "W_max"),
        "vocab_avg": vocab_avg,
        "vocab_pct": round(vocab_avg / 5500 * 100, 1),
    }


def build_html(template, students, title=None, class_name=None):
    """把学生数据注入模板,返回完整 HTML 字符串。"""
    if PLACEHOLDER not in template:
        raise ValueError(f"模板缺少占位符 {PLACEHOLDER}")

    html = template.replace(PLACEHOLDER, json.dumps(students, ensure_ascii=False))

    if title:
        # 替换 <title> 与 H1 标题
        html = re.sub(r"<title>.*?</title>",
                       f"<title>{title}</title>", html, count=1, flags=re.S)
        html = re.sub(r"<h1>.*?</h1>",
                       f"<h1>{title}</h1>", html, count=1, flags=re.S)
        # 副标题
        html = html.replace(
            "40 名学生 · 12 周个性化计划 · 高考目标 138 分 · 数据自动保存于本机浏览器",
            f"{len(students)} 名学生 · 12 周个性化计划 · 数据自动保存于本机浏览器",
        )
    if class_name:
        html = re.sub(r"<h1>.*?</h1>",
                       f"<h1>{class_name} · 英语学习仪表盘</h1>",
                       html, count=1, flags=re.S)

    # 顶部标题里的学生人数始终与实际一致
    html = re.sub(
        r"(\d+)\s*名学生 · 12 周个性化计划",
        f"{len(students)} 名学生 · 12 周个性化计划",
        html,
    )
    # 全局过滤按钮上的 "全部 N"
    html = re.sub(r'(data-tier="all"[^>]*>)\s*全部\s*\d+', r"\1 全部 " + str(len(students)), html)
    return html


def validate_js(html):
    """提取 <script> 用 node --check 验证语法。"""
    try:
        node = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if node.returncode != 0:
            return "SKIPPED (未安装 node)"
    except FileNotFoundError:
        return "SKIPPED (未安装 node)"

    m = re.search(r"<script>([\s\S]*?)</script>", html)
    if not m:
        return "FAILED (未找到 <script> 块)"

    tmp = os.path.join("/tmp", f"_dash_check_{os.getpid()}.js")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(m.group(1))
    try:
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        if r.returncode != 0:
            return "FAILED\n" + r.stderr
        return "OK"
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(
        description="从成绩表 xlsx 生成单文件 HTML 班级英语学习仪表盘"
    )
    ap.add_argument("roster", help="成绩表 .xlsx 路径")
    ap.add_argument("output", help="输出的 .html 路径")
    ap.add_argument("--title", help="页面标题(默认自动生成)")
    ap.add_argument("--class-name", help="班级名称,如 '高二(5)班'")
    args = ap.parse_args()

    if not os.path.exists(args.roster):
        sys.exit(f"成绩表不存在: {args.roster}")
    if not os.path.exists(TEMPLATE_PATH):
        sys.exit(f"模板不存在: {TEMPLATE_PATH}")

    print(f"[1/4] 读取成绩表: {args.roster}")
    students, auto_class = read_roster(args.roster)
    print(f"      读取到 {len(students)} 名学生")
    if auto_class:
        print(f"      识别到班级: {auto_class}")

    stats = analyze(students)
    print("[2/4] 分析完成:")
    print(f"      平均分 {stats['avg']} | 中位 {stats['median']} | "
          f"最高 {stats['max']} | 最低 {stats['min']} | σ {stats['stdev']}")
    print(f"      分数段: " + " | ".join(f"{k} {v}人" for k, v in stats["bands"].items()))
    print(f"      四项达标率: 听 {stats['L_pct']}% | 读 {stats['R_pct']}% | "
          f"写 {stats['W_pct']}% | 词 {stats['vocab_pct']}%")
    weak_desc = " | ".join(f"{k} {v}人" for k, v in sorted(stats["weakness"].items(), key=lambda x: -x[1]))
    print(f"      弱项分布: {weak_desc}")

    print(f"[3/4] 注入模板: {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    class_name = args.class_name or auto_class or "班级"
    default_title = f"{class_name} · 英语学习仪表盘"
    html = build_html(template, students, args.title or default_title, class_name)

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(args.output)
    print(f"      已写入 {args.output} ({size:,} 字节)")

    print("[4/4] 验证 JS 语法...")
    result = validate_js(html)
    print(f"      {result}")
    if result.startswith("FAILED"):
        sys.exit("JS 语法验证失败,未交付")

    print("\n完成。双击生成的 HTML 文件即可在浏览器打开。")
    print("教师可编辑单元格与进度;数据存于浏览器 localStorage,可用右下角导出 JSON 备份。")


if __name__ == "__main__":
    main()
