#!/usr/bin/env python3
"""
按需裁剪中文字体：只保留网站实际用到的中文字符，生成很小的 woff2，
并把 @font-face 注入到每个 HTML 页面的 <head> 里。

在 `hugo` 构建之后运行（GitHub Actions 里已经配置好）：
    python3 scripts/font_subset.py --public public --font ChillHuoFangKai_F_Regular.otf

依赖：pip install fonttools brotli
"""
import argparse
import hashlib
import io
import pathlib
import re

from fontTools import subset
from fontTools.ttLib import TTFont

FAMILY = "Chill HuoFangKai"
LOCAL_NAMES = ["寒蝉活仿楷_復Regular", "ChillHuoFangKai_F_Regular"]

# 交给中文字体渲染的字符范围；其余字符（英文、数字、半角符号）继续用主题的 monospace
CJK_RANGES = [
    (0x2E80, 0x2FDF),  # 部首
    (0x3000, 0x303F),  # 中文标点：、。「」《》等
    (0x31C0, 0x31EF),  # 笔画
    (0x3200, 0x33FF),  # 带圈字符等
    (0x3400, 0x4DBF),  # 扩展 A
    (0x4E00, 0x9FFF),  # 基本汉字
    (0xF900, 0xFAFF),  # 兼容汉字
    (0xFE10, 0xFE1F),  # 竖排标点
    (0xFE30, 0xFE4F),  # 兼容标点
    (0xFF00, 0xFFEF),  # 全角符号：，！？（）：；等
]
# 中文里常用、但位于通用标点区的符号：‘ ’ “ ” — …
EXTRA = {0x2018, 0x2019, 0x201C, 0x201D, 0x2014, 0x2026}


def is_cjk(cp: int) -> bool:
    return cp in EXTRA or any(a <= cp <= b for a, b in CJK_RANGES)


def to_unicode_range(cps):
    cps = sorted(cps)
    out, start, prev = [], cps[0], cps[0]
    for cp in cps[1:] + [None]:
        if cp is not None and cp == prev + 1:
            prev = cp
            continue
        out.append(f"U+{start:X}" if start == prev else f"U+{start:X}-{prev:X}")
        if cp is not None:
            start = prev = cp
    return ",".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default="public")
    ap.add_argument("--font", required=True)
    ap.add_argument("--base-path", default="/", help="网站的根路径，用户主页就是 /")
    args = ap.parse_args()

    public = pathlib.Path(args.public)
    html_files = sorted(public.rglob("*.html"))
    if not html_files:
        raise SystemExit(f"在 {public} 里没有找到 HTML，先运行 hugo 构建")

    used = set()
    for f in html_files:
        used.update(ord(c) for c in f.read_text(encoding="utf-8"))

    font = TTFont(args.font)
    cmap = font.getBestCmap()
    keep = sorted(cp for cp in used if is_cjk(cp) and cp in cmap)
    if not keep:
        print("网站里没有中文字符，跳过字体处理")
        return

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=keep)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = buf.getvalue()

    digest = hashlib.sha256(data).hexdigest()[:10]
    name = f"chill-huofangkai.{digest}.woff2"
    out_dir = public / "fonts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("chill-huofangkai.*.woff2"):
        old.unlink()
    (out_dir / name).write_bytes(data)

    base = args.base_path.rstrip("/") + "/"
    url = f"{base}fonts/{name}"
    local_src = ",".join(f'local("{n}")' for n in LOCAL_NAMES)
    preload = f'<link rel="preload" href="{url}" as="font" type="font/woff2" crossorigin>'
    face = (
        f"<style>@font-face{{font-family:\"{FAMILY}\";"
        f"src:{local_src},url(\"{url}\") format(\"woff2\");"
        f"font-weight:normal;font-style:normal;font-display:swap;"
        f"unicode-range:{to_unicode_range(keep)}}}</style>"
    )

    pattern = re.compile(r"</head>", re.IGNORECASE)
    zh_page = re.compile(r"<html[^>]*\blang=[\"']?zh", re.IGNORECASE)
    for f in html_files:
        text = f.read_text(encoding="utf-8")
        if FAMILY in text and "@font-face" in text:
            continue  # 已经注入过
        # 只有中文页面预加载字体；英文页面只声明 @font-face，用到中文字符时浏览器才会按需下载
        tag = (preload + face) if zh_page.search(text) else face
        new, n = pattern.subn(tag + "</head>", text, count=1)
        if n:
            f.write_text(new, encoding="utf-8")

    print(f"中文字符 {len(keep)} 个，字体 {len(data) / 1024:.1f} KB → {url}，已注入 {len(html_files)} 个页面")


if __name__ == "__main__":
    main()
