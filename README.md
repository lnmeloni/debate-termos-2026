# O chat do debate, minuto a minuto (Band, 18/10/2026)

**🔴 Ao vivo: https://lnmeloni.github.io/debate-termos-2026/** · termos mais falados, termos subindo e sentimento minuto a minuto sobre Lula e Flávio Bolsonaro nos chats ao vivo de 8 transmissões do debate no YouTube.

## Como é feito

1. **Coleta.** `coletar.sh <url> <nome>` lê o chat ao vivo de cada transmissão com o [yt-dlp](https://github.com/yt-dlp/yt-dlp) e grava o bruto em `dados/` (fora do repositório). Reconecta sozinho se cair. A Band está sendo coletada desde ~20h06; os outros canais, desde ~20h35.
2. **Termos.** `ranking.py <nome> --loop` quebra cada mensagem em palavras e pares de palavras, tira palavras vazias e conta cada termo uma vez por mensagem. *Mais falados* = últimos 5 minutos. *Subindo* = frequência nos últimos 5 minutos dividida pela frequência no resto do debate.
3. **Sentimento.** `sentimento.py <nome> [amostra]` pega cada minuto fechado, sorteia até 120 mensagens (80 nos canais menores) que citam um dos candidatos por nome, apelido, partido ou bolsonarismo, e pede ao Claude Haiku (Anthropic) que marque cada uma como favorável, desfavorável ou neutra para cada candidato. Saldo = (favoráveis − desfavoráveis) ÷ mensagens que falam do candidato, de −1 a +1.
4. **Comparação.** `comparar.py --loop` junta os canais em `docs/canais.json`.
5. **Publicação.** A cada minuto os JSON agregados em `docs/` são commitados e o GitHub Pages serve `docs/index.html`.

## Limites

- O chat de uma live não é o eleitorado. Cada transmissão tem a sua audiência (há canais de react e de análise), então o interessante é a variação no tempo e a diferença entre bolhas, não o nível.
- Ironia, torcida organizada e spam confundem a classificação. Minutos com poucas mensagens são ruidosos; a página mostra o n.
- Atraso de 2 a 5 minutos.
- Só agregados são publicados. Nenhum nome de usuário nem texto de mensagem sai do computador.

## Canais

Band Jornalismo · Rádio BandNews FM · Rádio Bandeirantes · CNN Brasil · DCM TV (react) · Ben Mendes TV · Canal Tragicômico (análise) · MRTV Márcio Rangel. Links em `comparar.py`.
