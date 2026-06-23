# Plano — Incorporar ClaudeClaw, Hermes e AIOS nos sistemas de menus + mercearia + gerador

**Data:** 2026-06-22 · **Status:** aprovado (abordagem C, completo, só PT) · **Autor:** INTELECTO

## Objetivo

Colher dados reais de três novas fontes (ClaudeClaw, Hermes, AIOS) — somados aos
~36 data-points já minerados de OpenClaw + NanoBot — e incorporá-los em três
sistemas, melhorando as explicações da página:

1. **Mercearia** (`doc/framework-comparison-pt.html`) — cards de marca + itens de funcionalidade.
2. **Menus** (`doc/guia-funcionalidades.html`) — 8 corredores + arquiteturas.
3. **Gerador de prompt** (`exportCart()` na mercearia) — o briefing `.md` para Claude Code.

Escopo de idioma: **somente PT**. O gêmeo EN `framework-comparison.html` fica como está (tarefa futura).

## Fontes e natureza dos dados

| Fonte | Repo / curso | Natureza | Vendorizado? |
|---|---|---|---|
| **ClaudeClaw** | `earlyaidopters/claudeclaw-os` (TS/Py) | código real | **Não** (licença commercial/source-available) → upstream `github.com/earlyaidopters/claudeclaw-os` |
| **Hermes** | Nous Research `hermes-agent`; cursos `hermes21c`, `hermesagent` | conceitos (curso autoral) | Não — aponta upstream + cursos |
| **AIOS** | AGI Research/Rutgers `agiresearch/AIOS`+`Cerebrum`; curso `aiosagi` | conceitos (curso autoral) | Não — aponta upstream + curso |

Regra: **não fabricar números/specs**. Cada item vem do harvest real (ver `doc/` e os repos).

## Decisão de arquitetura (abordagem C)

A mercearia/gerador deixa de ser HTML hardcoded e passa a um **catálogo JS único**
(`doc/framework-data.js`), fonte de verdade que renderiza: (a) cards de marca,
(b) item-cards por corredor, (c) a matriz de comparação, e que alimenta (d) o
`exportCart()`. O `guia-funcionalidades.html` (doc de referência, baixa rotatividade)
recebe adições **pontuais na unha** (itens nos corredores + 3 arquiteturas novas).

Motivo: adicionar ~40 itens + matriz exige dado estruturado; um catálogo elimina o
risco "editar em dois lugares" e habilita a matriz de comparação.

### Modelo de dados — `doc/framework-data.js`

```js
const FRAMEWORKS = [
  { id:'openclaw', nome:'OpenClaw', tagline:'A Plataforma Original',
    lang:'TypeScript', cor:'#...', desc:'...', upstream:'...', vendor:'reference-repos/openclaw' },
  // ... zeroclaw, nanoclaw, nanobot, picoclaw, ironclaw, tinyclaw, agentzero,
  //     + claudeclaw, hermes, aios
];

const ITEMS = [
  { name:'Multi-Agent War Room', categoria:'communication',
    desc:'Sala de reunião com seu time de agentes...', sources:['claudeclaw'] },
  // ~40 itens novos + os ~54 existentes migrados
];

const ATTRS = [   // eixos da matriz de comparação
  { id:'multi-agente-vivo', label:'War Room multi-agente ao vivo',
    valores:{ openclaw:'parcial', claudeclaw:'sim', hermes:'sub-agentes', aios:'scheduler', ... } },
  // ~12-15 eixos de alto sinal
];
```

Renderização: funções `renderBrands()`, `renderAisles()`, `renderMatrix()` no load;
`exportCart()` lê a seleção (set de `item.name`) e monta o markdown a partir de `ITEMS`/`FRAMEWORKS`.

## Mudanças por sistema

### 1. Mercearia (`framework-comparison-pt.html` + novo `framework-data.js`)
- +3 marcas: **ClaudeClaw** ("O Quartel-General de Bolso"), **Hermes** ("O Agente que Cresce com Você"), **AIOS** ("O Kernel dos Agentes").
- Tags de origem novas: `source-claudeclaw`, `source-hermes`, `source-aios` (CSS).
- +~40 item-cards distribuídos nos corredores (ver harvest):
  - ClaudeClaw (~15): War Room (texto+voz), Hive Mind 3D, Mission Control, Acceptance Checks, Live Video Avatar, Exfiltration Guard, Hot-Reload Kill Switches, War Room Tool Policy, Memória 5-camadas c/ decaimento, Memory Hygiene & Sharing, Normalized Provider Engine (ACP), OAuth Health Monitor, Smart Model Routing, Cross-Agent Hive Log, Per-Agent Telegram Bots, Auto-Registered Skill Commands.
  - Hermes (~15): Autonomous Skill Generation, agentskills.io Portable Skills, Reflect-Step Memory Curation, Honcho User Modeling, Unified Message Gateway, Toggleable Toolsets, Tool Gateway (@hermes.tool), Build-Your-Own MCP, Multi-Brain Model Routing, Northstar Goal Function, Skill Composition/State Machines, Egress Allowlist + Sandbox, Local-First Data Map, Multi-Backend Deploy (7), Request Trace, Declarative config.yaml, Computer-Use Actions.
  - AIOS (~12): Agent-as-OS-Process Scheduling, LLM Kernel + Syscalls, Context Switch (snapshot/restore), Kernel+SDK Separation, Multi-LLM Core Routing, Agent Hub, Semantic FS (LSFS), Agentic Memory (A-MEM), Computer-Use via VM (LiteCUA), Framework Adapter Layer, Memory vs Storage, Multi-Agent Fan-out/Fan-in.
- Deduplicar contra os 54 itens existentes (não duplicar p.ex. SQLite FTS5, MCP, heartbeat, sub-agentes — adicionar `source` quando já existir).
- **Matriz de comparação** nova: ~12-15 eixos × frameworks (ver `ATTRS`).

### 2. Menus (`guia-funcionalidades.html`)
- Itens novos refletidos nos 8 corredores (subset curado dos acima).
- **6 → 9 arquiteturas** na seção "As Arquiteturas em Detalhe":
  - **ClaudeClaw** — "Enxame Local Multi-Agente + Hive Bus" (badge CC, N agentes-bot na mesma máquina/DB, delegam via `@agente:`, War Room ao vivo, barramento `hive_mind` = memória+visual 3D; malha de contenção: kill-switches + tool-policy default-deny + exfiltration guard).
  - **Hermes** — "Reflective Loop c/ Memória Auto-Curada + Skills Autônomas" (perceive→act→reflect→save; reflect usa modelo barato pra curar memória e detectar workflows repetidos → skills auto-geradas; model-agnostic por papel).
  - **AIOS** — "Agente-como-Processo-de-SO / Kernel LLM" (LLM embutida no kernel; agentes escalonados (FIFO/Round-Robin); context switch snapshot/restore; syscalls auditáveis; SDK Cerebrum separado; LangChain/AutoGen/CrewAI rodam EM CIMA).
- Atualizar o índice/nav do topo (badges, âncoras `#arch-claudeclaw`, `#arch-hermes`, `#arch-aios`).

### 3. Gerador (`exportCart()`)
- Lê de `FRAMEWORKS`/`ITEMS` (não mais do DOM cru).
- Aponta os repos de referência certos por item: ClaudeClaw → upstream `github.com/earlyaidopters/claudeclaw-os` (não vendorizado — licença commercial), Hermes → `github.com/NousResearch/hermes-agent` + curso, AIOS → `github.com/agiresearch/AIOS` + curso.
- "Implementation Notes for Claude Code" enriquecidas (princípios + ponteiro a `doc/intelecto.md`).
- **Corrigir bug de nome**: padronizar o arquivo gerado (`meu-assistente.md`) e bater com `como-construir.html` (que oscila entre `my-framework-ingredients.md` e `meu-assistente.md`).

### 4. Melhorar explicações ("a página")
- Reescrever as descrições de cada framework p/ baterem com o harvest real.
- Expandir o explicador de conceitos (Gateway/Sandbox/Tools/Memória) com os conceitos novos: enxame multi-agente, reflective loop, agente-como-processo, memória auto-curada, defesa anti-injeção.
- **Corrigir inconsistência Docker × sem-Docker** entre README/CLAUDE.md (no-Docker) e os guias HTML (Docker first-class) — texto único e claro.
- Glossário curto dos novos eixos de comparação.

### 5. Ponto 6 — links mortos do curso (correção mínima)
- `curso/trilha1` linka `../trilha2/` e `../trilha3/` que não existem (404).
- Neutralizar/ocultar os dois links (selo "em breve") no nav e rodapé da trilha1.
- **Fora de escopo**: criar o conteúdo de trilha2/trilha3 (tarefa futura separada).

## Verificação (fechar o loop)
- Abrir `framework-comparison-pt.html` em navegador headless e checar:
  - nº de cards de marca = 12; nº de item-cards = (54 + novos, deduplicados); matriz renderiza.
  - `exportCart()` com uma seleção gera markdown com os ponteiros de repo certos e nome `meu-assistente.md`.
- `guia-funcionalidades.html`: 9 arquiteturas com âncoras válidas; índice do topo casa.
- Sem links quebrados; revisão adversarial dos dados (não fabricados).

## Fora de escopo
- Gêmeo EN (`framework-comparison.html`).
- Conteúdo de curso trilha2/trilha3.
- Vendorizar Hermes/AIOS (só ponteiros).
- Código Python do INTELECTO em si.
