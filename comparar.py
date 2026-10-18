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
        saida.append({"nome": nome, "rotulo": rotulo, "url": url, "n_total": sum(msgs.values()), "serie": serie})
    with open("docs/canais.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(BRT).strftime("%H:%M:%S"), "canais": saida}, f, ensure_ascii=False)
    print(datetime.now(BRT).strftime("%H:%M:%S"), " · ".join(f"{c['rotulo']} {c['n_total']}" for c in saida), flush=True)

if "--loop" in sys.argv:
    while True:
        rodar(); time.sleep(60)
else:
    rodar()
