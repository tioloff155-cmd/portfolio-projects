# OmniQuant HFT Bot: Master Execution Plan 🚀

> **Contexto para Mistral 7B (LM Studio)**: Você é a unidade de processamento e execução deste projeto. A inteligência estratégica (Antigravity) desenhou a arquitetura atual baseada em HFT real (Anti-ruído, RSI Momentum e Super Memória de Kelly). Seu objetivo é seguir as instruções de modificação técnica mantendo a integridade assíncrona e a segurança do capital.

## 🏗️ Arquitetura do Sistema
O bot opera em um loop assíncrono (`asyncio`) para garantir latência mínima e processamento não bloqueante.

- **`app.py`**: Servidor Flask + SocketIO. Ponte de comando entre o usuário e o motor.
- **`strategy.py`**: O núcleo algorítmico.
  - `StateManager`: Agregação temporal (velas sintéticas de 15s).
  - `IndicatorCalculator`: Métodos estáticos extremamente rápidos para EMA e RSI.
  - `OmniQuantBot`: Orquestrador de WebSocket, gestão de risco e execução de ordens.
- **`omni_quant.db`**: SQLite para persistência de estado e aprendizado de máquina (Super Memória).

## 🎯 Objetivos de Refinamento (Próximos Passos)
1. **Otimização de Latência**: Revisar os bloqueios (`asyncio.Lock`) no StateManager para garantir que múltiplos pares não gerem contenção.
2. **Refinamento da Super Memória**: Melhorar o cálculo do Critério de Kelly para incluir a volatilidade recente da moeda como fator de redução de risco.
3. **Interface de Feedback**: Adicionar emissões de logs mais detalhados sobre o "porquê" de o filtro de RSI ter negado uma entrada específica.

## 📜 Diretrizes para a "Máquina" (Mistral 7B)
1. **Preservar Async/Await**: Nunca use funções bloqueantes (como `time.sleep`) dentro dos loops de estratégia. Use `await asyncio.sleep`.
2. **Contexto de Erro**: Se encontrar um `KeyError` ou `AttributeError`, verifique a sincronização entre a memória (`active_positions`) e o carregamento do DB.
3. **Padrão de Código**: Mantenha o estilo de comentários em português para o operador e inglês para documentação técnica interna.
4. **Segurança**: Nunca ignore as taxas de 0.1% na simulação; elas são o que separam um bot lucrativo de um bot "iludido".

---
**Comando Inicial**: *Aguardando entrada do operador via Antigravity Thinking.*
