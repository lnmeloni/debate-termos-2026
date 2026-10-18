# Termos mais falados no chat do debate (Band, 18/10/2026)

Criado no hub em 18/10/2026, 20h10, a pedido do Luís durante o debate do 2º turno (Flávio Bolsonaro × Lula, Band, 20h). Vai continuar no spoke do `tse-apuracao-tempo-real`.

- Live: https://www.youtube.com/watch?v=Gqc1rQtzWUk ("[AO VIVO] Flávio Bolsonaro x Lula: debate presidencial do 2º turno na Band")
- `coletar.sh <url> <nome>` grava o chat bruto com yt-dlp em `dados/<nome>.live_chat.json*`; reconecta se cair. (`chat-downloader` não funciona mais com o YouTube atual: "Unable to parse initial video data".)
- `ranking.py <nome> [janela_min] [top] [--loop]` lê o bruto e escreve `dados/<nome>_mensagens.csv` e `dados/<nome>_termos_por_minuto.csv`; imprime top termos da janela. Unigramas e bigramas, contados uma vez por mensagem, stopwords feitas às pressas.
- Rodando em segundo plano desde ~20h12: `coletar.sh` (yt-dlp) e `ranking.py --loop` → `dados/ranking_ao_vivo.log`. Parar: `pkill -f coletar.sh; pkill -f yt-dlp; pkill -f ranking.py`.
- Limites: 1–2 min de atraso (yt-dlp grava o chat em fragmentos); o chat da live não representa "as redes". Próximo debate: Globo, 23/10.
