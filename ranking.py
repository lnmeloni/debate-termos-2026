"""Lê o chat coletado pelo yt-dlp e mostra os termos mais falados por janela de tempo.

Uso: venv/bin/python ranking.py <nome> [janela_min=5] [top=20] [--loop]
Lê dados/<nome>.live_chat.json* (escritos só pelo coletar.sh).
Escreve dados/<nome>_mensagens.csv e dados/<nome>_termos_por_minuto.csv (donos: este script).
"""
import csv
import glob
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone

nome = sys.argv[1]
args = [a for a in sys.argv[2:] if not a.startswith("--")]
janela = int(args[0]) if args else 5
top = int(args[1]) if len(args) > 1 else 20
loop = "--loop" in sys.argv
BRT = timezone(timedelta(hours=-3))

STOP = set("""
a o e é de da do das dos que em um uma uns umas no na nos nas para pra pro por com sem se
ao aos à às os as mais mas mais ou já não nao sim eu tu ele ela eles elas nós vc vcs voce
você vocês me te lhe nos isso isto esse essa este esta aquele aquela ai aí la lá aqui
foi ser ter tem tá ta esta está estão estao vai vão vao era são sao sou fica ficar
muito mt muita pouco tudo todo toda todos nada nem só so até ate quando como onde porque
pq por que q k kk kkk kkkk kkkkk kkkkkk rs rsrs haha hahaha meu minha seu sua dele dela
bem bom boa então entao ainda agora hoje vou faz fazer fala falar disse diz dizer quem
qual depois antes sobre entre também tambem the de né ne tipo cara gente coisa vez
""".split())

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return s

def achar(o):
    if isinstance(o, dict):
        for k in ("liveChatTextMessageRenderer", "liveChatPaidMessageRenderer"):
            if k in o:
                yield o[k]
        for v in o.values():
            yield from achar(v)
    elif isinstance(o, list):
        for v in o:
            yield from achar(v)

def ler():
    msgs = {}
    for p in sorted(glob.glob(f"dados/{nome}.live_chat.json*")):
        with open(p, encoding="utf-8", errors="ignore") as f:
            for linha in f:
                try:
                    d = json.loads(linha)
                except ValueError:
                    continue
                for r in achar(d):
                    texto = "".join(x.get("text", "") for x in r.get("message", {}).get("runs", []))
                    if texto and r.get("id") not in msgs:
                        ts = datetime.fromtimestamp(int(r["timestampUsec"]) / 1e6, BRT)
                        msgs[r["id"]] = (ts, r.get("authorName", {}).get("simpleText", ""), texto)
    return sorted(msgs.values())

def tokens(texto):
    ws = [w for w in re.findall(r"[a-z0-9#@]+", norm(texto)) if len(w) > 2 and w not in STOP]
    return ws + [f"{a} {b}" for a, b in zip(ws, ws[1:])]

def rodar():
    msgs = ler()
    if not msgs:
        print("sem mensagens ainda"); return
    with open(f"dados/{nome}_mensagens.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ts_brt", "autor", "mensagem"])
        w.writerows((t.isoformat(), a, m) for t, a, m in msgs)
    por_min = {}
    for t, _, m in msgs:
        por_min.setdefault(t.replace(second=0, microsecond=0), Counter()).update(set(tokens(m)))
    with open(f"dados/{nome}_termos_por_minuto.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["minuto_brt", "termo", "mensagens"])
        for mi in sorted(por_min):
            for termo, n in por_min[mi].most_common(50):
                w.writerow([mi.strftime("%H:%M"), termo, n])
    fim = msgs[-1][0]
    ini = fim - timedelta(minutes=janela)
    c, base = Counter(), Counter()
    n = nb = 0
    for t, _, m in msgs:
        if t >= ini:
            c.update(set(tokens(m))); n += 1
        else:
            base.update(set(tokens(m))); nb += 1
    # subindo: taxa na janela sobre a taxa no resto do debate, com suavização
    sub = []
    for termo, k in c.items():
        if k >= 3:
            lift = (k / max(n, 1)) / ((base[termo] + 1) / (nb + 20))
            sub.append((lift, k, termo))
    sub.sort(reverse=True)
    mais = c.most_common(top)
    serie = {}
    for t, _, m in msgs:
        mi = t.strftime("%H:%M"); s = serie.setdefault(mi, [0, 0, 0]); x = norm(m)
        s[0] += 1; s[1] += "lula" in x; s[2] += ("flavio" in x or "bolsonaro" in x)
    with open("docs/termos.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(BRT).strftime("%H:%M:%S"), "janela": f"{ini:%H:%M}–{fim:%H:%M}",
                   "n_janela": n, "n_total": len(msgs),
                   "mais": [[t, k] for t, k in mais], "subindo": [[t, k, round(l, 1)] for l, k, t in sub[:top]],
                   "serie": [[mi, *v] for mi, v in sorted(serie.items())]}, f, ensure_ascii=False)
    print(f"\n── {ini:%H:%M}–{fim:%H:%M} · {n} mensagens na janela · {len(msgs)} no total ──")
    print(f"{'MAIS FALADOS':<32}{'SUBINDO (vs. resto do debate)'}")
    for i in range(top):
        a = f"{mais[i][1]:5d}  {mais[i][0]}" if i < len(mais) else ""
        b = f"{sub[i][1]:5d}  {sub[i][2]}  ×{sub[i][0]:.1f}" if i < len(sub) else ""
        print(f"{a:<32}{b}")

if loop:
    while True:
        rodar(); time.sleep(60)
else:
    rodar()
