# Requisitos de Hardware para Ollama

## VPS Recomendada

| Recurso | Minimo | Recomendado |
|---------|--------|-------------|
| RAM | 8 GB | 16 GB |
| CPU | 2 vCPUs | 4+ vCPUs |
| Disco | 40 GB SSD | 80 GB SSD |
| Swap | 4 GB | 8 GB |

## Modelos por Tamanho de RAM

### 8 GB RAM (VPS basica)

| Modelo | Parametros | RAM Usada | Qualidade |
|--------|------------|-----------|-----------|
| llama3.2 | 3B | ~2 GB | Boa para tarefas simples |
| phi3 | 3.8B | ~2.5 GB | Rapido, bom para codigo |
| gemma2:2b | 2B | ~1.5 GB | Leve, respostas rapidas |
| qwen2.5:3b | 3B | ~2 GB | Bom para chat |

### 16 GB RAM

| Modelo | Parametros | RAM Usada | Qualidade |
|--------|------------|-----------|-----------|
| llama3.2 | 3B | ~2 GB | Excelente |
| llama3.1:8b | 8B | ~5 GB | Muito boa |
| mistral | 7B | ~4.5 GB | Excelente para codigo |
| codellama:7b | 7B | ~4.5 GB | Especializado em codigo |
| deepseek-coder:6.7b | 6.7B | ~4 GB | Otimo para codigo |

### 32 GB+ RAM

| Modelo | Parametros | RAM Usada | Qualidade |
|--------|------------|-----------|-----------|
| llama3.1:70b | 70B | ~40 GB | Estado da arte |
| mixtral | 8x7B | ~26 GB | Excelente |
| codellama:34b | 34B | ~20 GB | Melhor para codigo |

## Dicas de Otimizacao

### Swap (obrigatorio para 8GB RAM)

```bash
# Criar 4GB de swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Ajustar swappiness (menor = usa menos swap)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Limite de Memoria do Container

O docker-compose.ollama.yml ja limita o Ollama a 6GB:

```yaml
deploy:
  resources:
    limits:
      memory: 6G
```

Ajuste conforme sua VPS:
- 8 GB RAM: `memory: 6G` (deixa ~2GB para sistema + OpenClaw)
- 16 GB RAM: `memory: 12G`
- 32 GB RAM: `memory: 28G`

### Quantizacao

Modelos quantizados usam menos RAM:

```bash
# Modelo completo (mais qualidade, mais RAM)
ollama pull llama3.1:8b

# Modelo quantizado Q4 (menos RAM, qualidade boa)
ollama pull llama3.1:8b-instruct-q4_0
```

## Provedores de VPS Recomendados

| Provedor | Plano | RAM | Preco/mes |
|----------|-------|-----|-----------|
| Hetzner | CPX31 | 8 GB | ~EUR 15 |
| Hetzner | CPX41 | 16 GB | ~EUR 30 |
| DigitalOcean | Basic | 8 GB | ~$48 |
| Vultr | High Freq | 8 GB | ~$48 |
| Contabo | VPS M | 16 GB | ~EUR 12 |

## Monitoramento

```bash
# Ver uso de memoria do Ollama
docker stats openclaw-ollama

# Ver modelos carregados
docker compose exec ollama ollama ps

# Ver espaco usado pelos modelos
docker compose exec ollama du -sh /root/.ollama/models
```

## Troubleshooting

### Modelo muito lento

- Verifique se ha swap em uso excessivo: `free -h`
- Considere um modelo menor
- Aumente a RAM da VPS

### Out of Memory (OOM)

- Ollama descarrega modelos inativos apos 5 minutos
- Limite a memoria do container
- Use modelos quantizados (q4, q5)

### Modelo nao carrega

- Verifique espaco em disco: `df -h`
- Modelos ficam em `/root/.ollama/models` dentro do container
- Volume `ollama-data` persiste os modelos
