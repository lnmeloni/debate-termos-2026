"""Coleta posts do Bluesky em tempo real (Jetstream, fluxo público, sem chave) que falam do debate.

Uso: venv/bin/python coletar_bluesky.py
Filtra posts em português que citam Lula, Flávio, Bolsonaro ou o debate.
Escreve dados/bluesky_mensagens.csv (dono: este script), no mesmo formato que o ranking.py gera
para o YouTube, para o sentimento.py e o comparar.py lerem igual.
"""
import asyncio
import csv
import json
import os
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import websockets

BRT = timezone(timedelta(hours=-3))
URL = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
SAIDA = "dados/bluesky_mensagens.csv"
TEMA = re.compile(r"\blula\b|flavio|bolsonar|debate|#debatenaband|\bpt\b|petista|bolsonarista")

def norm(s):
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()

async def main():
    novo = not os.path.exists(SAIDA)
    with open(SAIDA, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["ts_brt", "autor", "mensagem"])
        while True:
            try:
                async with websockets.connect(URL, max_size=2**22) as ws:
                    async for raw in ws:
                        e = json.loads(raw)
                        c = e.get("commit") or {}
                        if c.get("operation") != "create":
                            continue
                        rec = c.get("record") or {}
                        langs = rec.get("langs") or []
                        texto = rec.get("text") or ""
                        if langs and not any(l.startswith("pt") for l in langs):
                            continue
                        if not TEMA.search(norm(texto)):
                            continue
                        ts = datetime.fromtimestamp(e["time_us"] / 1e6, BRT).isoformat()
                        w.writerow([ts, e.get("did", ""), texto.replace("\n", " ")])
                        f.flush()
            except Exception as ex:
                print(f"{datetime.now():%H:%M:%S} reconectando: {ex}", flush=True)
                await asyncio.sleep(5)

asyncio.run(main())
