"""Segundo classificador: refaz o sentimento de cada canal com o GPT (gpt-4o-mini), para conferir o Claude.

Uso: venv/bin/python sentimento_gpt.py
Lê a chave de OPENAI_API_KEY no ambiente ou em ~/.config/debate-termos/.env (fora do Dropbox e do git).
Para cada canal em comparar.CANAIS, sorteia a MESMA amostra que o sentimento.py (mesma semente,
mesmo filtro, mesmo tamanho) e classifica com o mesmo prompt.
Escreve dados/<nome>_sentimento_gpt.csv (dono: este script), no mesmo formato do sentimento.py.
"""
import csv
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from openai import OpenAI

from comparar import CANAIS
from sentimento import ALVO, PROMPT, campos, norm  # noqa: E402  (mesma régua do Claude)

ENV = os.path.expanduser("~/.config/debate-termos/.env")  # fora do Dropbox e do git
if not os.environ.get("OPENAI_API_KEY") and os.path.exists(ENV):
    for linha in open(ENV):
        k, _, v = linha.strip().partition("=")
        if k == "OPENAI_API_KEY":
            os.environ[k] = v.strip().strip('"')
if not os.environ.get("OPENAI_API_KEY"):
    sys.exit("sem OPENAI_API_KEY (ambiente ou ~/.config/debate-termos/.env)")

cli = OpenAI()
AMOSTRA = {"band_2026-10-18": 120}  # os outros canais usam 80, como no sentimento.py

def classificar(msgs):
    texto = "\n".join(f"{i+1}. {m[:200]}" for i, m in enumerate(msgs))
    r = cli.chat.completions.create(model="gpt-4o-mini", temperature=0,
                                    messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": texto}])
    j = re.search(r"\[.*\]", r.choices[0].message.content, re.S)
    return json.loads(j.group(0)) if j else []

def canal(nome):
    p = f"dados/{nome}_mensagens.csv"
    if not os.path.exists(p):
        return
    saida = f"dados/{nome}_sentimento_gpt.csv"
    linhas = {}
    if os.path.exists(saida):
        with open(saida, encoding="utf-8") as f:
            linhas = {r["minuto_brt"]: r for r in csv.DictReader(f)}
    por_min = {}
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            por_min.setdefault(r["ts_brt"][11:16], []).append(r["mensagem"])
    for mi in [m for m in sorted(por_min)[:-1] if m not in linhas][-5:]:
        todas = por_min[mi]
        alvo = [m for m in todas if ALVO.search(norm(m))]
        random.seed(mi)
        sel = random.sample(alvo, min(AMOSTRA.get(nome, 80), len(alvo)))
        res = classificar(sel) if sel else []
        c = {k: 0 for k in ("nl", "fl", "dl", "nf", "ff", "df")}
        for x in res:
            for cand, n, fa, de in (("lula", "nl", "fl", "dl"), ("flavio", "nf", "ff", "df")):
                v = x.get(cand)
                if v is not None:
                    c[n] += 1; c[fa] += v == 1; c[de] += v == -1
        sal = lambda fa, de, n: round((c[fa] - c[de]) / c[n], 2) if c[n] else ""
        linhas[mi] = dict(zip(campos, [mi, len(todas), len(sel), c["nl"], c["fl"], c["dl"], sal("fl", "dl", "nl"),
                                       c["nf"], c["ff"], c["df"], sal("ff", "df", "nf")]))
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos); w.writeheader()
        w.writerows(sorted(linhas.values(), key=lambda r: r["minuto_brt"]))

while True:
    def seguro(n):
        try:
            canal(n)
        except Exception as e:
            print(f"{n}: {e}", flush=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(seguro, CANAIS))
    print(f"{datetime.now():%H:%M:%S} rodada GPT ok", flush=True)
    time.sleep(30)
