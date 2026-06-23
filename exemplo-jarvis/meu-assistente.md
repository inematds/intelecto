# My Custom AI Framework - Ingredient List

> **Purpose**: This document defines the selected features, skills, and architectural patterns
> for building a custom AI agent framework. Each item includes a description of what it does,
> which reference frameworks implement it, and enough context for Claude Code to understand
> the implementation requirements.
>
> **Reference repos**: Bundled in `reference-repos/` (openclaw, nanobot). ClaudeClaw (earlyaidopters), Hermes (Nous Research) and AIOS (AGI Research/Rutgers) are external upstreams referenced below.
> **Full analysis**: See `doc/intelecto.md` (the full build plan).

---

**Total selected items: 21**

## Identidade e Personalidade

### 1. Soul.md Personality File

**What it does**: Defina a personalidade, os valores e o estilo de comunicação da sua IA em um arquivo de texto simples. Como escrever uma ficha de personagem.

**Reference implementations**: OpenClaw, NanoBot, ZeroClaw, PicoClaw

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`

---

### 2. Dynamic Behavior Rules

**What it does**: Altere o comportamento da IA no meio da conversa. Sem necessidade de reinicialização. Ela se adapta imediatamente.

**Reference implementations**: Agent Zero, OpenClaw

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories

---

## Canais de Comunicação

### 1. Telegram Bot

**What it does**: Configuração mais fácil — apenas um token. Suporte a mídia rica, botões inline, compartilhamento de arquivos. Ótimo para equipes.

**Reference implementations**: OpenClaw, NanoBot, PicoClaw, ZeroClaw, IronClaw, TinyClaw, ClaudeClaw, Hermes

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`
- ClaudeClaw (earlyaidopters): upstream `github.com/earlyaidopters/claudeclaw-os` — TypeScript/Node + Python (warroom); licença source-available
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

## Memória e Conhecimento

### 1. Two-Layer Memory

**What it does**: Camada 1: Fatos rápidos (MEMORY.md). Camada 2: Log de histórico pesquisável. Simples, mas eficaz.

**Reference implementations**: NanoBot, PicoClaw

**Where to find reference code**:
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`

---

### 2. SQLite FTS5 / BM25 Recall

**What it does**: Memória persistente local em 3 camadas (conversas com TTL, fatos sem TTL, skills) com busca full-text BM25 — sem embeddings, offline, recall em milissegundos.

**Reference implementations**: Hermes, INTELECTO

**Where to find reference code**:
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

### 3. Session Auto-Compaction

**What it does**: Quando as conversas ficam muito longas, resume automaticamente as partes antigas para manter a IA rápida enquanto preserva informações essenciais.

**Reference implementations**: NanoClaw, IronClaw

---

### 4. Reflect-Step Memory Curation

**What it does**: Loop perceive->act->reflect->save: um modelo barato (&lt;1k tokens) decide o que vale ser lembrado e cura a memória sozinho, em vez de você ditar tudo.

**Reference implementations**: Hermes

**Where to find reference code**:
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

## Integrações e Protocolos

### 1. OpenRouter 100+ Models

**What it does**: Acesse Claude, GPT-4, Gemini, Mistral, DeepSeek, Llama e mais de 100 modelos com uma única chave de API. Troque de modelo sem mudar o código. Ideal como provider principal com Ollama como fallback local.

**Reference implementations**: OpenRouter, INTELECTO, NanoBot, Hermes, ClaudeClaw

**Where to find reference code**:
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`
- ClaudeClaw (earlyaidopters): upstream `github.com/earlyaidopters/claudeclaw-os` — TypeScript/Node + Python (warroom); licença source-available
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

### 2. Local LLM Support

**What it does**: Execute modelos de IA no seu próprio computador. Zero custo de API. Privacidade total. Sem necessidade de internet. Use junto com OpenRouter: nuvem quando precisa de potência, local quando precisa de privacidade.

**Reference implementations**: OpenClaw, ZeroClaw, PicoClaw, Agent Zero, NanoBot, INTELECTO, Hermes, AIOS

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`
- AIOS (AGI Research/Rutgers): upstream `github.com/agiresearch/AIOS` + Cerebrum; curso local `aiosagi`

---

### 3. MCP Protocol

**What it does**: Padrão universal para conectar IA a ferramentas externas. Um protocolo, milhares de integrações. O "USB" das ferramentas de IA.

**Reference implementations**: OpenClaw, NanoBot, IronClaw, Agent Zero, ClaudeClaw, Hermes

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`
- ClaudeClaw (earlyaidopters): upstream `github.com/earlyaidopters/claudeclaw-os` — TypeScript/Node + Python (warroom); licença source-available
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

### 4. Multi-Provider Failover

**What it does**: Se o Claude cair, alterne automaticamente para o GPT. Se o GPT estiver lento, tente o Gemini ou OpenRouter. Com OpenRouter você tem 100+ modelos como fallback automático em uma única chave. Nunca perca o serviço.

**Reference implementations**: IronClaw, OpenClaw, ZeroClaw, OpenRouter, Hermes

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

### 5. Skills System

**What it does**: Instale novas capacidades como aplicativos no celular. "Instalar skill de clima" ou "instalar skill do GitHub." Sem necessidade de codificação.

**Reference implementations**: OpenClaw, PicoClaw, NanoClaw, Agent Zero, TinyClaw, Hermes, ClaudeClaw

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- ClaudeClaw (earlyaidopters): upstream `github.com/earlyaidopters/claudeclaw-os` — TypeScript/Node + Python (warroom); licença source-available
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

## Segurança e Proteção

### 1. Encrypted Secret Store

**What it does**: Chaves de API armazenadas com criptografia de nível militar (ChaCha20). Mesmo que alguém roube o arquivo, não conseguirá lê-lo.

**Reference implementations**: ZeroClaw, IronClaw

---

### 2. Command Blocklist

**What it does**: Bloqueia automaticamente comandos que podem danificar seu sistema (deletar tudo, formatar discos, reiniciar, etc.)

**Reference implementations**: PicoClaw, NanoBot, ZeroClaw

**Where to find reference code**:
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`

---

### 3. Execution Approval Gates

**What it does**: A IA deve pedir sua permissão antes de executar certos comandos. Três níveis: somente leitura, supervisionado, autonomia total.

**Reference implementations**: OpenClaw, ZeroClaw

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories

---

### 4. Prompt Injection Defense

**What it does**: Detecta e bloqueia tentativas de enganar sua IA com instruções ocultas em páginas web ou mensagens. Detecção de padrões em múltiplas camadas.

**Reference implementations**: IronClaw, Hermes, ClaudeClaw

**Where to find reference code**:
- ClaudeClaw (earlyaidopters): upstream `github.com/earlyaidopters/claudeclaw-os` — TypeScript/Node + Python (warroom); licença source-available
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

### 5. Outbound Exfiltration Guard

**What it does**: Varre toda resposta de saída por regex (chaves de API, tokens Slack/GitHub, AWS, hex longos) e redige segredos antes de mandar pro chat — barreira contra vazamento por prompt-injection.

**Reference implementations**: ClaudeClaw

**Where to find reference code**:
- ClaudeClaw (earlyaidopters): upstream `github.com/earlyaidopters/claudeclaw-os` — TypeScript/Node + Python (warroom); licença source-available

---

## Automação e Agendamento

### 1. Cron Scheduling

**What it does**: Execute tarefas em um cronograma: "toda segunda-feira às 9h, me envie um briefing." Funciona como um despertador confiável para sua IA.

**Reference implementations**: OpenClaw, NanoClaw, NanoBot, PicoClaw, ZeroClaw, TinyClaw, IronClaw

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`

---

### 2. Heartbeat System

**What it does**: A IA acorda a cada 30 minutos para verificar se algo precisa de atenção. Proativa, não apenas reativa.

**Reference implementations**: OpenClaw, PicoClaw, NanoBot, IronClaw, ZeroClaw, Hermes

**Where to find reference code**:
- OpenClaw (`./reference-repos/openclaw/`): TypeScript, check `skills/` and `extensions/` directories
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

### 3. Background Sub-Agents

**What it does**: Crie trabalhadores de IA auxiliares para tarefas longas. O agente principal permanece responsivo enquanto os trabalhadores fazem o trabalho pesado em segundo plano.

**Reference implementations**: PicoClaw, NanoBot, Agent Zero, TinyClaw, Hermes

**Where to find reference code**:
- NanoBot (`./reference-repos/nanobot/`): Python, check `nanobot/skills/` and `nanobot/agent/tools/`
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

## Skills Integradas e Ferramentas Prontas

### 1. Autonomous Skill Generation

**What it does**: O agente detecta um workflow repetido (>=3x) no passo reflect e ele mesmo escreve uma SKILL.md em draft para você aprovar — habilidades que nascem do uso, sem programar.

**Reference implementations**: Hermes

**Where to find reference code**:
- Hermes (Nous Research): upstream `github.com/NousResearch/hermes-agent`; curso local `hermes21c`

---

## Implementation Notes for Claude Code

When building this framework, follow these principles:

1. **Start with the reference code** ...
2. **Prefer simplicity** ...
3. **Keep it modular** ...
4. **Security by default** ...
5. **Start single-agent** ...
6. **Guard the boundaries at runtime** ...
7. **Full deep-dive reference** - See `doc/intelecto.md`.

---
*Generated from the AI Agent Framework Grocery Store comparison tool.*
