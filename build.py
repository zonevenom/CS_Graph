#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""合并、校验知识图谱数据，输出统一的 graph.json。"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"


DISP = {
    "d_math_found": "离散数学\n与计算理论",
    "d_math_algo": "算法与\n数据结构",
    "d_math_prob": "概率统计\n与信息论",
    "d_math_num": "数值计算\n与最优化",
    "d_sys_arch": "数字逻辑与\n体系结构",
    "d_sys_os": "操作系统",
    "d_sys_comp": "编译原理\n与程序语言",
    "d_sys_dist": "并行分布式\n与云计算",
    "d_sw_se": "软件工程",
    "d_sw_db": "数据库\n与数据管理",
    "d_sw_big": "大数据\n与数据科学",
    "d_sw_gfx": "图形学\n与多媒体",
    "d_sw_hci": "人机交互\n与可视化",
    "d_net_net": "计算机网络",
    "d_net_sec": "网络空间\n安全",
    "d_net_crypto": "密码学\n与隐私计算",
    "d_ai_kg": "人工智能\n与知识工程",
    "d_ai_ml": "机器学习",
    "d_ai_dl": "深度学习\n与大模型",
    "d_ai_perc": "感知智能",
    "d_app_iot": "物联网\n与嵌入式",
    "d_app_robot": "机器人\n与具身智能",
    "d_app_chain": "区块链\n与 Web3",
    "d_app_bio": "生物信息\n与 AI4Science",
    "d_app_quantum": "量子计算\n与量子信息",
}


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def render_html(graph):
    tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    if "/*__GRAPH_JSON__*/" not in tpl:
        sys.exit("模板缺少数据占位符")
    html = tpl.replace("/*__GRAPH_JSON__*/", payload)
    target = ROOT / "计算机科学与技术知识图谱.html"
    target.write_text(html, encoding="utf-8")
    print(f"HTML: {target.name}  {target.stat().st_size / 1024:.1f} KB")


def main():
    meta = load("00-meta.json")
    cat_files = ["10-math.json", "20-sys.json", "30-net.json",
                 "40-sw.json", "50-ai.json", "60-app.json"]
    cats = {c["id"]: c for c in meta["categories"]}
    graph = {"title": meta["title"], "subtitle": meta["subtitle"],
             "version": meta["version"], "categories": [], "crossLinks": meta["crossLinks"]}

    order = [c["id"] for c in meta["categories"]]
    by_cat = {}
    for fn in cat_files:
        block = load(fn)
        cid = block["category"]
        if cid not in cats:
            sys.exit(f"未知大类 {cid} in {fn}")
        by_cat[cid] = block["directions"]

    seen = set()
    total_dirs = total_branches = total_points = 0
    for cid in order:
        cat = dict(cats[cid])
        dirs = by_cat.get(cid, [])
        cat["directions"] = []
        for d in dirs:
            if d["id"] in seen:
                sys.exit(f"重复方向 id: {d['id']}")
            seen.add(d["id"])
            d["cat"] = cid
            d["disp"] = DISP.get(d["id"], d["name"])
            for b in d["branches"]:
                b["id"] = f"{d['id']}::{b['name']}"
                for p in b["points"]:
                    for k in ("n", "t", "l", "s"):
                        if k not in p:
                            sys.exit(f"{d['id']} / {b['name']} 缺少字段 {k}")
            n_points = len(d.get("base", [])) + sum(len(b["points"]) for b in d["branches"])
            d["nBase"] = len(d.get("base", []))
            d["nBranch"] = len(d["branches"])
            d["nPoint"] = n_points
            total_dirs += 1
            total_branches += len(d["branches"])
            total_points += n_points
            cat["directions"].append(d)
        graph["categories"].append(cat)

    for link in graph["crossLinks"]:
        for key in ("a", "b"):
            if link[key] not in seen:
                sys.exit(f"交叉链接引用不存在方向: {link[key]}")
    # 建立双向索引
    idx = {}
    for i, link in enumerate(graph["crossLinks"]):
        idx.setdefault(link["a"], []).append(i)
        idx.setdefault(link["b"], []).append(i)
    for cat in graph["categories"]:
        for d in cat["directions"]:
            d["links"] = idx.get(d["id"], [])

    graph["stats"] = {"categories": len(graph["categories"]),
                      "directions": total_dirs,
                      "branches": total_branches,
                      "points": total_points,
                      "links": len(graph["crossLinks"])}

    out = ROOT / "graph.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=1)
    render_html(graph)
    print(json.dumps(graph["stats"], ensure_ascii=False))
    for cat in graph["categories"]:
        print(f"  {cat['name']}: {len(cat['directions'])} 方向 / "
              f"{sum(d['nBranch'] for d in cat['directions'])} 衍生 / "
              f"{sum(d['nPoint'] for d in cat['directions'])} 知识点")


if __name__ == "__main__":
    main()
