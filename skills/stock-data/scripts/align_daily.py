#!/usr/bin/env python3
import json

def load(p):
    return {b['date']: b for b in json.load(open(p))['data']['bars']}

g = load('/tmp/601211.json')
sh = load('/tmp/sh.json')
sz = load('/tmp/sz.json')
cyb = load('/tmp/cyb.json')
bk = load('/tmp/bk.json')

dates = sorted(set(g) & set(sh) & set(sz) & set(cyb) & set(bk))

rows = []
for i, d in enumerate(dates):
    if i == 0:
        continue
    pd = dates[i-1]
    gc = g[d]['close']; pc = g[pd]['close']
    gp = (gc/pc-1)*100
    sp = (sh[d]['close']/sh[pd]['close']-1)*100
    zp = (sz[d]['close']/sz[pd]['close']-1)*100
    cp = (cyb[d]['close']/cyb[pd]['close']-1)*100
    kp = (bk[d]['close']/bk[pd]['close']-1)*100
    rel = gp - kp
    rows.append((d, gc, gp, sp, zp, cp, kp, rel))

print("日期        国泰收   国泰%   上证%   深成%   创业%   券商%  相对券商")
for d, gc, gp, sp, zp, cp, kp, rel in rows:
    print(f"{d}  {gc:7.2f} {gp:+6.2f} {sp:+6.2f} {zp:+6.2f} {cp:+6.2f} {kp:+6.2f} {rel:+7.2f}")
