#!/usr/bin/env python3
"""XMLTV from the user's M3U. Real TaiwanPlus programmes; other channels listed only."""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

M3U = Path(r"C:/Users/林于翔/AppData/Local/hermes/cache/documents/doc_1fc7f1070c76_playlist.m3u")
OUT = Path(r"D:/iptv/guide.xml")
TZ = timezone(timedelta(hours=8))


def load_channels(m3u: Path) -> list[dict]:
    text = m3u.read_text(encoding="utf-8")
    seen = set()
    channels = []
    for meta, _url in re.findall(r"#EXTINF:-1 ([^\n]*)\n(\S+)", text):
        tid = re.search(r'tvg-id="([^"]*)"', meta)
        logo = re.search(r'tvg-logo="([^"]*)"', meta)
        name = meta.split(",")[-1].strip()
        cid = tid.group(1) if tid else name
        if cid in seen:
            continue
        seen.add(cid)
        channels.append({"id": cid, "name": name, "logo": logo.group(1) if logo else ""})
    return channels


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def resolve(data: list, v):
    if isinstance(v, int) and 0 <= v < len(data):
        return data[v]
    return v


def taiwanplus_programs() -> list[dict]:
    html = fetch("https://www.taiwanplus.com/taiwanplustv/schedule")
    a = html.find("[[\"ShallowReactive\"")
    b = html.find("</script>", a)
    data = json.loads(html[a:b])
    items = []
    for x in data:
        if not (isinstance(x, dict) and "dateTime" in x and "title" in x):
            continue
        dt_s = resolve(data, x["dateTime"])
        title = resolve(data, x["title"])
        if not isinstance(dt_s, str) or not isinstance(title, str):
            continue
        try:
            start = datetime.strptime(dt_s.replace("\\u002F", "/"), "%Y/%m/%d %H:%M").replace(tzinfo=TZ)
        except ValueError:
            continue
        desc = resolve(data, x.get("description"))
        image = resolve(data, x.get("image"))
        items.append(
            {
                "start": start,
                "title": title,
                "desc": desc if isinstance(desc, str) else "",
                "image": image if isinstance(image, str) else "",
            }
        )
    uniq = {it["start"]: it for it in items}
    ordered = sorted(uniq.values(), key=lambda z: z["start"])
    for i, it in enumerate(ordered):
        if i + 1 < len(ordered):
            it["stop"] = ordered[i + 1]["start"]
        else:
            it["stop"] = it["start"] + timedelta(minutes=30)
    return ordered


def xmltv_time(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S %z")


def build(channels: list[dict], plus: list[dict]) -> str:
    root = Element("tv")
    root.set("generator-info-name", "xteve-playlist")
    root.set("source-info-name", "m3u tvg-id + TaiwanPlus live schedule")
    for ch in channels:
        el = SubElement(root, "channel", id=ch["id"])
        dn = SubElement(el, "display-name")
        dn.text = ch["name"]
        if ch["logo"]:
            SubElement(el, "icon", src=ch["logo"])
    for it in plus:
        prog = SubElement(
            root,
            "programme",
            start=xmltv_time(it["start"]),
            stop=xmltv_time(it["stop"]),
            channel="TaiwanPlusTV.tw@SD",
        )
        title = SubElement(prog, "title", lang="en")
        title.text = it["title"]
        if it["desc"]:
            d = SubElement(prog, "desc", lang="en")
            d.text = it["desc"]
        if it["image"]:
            SubElement(prog, "icon", src=it["image"])
    xml = tostring(root, encoding="utf-8")
    return minidom.parseString(xml).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def main() -> None:
    chans = load_channels(M3U)
    plus = taiwanplus_programs()
    xml = build(chans, plus)
    OUT.write_text(xml, encoding="utf-8")
    print("channels", len(chans))
    print("taiwanplus programmes", len(plus))
    if plus:
        print("range", plus[0]["start"], "->", plus[-1]["stop"])
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
