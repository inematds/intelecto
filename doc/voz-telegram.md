# INTELECTO — voz no Telegram (mandar e receber áudio)

Data: 25/09/2026. Complementa a **Task 4.2** de [intelecto.md](intelecto.md). Ali a nota de voz é "salva em arquivo temporário; transcrição é feature futura". Este documento é essa feature.

## Situação

- O INTELECTO ainda não tem canal Telegram rodando: `exemplo-jarvis/jarvis/channels/telegram.py` é **estrutural** (sem token e sem rede, por design).
- Portanto, hoje **não há voz**. Abaixo estão o modo de uso e a implementação para quando o canal real existir.
- Referências que já funcionam no ecossistema:
  - **openpcbotv2**: voz em produção, com Groq para transcrever e ElevenLabs para falar.
  - **openpcbotv3**: [docs/VOZ-TELEGRAM.md](https://github.com/inematds/openpcbotv3/blob/main/docs/VOZ-TELEGRAM.md), com o plano de voz local via inemavox.

## 1. Como vai funcionar para quem usa

| Você faz | O INTELECTO faz |
|---|---|
| Manda uma **nota de voz** | Transcreve, responde em **texto** (com "🎙 Você disse: …" no topo, para conferir) **e em voz** |
| Manda **texto** | Responde em texto. Com `/voz sempre` ligado, também em voz |
| `/voz` | Mostra o modo atual |
| `/voz espelho` (padrão) | Voz só quando você mandou voz |
| `/voz sempre` | Toda resposta vem também em áudio |
| `/voz off` | Nunca responde em áudio; continua entendendo a voz recebida |

O áudio da resposta é um **resumo falável** (até ~400 caracteres, começando pelo principal). O texto completo sempre vai junto.

## 2. Arquitetura (encaixa nos contratos existentes)

```
Telegram (long-polling)
  → channels/telegram.py
      message.voice / message.audio
        → baixa (get_file) → ~/.intelecto/tmp/<id>.ogg
        → voice/stt.py  → texto
        → IncomingMessage(text=texto, media=[ogg], meta={"voice": True})
  → agent/loop.py  (inalterado: não sabe que veio de voz)
  → OutgoingMessage(text=…, meta={"speak": True|False})
  → channels/telegram.py
        send_message(texto)              ← sempre
        se speak: voice/tts.py → ogg → send_voice(reply_to=texto)
```

O agente não muda. A voz é assunto do **canal**. Isso segue a regra do projeto: um subsistema novo entra implementando a interface, sem mexer no resto.

### Arquivos novos

```
intelecto/voice/
  base.py      # BaseSTT.transcribe(path) -> str ; BaseTTS.speak(text) -> bytes (ogg/opus)
  stt.py       # GroqSTT, OpenAISTT, InemavoxSTT (local, opcional)
  tts.py       # OpenAITTS, ElevenLabsTTS, MacSayTTS (macOS: `say` + ffmpeg), InemavoxTTS
  speakable.py # limpa markdown/links/emojis, valores por extenso, corta em ~400 chars
```

### Contratos (no estilo de `doc/intelecto.md`)

```python
class BaseSTT(ABC):
    name: str
    @abstractmethod
    async def transcribe(self, audio_path: Path, lang: str = "pt") -> str: ...

class BaseTTS(ABC):
    name: str
    @abstractmethod
    async def speak(self, text: str, lang: str = "pt") -> bytes:  # OGG/Opus pronto p/ send_voice
        ...
```

### Handler no canal (python-telegram-bot v21+)

```python
async def _on_voice(update, context):
    msg = update.effective_message
    if not self._allowed(update):          # mesma regra de DM/allowlist do texto
        return
    f = await (msg.voice or msg.audio).get_file()
    path = TMP / f"{msg.message_id}.ogg"
    await f.download_to_drive(path)
    await context.bot.send_chat_action(msg.chat_id, "typing")
    try:
        text = await self.stt.transcribe(path)
    except Exception:
        await msg.reply_text("Não consegui transcrever o áudio. Pode mandar de novo ou por texto?")
        return
    finally:
        path.unlink(missing_ok=True)
    await self.on_message(IncomingMessage(text=text, chat_id=msg.chat_id,
                                          meta={"voice": True, "heard": text}))

async def send(self, out: OutgoingMessage):
    for chunk in split_message(out.text):
        await self.bot.send_message(out.chat_id, chunk)
    if out.meta.get("speak") and self.tts:
        try:
            audio = await self.tts.speak(speakable(out.text))
            await self.bot.send_voice(out.chat_id, audio)
        except Exception as e:
            log.warning("tts falhou: %s", e)   # texto já foi; nunca derruba a resposta
```

A decisão `speak` sai de `/voz` (guardado em `~/.intelecto/config.json`, por chat) e de `meta["voice"]` da mensagem recebida.

### Conversão para nota de voz

O Telegram só mostra como **nota de voz** (a bolinha com a onda) um arquivo OGG/Opus. Qualquer outro formato vira um "arquivo de áudio".

```bash
ffmpeg -y -i in.mp3 -ac 1 -ar 48000 -c:a libopus -b:a 32k out.ogg
```

## 3. Provedores — qual usar

| Provedor | STT | TTS | Custo | Quando |
|---|---|---|---|---|
| **Groq** (`whisper-large-v3-turbo`) | ✅ | — | Baixo, pago por uso | Padrão de STT: rápido e simples. É o que o openpcbotv2 usa |
| **OpenAI** (`gpt-4o-mini-transcribe` / `gpt-4o-mini-tts`) | ✅ | ✅ | Pago por uso | Uma chave só para os dois lados |
| **ElevenLabs** | — | ✅ | Por caractere | A voz mais natural |
| **macOS `say` + ffmpeg** | — | ✅ | Grátis | Reserva offline no Mac (plataforma-alvo do INTELECTO) |
| **inemavox** (`localhost:8010`) | ✅ | ✅ (`chatterbox`, voz `rachel`) | Grátis, usa a GPU | Na máquina Linux com GPU do ecossistema INEMA |

A ordem é configurável. Padrão sugerido: STT = Groq → inemavox; TTS = ElevenLabs → OpenAI → `say`. A escolha e as chaves entram no **wizard** (`intelecto setup`), e as chaves vão para o `~/.intelecto/.secrets` (Fernet), como as demais.

Chamadas do inemavox, se for usado:

```text
POST /api/jobs/transcribe/upload   multipart file=<ogg>, config_json={...}  → job
POST /api/jobs/tts                 {"text":"…","engine":"chatterbox","voice":"rachel","lang":"pt"} → job
GET  /api/jobs/<id>                → status ;  /transcript  ou  /audio  quando completed
```

## 4. Segurança e limites

- **Só voz de quem pode falar com o bot:** a mesma checagem de DM e allowlist do texto, **antes** de baixar o arquivo. Estranhos não gastam transcrição.
- Teto de 5 minutos / 10 MB por áudio recebido. Acima disso, recusar com uma linha.
- O arquivo temporário é apagado depois da transcrição, com ou sem sucesso.
- A transcrição é **dado de entrada**, igual a texto digitado: passa pelo mesmo `security/safety.py` quando vira comando de ferramenta.
- Registrar no `audit.log`: provedor, duração do áudio, latência e custo estimado. Não registrar o conteúdo.

## 5. Testes

- `speakable.py`: markdown, links, emojis, valores, corte em 400 caracteres.
- Fallback: um STT falso que lança exceção faz passar para o próximo, e um TTS falso que lança exceção deixa só o texto enviado.
- Handler: um chat fora da allowlist não baixa o arquivo (mock do `get_file` não é chamado).
- `/voz`: o modo persiste no config e sobrevive a um reinício.
- Offline (como o `exemplo-jarvis`): provedores `Mock*` em `voice/` para os testes rodarem sem rede.

## 6. Onde entra no plano

É uma extensão da Task 4.2, depois que o canal Telegram real existir. Acrescenta 2 dependências opcionais: `httpx` para chamar os provedores e o `ffmpeg` no sistema. Mantém o "sem frameworks inchados": nada de SDK pesado de voz, só chamadas REST.
