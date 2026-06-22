# exemplo-jarvis — um jarvis mínimo, construído a partir da mercearia

Este diretório é um **exemplo real e rodável** do que sai do fluxo da INTELECTO:
**mercearia → briefing `.md` → código**. Não é um produto final — é a prova de
que o caminho funciona, construída e testada de verdade (offline, só stdlib).

## Como ele nasceu (o caminho)

1. Na **mercearia** (`doc/framework-comparison-pt.html`) você clica nos ingredientes
   e exporta o briefing → **`meu-assistente.md`** (incluído aqui, é o arquivo que gerou este código).
2. Esse briefing é entregue ao Claude Code, que o lê e segue o ponteiro para
   **`doc/intelecto.md`** (o plano de obra completo: contratos de interface, dataclasses,
   schema do FTS5, fluxo do loop, blocklist…).
3. O resultado é este núcleo: `jarvis/` + testes.

> **Descoberta honesta da validação (veredito: PARCIAL).**
> O `meu-assistente.md` **sozinho NÃO basta** — ele é uma *lista de ingredientes*
> (o quê incluir + onde está o código de referência), um **roteador, não uma receita**.
> O elemento que sustenta a construção é o ponteiro para `doc/intelecto.md`: são os
> **contratos de interface** desse plano que tornam cada módulo implementável e
> encaixável. `.md` + `doc/intelecto.md` + `reference-repos/` (o que o usuário real
> tem) = núcleo sai direto, como este exemplo prova.

## O que está aqui (tudo Python stdlib — zero pip, zero rede, zero chave de API)

```
jarvis/
  config.py            # carrega/salva config JSON (+ merge esparso, validação)
  security/
    safety.py          # blocklist de comandos perigosos (rm -rf /, mkfs, dd if=, …)
    secrets.py         # cofre de segredos cifrado, atado à máquina
  providers/
    base.py            # BaseProvider (contrato de doc/intelecto.md)
    mock.py            # MockProvider offline (respostas canned, inclui tool-call)
  channels/
    base.py            # BaseChannel
    cli.py             # canal CLI/in-memory (usado nos testes)
    telegram.py        # canal Telegram — ESTRUTURAL (não roda sem token, por design)
  memory/
    store.py           # memória SQLite FTS5 (save/search/forget/recent)
  tools/
    base.py registry.py memory_tools.py filesystem.py shell.py
  agent/
    context.py         # monta o system prompt a partir de SOUL/AGENTS/USER/MEMORY
    loop.py            # loop de tool-calling (máx N rounds)
workspace/             # SOUL.md / AGENTS.md / USER.md / MEMORY.md (identidade)
meu-assistente.md      # o briefing gerado que originou este código
test_jarvis.py         # 9 testes (unittest)
smoke.py               # demo ponta a ponta (memória + loop juntos)
```

## Como rodar (não precisa instalar nada)

```bash
cd exemplo-jarvis
python3 -m unittest discover -s . -p 'test_*.py' -v   # 9 testes
python3 smoke.py                                       # demo memória+loop
```

Saída esperada do smoke (a linha `DB` prova que o nome foi persistido no SQLite,
não veio de string fixa):

```
USER : lembre que meu nome é Nei
JARVIS: Seu nome é Nei.
USER : qual meu nome?
JARVIS: Seu nome é Nei.
DB   : ['Meu nome é Nei']
```

Os testes cobrem: FTS5 save→search→forget; um round completo do loop (MockProvider
pede uma tool, o loop executa e responde); blocklist bloqueia comando perigoso e
libera o seguro; config round-trip; contexto de identidade contém SOUL/USER.

## O que falta para um jarvis **vivo no Telegram**

Este exemplo é deliberadamente offline. Para virar um assistente real (seguindo
`doc/intelecto.md`) faltam, fora do escopo deste núcleo de validação:

- **Token do Telegram** (@BotFather) — `TelegramChannel.start()` recusa sem ele, de propósito.
- **Provider real + chave/custo** — trocar o `MockProvider` por OpenRouter (chave + billing)
  ou Ollama local (download de modelo multi-GB, GPU/RAM).
- **Dependências reais + instalação** — produção usa `python-telegram-bot`, `litellm`,
  `cryptography`, `aiosqlite`; precisa de um **venv** (este ambiente é
  *externally-managed*, PEP 668 — `pip install` direto falha).
- **Rede** (long-polling + LLM na nuvem) e **autostart** (o plano usa launchd, **só macOS**).
- **O wizard** de onboarding (`wizard.py`) — descrito em `doc/intelecto.md`, não incluído neste mínimo.

## Resumo

Núcleo de jarvis **construído e testado verde (9/9)** a partir do briefing —
mas o briefing precisa do `doc/intelecto.md` que ele referencia. Para ir ao ar
no Telegram, um usuário leigo ainda esbarra em token, chave de LLM, instalação de
deps em venv, rede e autostart. Use este diretório como referência viva do caminho
mercearia → código.
