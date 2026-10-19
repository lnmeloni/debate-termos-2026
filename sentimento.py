"""Sentimento minuto a minuto do chat em relação a Lula e a Flávio, classificado pelo Claude (haiku).

Uso: venv/bin/python sentimento.py <nome> [amostra=120] [--docs]
Lê dados/<nome>_mensagens.csv (escrito pelo ranking.py).
Escreve dados/<nome>_sentimento.csv e docs/sentimento.json (donos: este script).
Cada minuto fechado é classificado uma vez: para cada mensagem, +1 favorável, -1 desfavorável,
0 neutro, null se não fala do candidato. Saldo = (favoráveis - desfavoráveis) / mensagens que falam dele.
"""
import csv
import json
import os
import random
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
PROMPT = ("Mensagens do chat ao vivo do YouTube durante o debate presidencial do 2º turno de 2026 "
          "entre Lula (PT) e Flávio Bolsonaro (PL). Para cada mensagem numerada, diga a posição dela "
          "em relação a cada candidato: 1 favorável, -1 desfavorável, 0 neutro ou ambíguo, null se não "
          "fala dele (direta ou indiretamente; ataque ao Bolsonaro pai ou ao bolsonarismo conta para Flávio, "
          "ataque ao PT conta para Lula). Responda SÓ um JSON, sem texto: "
          '[{"i":1,"lula":1,"flavio":null}, ...]')

def norm(s):
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()

ALVO = re.compile(r"lula|flavio|bolsonar|\bpt\b|petista|lul[ao]|bozo|biroliro|#lula|mito")

def classificar(msgs):
    texto = "\n".join(f"{i+1}. {m[:200]}" for i, m in enumerate(msgs))
    r = subprocess.run(["claude", "-p", "--model", "haiku", PROMPT], input=texto,
                       capture_output=True, text=True, timeout=180)
    j = re.search(r"\[.*\]", r.stdout, re.S)
    return json.loads(j.group(0)) if j else []

def feitos():
    if not os.path.exists(SAIDA):
        return {}
    with open(SAIDA, encoding="utf-8") as f:
        return {r["minuto_brt"]: r for r in csv.DictReader(f)}

def publicar(linhas):
    with open("docs/sentimento.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(BRT).strftime("%H:%M:%S"),
                   "serie": [[r["minuto_brt"], r["saldo_lula"], r["saldo_flavio"], int(r["n_lula"]), int(r["n_flavio"])]
                             for r in sorted(linhas.values(), key=lambda r: r["minuto_brt"])]}, f, ensure_ascii=False)

campos = ["minuto_brt", "msgs_minuto", "amostra", "n_lula", "fav_lula", "desf_lula", "saldo_lula",
          "n_flavio", "fav_flavio", "desf_flavio", "saldo_flavio"]
if __name__ == "__main__":
    nome = sys.argv[1]
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    amostra = int(args[0]) if args else 120
    docs = "--docs" in sys.argv  # só o canal principal escreve docs/sentimento.json
    SAIDA = f"dados/{nome}_sentimento.csv"
    while True:
        try:
            por_min = {}
            with open(f"dados/{nome}_mensagens.csv", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    por_min.setdefault(r["ts_brt"][11:16], []).append(r["mensagem"])
            linhas = feitos()
            abertos = sorted(por_min)[:-1]  # o último minuto ainda está chegando
            for mi in [m for m in abertos if m not in linhas][-3:]:
                todas = por_min[mi]
                alvo = [m for m in todas if ALVO.search(norm(m))]
                random.seed(mi)
                sel = random.sample(alvo, min(amostra, len(alvo)))
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
                with open(SAIDA, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=campos); w.writeheader()
                    w.writerows(sorted(linhas.values(), key=lambda r: r["minuto_brt"]))
                if docs:
                    publicar(linhas)
                print(f"{mi}  Lula {linhas[mi]['saldo_lula']} (n={c['nl']})  Flávio {linhas[mi]['saldo_flavio']} (n={c['nf']})", flush=True)
        except Exception as e:
            print(f"{datetime.now():%H:%M:%S} erro: {e}", flush=True)
        time.sleep(20)
