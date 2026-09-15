# xteve-playlist

M3U + XMLTV for xTeVe.

## xTeVe

Playlist:

https://raw.githubusercontent.com/louis83023/xteve-playlist/main/playlist.m3u

XMLTV File:

https://raw.githubusercontent.com/louis83023/xteve-playlist/main/guide.xml

Channel `id` matches `tvg-id` in the M3U. Programme entries currently exist only for **TaiwanPlus TV** (`TaiwanPlusTV.tw@SD`). Other channels are listed for mapping; no invented timeslots.

Regenerate locally:

```
python build_guide.py
```
