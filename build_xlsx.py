#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成《计算机科学与技术知识图谱 · 技术组成明细》工作簿。"""
import json
import math
import pathlib
from collections import Counter, OrderedDict

import xlsxwriter

ROOT = pathlib.Path(__file__).resolve().parent
G = json.loads((ROOT / "graph.json").read_text(encoding="utf-8"))
OUT = ROOT / "计算机科学与技术知识图谱-技术组成明细.xlsx"

NAVY = "#0F172A"
INK = "#1F2937"
MUTED = "#6B7280"
GRID = "#E5E7EB"

CAT_TINT = {
    "math": "#EDF2FF", "sys": "#FFEEF1", "sw": "#EFF8E9",
    "net": "#FFF6E5", "ai": "#F4EFFF", "app": "#E9F7FF",
}
CAT_SHORT = {c["id"]: c["short"] for c in G["categories"]}
CAT_DEEP = {c["id"]: c["color"] for c in G["categories"]}

wb = xlsxwriter.Workbook(str(OUT), {"nan_inf_to_errors": True})
wb.set_properties({
    "title": "计算机科学与技术知识图谱 — 技术组成明细",
    "subject": "学科分类 / 衍生方向 / 知识点 / 技术组成",
    "author": "DSH Knowledge Map",
    "comments": f"版本 {G['version']}，共 {G['stats']['points']} 个知识点",
})

base = {"font_name": "微软雅黑", "font_size": 10, "font_color": INK}
F = {
    "title": wb.add_format({**base, "font_size": 22, "bold": True, "font_color": NAVY}),
    "sub": wb.add_format({**base, "font_size": 11, "font_color": MUTED}),
    "h1": wb.add_format({**base, "font_size": 12, "bold": True, "font_color": NAVY}),
    "stat_n": wb.add_format({**base, "font_size": 20, "bold": True, "font_color": NAVY, "align": "center"}),
    "stat_l": wb.add_format({**base, "font_size": 9, "font_color": MUTED, "align": "center"}),
    "head": wb.add_format({**base, "bold": True, "font_color": "#FFFFFF", "bg_color": NAVY,
                           "border": 1, "border_color": NAVY, "valign": "vcenter", "text_wrap": True}),
    "cell": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "text_wrap": True,
                           "indent": 1}),
    "cell_c": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "align": "center"}),
    "num": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "align": "center",
                          "font_name": "Consolas"}),
    "cat": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "bold": True}),
    "dir": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "bold": True,
                          "indent": 1}),
    "dim": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "font_color": MUTED,
                          "text_wrap": True, "indent": 1}),
    "mono": wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top", "font_name": "Consolas",
                           "font_size": 9.5, "text_wrap": True, "indent": 1}),
    "note": wb.add_format({**base, "font_size": 10, "font_color": MUTED, "text_wrap": True, "valign": "top"}),
}

def _unused():
    return None


def units(s):
    """按显示宽度估算：中日韩字符记 2，其余记 1。"""
    return sum(2 if ord(ch) > 127 else 1 for ch in str(s))


def lines(s, width, minimum=1):
    return max(minimum, math.ceil(units(s) / max(1.0, width * 0.98)))

# ---------------------------------------------------------------- 总览
s1 = wb.add_worksheet("总览")
s1.hide_gridlines(2)
s1.set_column("A:A", 3)
s1.set_column("B:B", 22)
s1.set_column("C:C", 10)
s1.set_column("D:D", 11)
s1.set_column("E:E", 11)
s1.set_column("F:F", 11)
s1.set_column("G:G", 62)
s1.set_row(1, 34)
s1.merge_range("B2:G2", G["title"], F["title"])
s1.merge_range("B3:G3", "专业分类体系 · 衍生方向 · 每个知识点的技术组成（理论 / 语言 / 工具）", F["sub"])

st = G["stats"]
stats = [(st["categories"], "学科大类"), (st["directions"], "专业方向"),
         (st["branches"], "衍生方向"), (st["points"], "知识点"), (st["links"], "交叉衍生")]
for i, (n, label) in enumerate(stats):
    c = 1 + i
    s1.set_row(5, 26)
    s1.write(5, c, n, F["stat_n"])
    s1.write(6, c, label, F["stat_l"])

s1.write("B9", "学科大类分布", F["h1"])
s1.set_row(9, 22)
heads = ["大类", "代码", "方向", "衍生方向", "知识点", "定位与内涵"]
for i, h in enumerate(heads):
    s1.write(10, 1 + i, h, F["head"])
r = 11
for cat in G["categories"]:
    tint = wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top",
                          "bold": True, "bg_color": CAT_TINT[cat["id"]]})
    s1.write(r, 1, cat["name"], tint)
    s1.write(r, 2, cat["code"], F["num"])
    s1.write_number(r, 3, len(cat["directions"]), F["num"])
    s1.write_number(r, 4, sum(d["nBranch"] for d in cat["directions"]), F["num"])
    s1.write_number(r, 5, sum(d["nPoint"] for d in cat["directions"]), F["num"])
    s1.write(r, 6, cat["desc"], F["cell"])
    s1.set_row(r, 42)
    r += 1

chart = wb.add_chart({"type": "bar"})
chart.add_series({
    "name": "知识点数量",
    "categories": ["总览", 11, 1, r - 1, 1],
    "values": ["总览", 11, 5, r - 1, 5],
    "fill": {"color": "#7AA2F7"},
    "border": {"none": True},
    "data_labels": {"value": True, "font": {"size": 9, "color": INK}},
})
chart.set_title({"name": "各学科大类知识点数量", "name_font": {"size": 11, "bold": True, "color": NAVY}})
chart.set_legend({"none": True})
chart.set_size({"width": 430, "height": 240})
chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
chart.set_plotarea({"border": {"none": True}})
chart.set_y_axis({"reverse": True, "line": {"none": True}, "major_gridlines": {"visible": False},
                  "num_font": {"size": 9}})
chart.set_x_axis({"line": {"none": True}, "major_gridlines": {"visible": True, "line": {"color": "#F1F3F7"}},
                  "num_font": {"size": 9}})
s1.insert_chart("B19", chart, {"x_offset": 6, "y_offset": 8})

s1.set_row(33, 30)
s1.merge_range("B34:G34", "阅读方式：总览 → 方向总览 → 知识点明细。每个知识点均给出「理论与方法 / 编程语言 / 框架·工具·平台」三层技术组成；"
                          "「技术栈索引」可反查任一技术被哪些方向使用。", F["note"])

# ---------------------------------------------------------------- 方向总览
s2 = wb.add_worksheet("方向总览")
s2.hide_gridlines(2)
s2.freeze_panes(1, 0)
s2.set_column("A:A", 5)
s2.set_column("B:B", 20)
s2.set_column("C:C", 24)
s2.set_column("D:D", 34)
s2.set_column("E:E", 50)
s2.set_column("F:F", 10)
s2.set_column("G:G", 10)
s2.set_column("H:H", 10)
heads2 = ["#", "学科大类", "专业方向", "英文名称", "方向定位", "衍生方向", "知识点", "交叉关联"]
for i, h in enumerate(heads2):
    s2.write(0, i, h, F["head"])
s2.set_row(0, 24)
r = 1
for cat in G["categories"]:
    for d in cat["directions"]:
        tint = wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top",
                              "font_color": MUTED, "bg_color": CAT_TINT[cat["id"]]})
        s2.write_number(r, 0, r, F["num"])
        s2.write(r, 1, cat["name"], tint)
        s2.write(r, 2, d["name"], F["dir"])
        s2.write(r, 3, d["en"], F["dim"])
        s2.write(r, 4, d["desc"], F["cell"])
        s2.write_number(r, 5, d["nBranch"], F["num"])
        s2.write_number(r, 6, d["nPoint"], F["num"])
        s2.write_number(r, 7, len(d.get("links", [])), F["num"])
        s2.set_row(r, 14.5 * max(lines(d["desc"], 50), lines(d["en"], 34)) + 5)
        r += 1
s2.autofilter(0, 0, r - 1, 7)

# ---------------------------------------------------------------- 知识点明细
s3 = wb.add_worksheet("知识点明细")
s3.hide_gridlines(2)
s3.freeze_panes(1, 5)
widths = [5, 18, 22, 18, 24, 44, 13, 38]
for i, w in enumerate(widths):
    s3.set_column(i, i, w)
heads3 = ["#", "学科大类", "专业方向", "衍生方向", "知识点", "理论与方法", "编程语言", "框架 / 工具 / 平台"]
for i, h in enumerate(heads3):
    s3.write(0, i, h, F["head"])
s3.set_row(0, 26)

r = 1
idx = 1
for cat in G["categories"]:
    tint = wb.add_format({**base, "border": 1, "border_color": GRID, "valign": "top",
                          "font_color": MUTED, "bg_color": CAT_TINT[cat["id"]]})
    for d in cat["directions"]:
        rows = [("基础", p) for p in d["base"]]
        for b in d["branches"]:
            rows += [(b["name"], p) for p in b["points"]]
        for bname, p in rows:
            s3.write_number(r, 0, idx, F["num"])
            s3.write(r, 1, cat["name"], tint)
            s3.write(r, 2, d["name"], F["dim"])
            s3.write(r, 3, bname, F["cell"])
            s3.write(r, 4, p["n"], F["dir"])
            s3.write(r, 5, p["t"], F["cell"])
            s3.write(r, 6, p["l"], F["mono"])
            s3.write(r, 7, p["s"], F["mono"])
            n_lines = max(lines(p["t"], 44), lines(p["s"], 38), lines(p["n"], 24))
            s3.set_row(r, 14.5 * n_lines + 4)
            r += 1
            idx += 1
s3.autofilter(0, 0, r - 1, 7)
s3.freeze_panes(1, 5)

# ---------------------------------------------------------------- 交叉衍生
s4 = wb.add_worksheet("交叉衍生")
s4.hide_gridlines(2)
s4.set_column("A:A", 5)
s4.set_column("B:B", 26)
s4.set_column("C:C", 24)
s4.set_column("D:D", 24)
s4.set_column("E:E", 78)
heads4 = ["#", "交叉方向", "组成方向 A", "组成方向 B", "为什么会出现：技术耦合点"]
for i, h in enumerate(heads4):
    s4.write(0, i, h, F["head"])
s4.set_row(0, 24)
dmap = {d["id"]: (d, c) for c in G["categories"] for d in c["directions"]}
r = 1
for i, x in enumerate(G["crossLinks"], 1):
    a, ca = dmap[x["a"]]
    b, cb = dmap[x["b"]]
    s4.write_number(r, 0, i, F["num"])
    s4.write(r, 1, x["name"], F["dir"])
    s4.write(r, 2, f"{a['name']}\n{ca['name']}", F["cell"])
    s4.write(r, 3, f"{b['name']}\n{cb['name']}", F["cell"])
    s4.write(r, 4, x["desc"], F["cell"])
    s4.set_row(r, 46)
    r += 1

# ---------------------------------------------------------------- 技术栈索引
tech = OrderedDict()
for cat in G["categories"]:
    for d in cat["directions"]:
        pts = list(d["base"]) + [p for b in d["branches"] for p in b["points"]]
        for p in pts:
            for item in p["s"].replace("，", "、").split("、"):
                item = item.strip()
                if not item or item == "—" or len(item) > 40:
                    continue
                tech.setdefault(item, {"n": 0, "dirs": [], "cats": []})
                tech[item]["n"] += 1
                if d["name"] not in tech[item]["dirs"]:
                    tech[item]["dirs"].append(d["name"])
                if cat["id"] not in [c for c in tech[item]["cats"]]:
                    tech[item]["cats"].append(cat["id"])

s5 = wb.add_worksheet("技术栈索引")
s5.hide_gridlines(2)
s5.set_column("A:A", 5)
s5.set_column("B:B", 30)
s5.set_column("C:C", 9)
s5.set_column("D:D", 20)
s5.set_column("E:E", 70)
heads5 = ["#", "技术 / 工具 / 平台", "知识点", "所属大类", "关联方向"]
for i, h in enumerate(heads5):
    s5.write(0, i, h, F["head"])
s5.set_row(0, 24)
rows = sorted(tech.items(), key=lambda kv: (-kv[1]["n"], kv[0]))
r = 1
for i, (name, info) in enumerate(rows, 1):
    s5.write_number(r, 0, i, F["num"])
    s5.write(r, 1, name, F["dir"])
    s5.write_number(r, 2, info["n"], F["num"])
    cats_label = "、".join([CAT_SHORT[c] for c in info["cats"][:2]]) + ("…" if len(info["cats"]) > 2 else "")
    s5.write(r, 3, cats_label, F["dim"])
    s5.write(r, 4, "、".join(info["dirs"][:5]) + ("…" if len(info["dirs"]) > 5 else ""), F["cell"])
    r += 1
s5.autofilter(0, 0, r - 1, 4)
s5.freeze_panes(1, 0)

wb.close()
print("written", OUT.name, OUT.stat().st_size // 1024, "KB", "| tech terms:", len(rows))
