"""Junta os canais num arquivo só para a página comparar o chat de cada live.

Uso: venv/bin/python comparar.py [--loop]
Lê dados/<nome>_mensagens.csv (ranking.py) e dados/<nome>_sentimento.csv (sentimento.py) de cada canal em CANAIS.
Escreve docs/canais.json (dono: este script).
"""
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
CANAIS = {  # nome: (rótulo, url da live)
    "band_2026-10-18": ("Band Jornalismo", "https://www.youtube.com/watch?v=Gqc1rQtzWUk"),
    "bandnewsfm": ("Rádio BandNews FM", "https://www.youtube.com/watch?v=Amwukq3hviM"),
    "radiobandeirantes": ("Rádio Bandeirantes", "https://www.youtube.com/watch?v=Y_S0Rb6J6A8"),
    "cnn": ("CNN Brasil", "https://www.youtube.com/watch?v=NMd1knf5fjw"),
    "dcm": ("DCM TV (react)", "https://www.youtube.com/watch?v=MsW2m_296b4"),
    "benmendes": ("Ben Mendes TV", "https://www.youtube.com/watch?v=huBXBz4R92o"),
    "tragicomico": ("Canal Tragicômico (análise)", "https://www.youtube.com/watch?v=mwR0LgDFU6A"),
    "mrtv": ("MRTV Márcio Rangel", "https://www.youtube.com/watch?v=KssLMd-3B8s"),
    "maxcardoso": ("Max Cardoso (react)", "https://www.youtube.com/watch?v=Xb0-cYhaIzY"),
    "bisotto": ("Eduardo Bisotto (react)", "https://www.youtube.com/watch?v=WNU3FWjkJOQ"),
    "crentenews": ("Crente News (react)", "https://www.youtube.com/watch?v=BEDeoAZ4xKM"),
    "focopatria": ("Foco Pátria (react)", "https://www.youtube.com/watch?v=kDKRsR-hvkc"),
    "portalviu": ("Portal VIU", "https://www.youtube.com/watch?v=pB33YNDSf3s"),
    "shimon": ("Shimon Oliveira", "https://www.youtube.com/watch?v=7EirjYrkvFA"),
    "steffan": ("Steffan", "https://www.youtube.com/watch?v=d7D2nPavEYA"),
    "vaznaminha": ("VazNaMinha Cast", "https://www.youtube.com/watch?v=qirN-TF7pd4"),
    "thebunker": ("The Bunker", "https://www.youtube.com/watch?v=tIsN0_9Xwjc"),
    "thenewscc": ("the news cc (react)", "https://www.youtube.com/watch?v=-D_2Ev0VABE"),
    "bluesky": ("Bluesky (posts em português)", "https://bsky.app/search?q=debate%20lula%20fl%C3%A1vio"),
}

def rodar():
    saida = []
    for nome, (rotulo, url) in CANAIS.items():
        msgs = {}
        p = f"dados/{nome}_mensagens.csv"
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    mi = r["ts_brt"][11:16]
                    msgs[mi] = msgs.get(mi, 0) + 1
        sent = {}
        p = f"dados/{nome}_sentimento.csv"
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    sent[r["minuto_brt"]] = r
        serie = []
        for mi in sorted(set(msgs) | set(sent)):
            s = sent.get(mi, {})
            serie.append([mi, msgs.get(mi, 0), s.get("saldo_lula", ""), s.get("saldo_flavio", ""),
                          int(s.get("n_lula") or 0), int(s.get("n_flavio") or 0)])
        tot = {k: sum(int(r.get(k) or 0) for r in sent.values()) for k in ("n_lula", "fav_lula", "desf_lula", "n_flavio", "fav_flavio", "desf_flavio")}
        lean = None
        if tot["n_lula"] >= 30 and tot["n_flavio"] >= 30:
            lean = (tot["fav_lula"] - tot["desf_lula"]) / tot["n_lula"] - (tot["fav_flavio"] - tot["desf_flavio"]) / tot["n_flavio"]
        bolha = None if lean is None else ("pró-Lula" if lean > 0.6 else "pró-Flávio" if lean < -0.6 else "dividida")
        saida.append({"nome": nome, "rotulo": rotulo, "url": url, "n_total": sum(msgs.values()), "serie": serie,
                      "lean": None if lean is None else round(lean, 2), "bolha": bolha, "_sent": sent})
    # Índice equilibrado: em cada minuto, média ponderada pelo n dentro de cada bolha e depois média simples
    # entre as bolhas presentes, para que a bolha maior (o chat da Band) não decida sozinha.
    eq = []
    minutos = sorted({mi for c in saida if c["bolha"] for mi in c["_sent"]})
    for mi in minutos:
        porb = {}
        for c in saida:
            r = c["_sent"].get(mi)
            if not c["bolha"] or not r:
                continue
            b = porb.setdefault(c["bolha"], {k: 0 for k in ("nl", "fl", "dl", "nf", "ff", "df")})
            b["nl"] += int(r["n_lula"] or 0); b["fl"] += int(r["fav_lula"] or 0); b["dl"] += int(r["desf_lula"] or 0)
            b["nf"] += int(r["n_flavio"] or 0); b["ff"] += int(r["fav_flavio"] or 0); b["df"] += int(r["desf_flavio"] or 0)
        vals = {"sl": [], "sf": [], "pl": [], "pf": []}
        var = {"sl": [], "sf": [], "pl": [], "pf": []}
        for b in porb.values():
            for n, fa, de, ks, kp in (("nl", "fl", "dl", "sl", "pl"), ("nf", "ff", "df", "sf", "pf")):
                if b[n]:
                    pf_, pd_ = b[fa] / b[n], b[de] / b[n]
                    sal = pf_ - pd_
                    vals[ks].append(sal); var[ks].append((pf_ + pd_ - sal ** 2) / b[n])
                    vals[kp].append(pf_); var[kp].append(pf_ * (1 - pf_) / b[n])
        med = lambda v: round(sum(v) / len(v), 2) if v else ""
        ic = lambda k: round(1.96 * (sum(var[k]) ** 0.5) / len(var[k]), 2) if var[k] else ""  # meia-largura do IC de 95%
        eq.append([mi, med(vals["sl"]), med(vals["sf"]), med(vals["pl"]), med(vals["pf"]), sorted(porb),
                   ic("sl"), ic("sf"), ic("pl"), ic("pf")])
    for c in saida:
        del c["_sent"]
    with open("docs/canais.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(BRT).strftime("%H:%M:%S"), "canais": saida, "equilibrado": eq}, f, ensure_ascii=False)
    print(datetime.now(BRT).strftime("%H:%M:%S"), " · ".join(f"{c['rotulo']} {c['n_total']}" for c in saida), flush=True)

if "--loop" in sys.argv:
    while True:
        rodar(); time.sleep(60)
else:
    rodar()
