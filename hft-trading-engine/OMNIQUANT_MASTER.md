# 🧠 OMNIQUANT: PROTOCOLO MESTRE
**Motor HFT & Configuração da Matriz Quantitativa**
*Versão:* 8.1 - "O Núcleo Quântico de Nível PhD"
*Data:* 2026-04-08

## 1. Premissa do Projeto
OmniQuant é um motor autônomo de negociação de criptomoedas em alta frequência (HFT) desenvolvido para resiliência extrema e análise estatística de grau institucional. Construído em Python e operando via um Servidor Web local (Flask + SocketIO), ele renuncia completamente à utilização de gráficos visuais (Charting) em favor de uma abordagem de "Dados Brutos & Lógica Pura".

### O Objetivo
Capturar micro-movimentos em criptoativos de alta liquidez utilizando vetores matemáticos robustos (Spread, Tendência, RSI, Confiança), gerenciando o risco dinamicamente através do Critério de Kelly, e sobrevivendo à volatilidade extrema do mercado através de "Escudos de Pânico" automatizados.

## 2. Arquitetura Base
- **Linguagem**: Python 3.12+ (Arquitetura orientada a Asyncio)
- **Frontend**: Matriz Institucional em Fundo Preto (HTML5, TailwindCSS, SocketIO)
- **Banco de Dados**: SQLite no modo `PRAGMA journal_mode=WAL` para leitura e escrita assíncrona concorrente.
- **Comunicação**: API de WebSocket da Binance (`wss://stream.binance.com:9443/ws/...@aggTrade`)
- **Fluxo de Execução**: 1 Thread Principal (Web) + 1 Thread em Segundo Plano (Motor HFT) gerenciando dezenas de rotinas Async Workers.

## 3. Frontend "Quantum Matrix"
A interface de usuário expurgou explicitamente todas as dependências de TradingView e Chart.js. Ela funciona de forma semelhante a um Terminal Bloomberg:
- **Zero Gráficos Plásticos**: Foco em renderização de dados de baixíssima latência.
- **Métricas Matemáticas Avançadas**: Último Preço, Spread da EMA % (Diferença exata entre EMA9 e EMA20), Contexto do RSI 14, Confiança do Vetor (Lógica Touro/Urso embasada na EMA200).
- **Interface de Controle**: F5 para Executar, ESC para Parada de Emergência (Halt) e um botão vermelho de "Liquidação de Pânico".
- **Modo de Diagnóstico (SYSTEST)**: Contorna as regras do mercado real para acionar um sinal de diagnóstico (Ping) que atesta a saúde das rotinas internas de envio e memória, sem de fato deduzir da sua banca virtual.

## 4. Estratégia Quantitativa
O bot atua sobre um proxy multi-tempo derivado de dados enviados "tick-a-tick" transmutados para Médias Móveis Internas.
- **Filtro de Tendência**: Só considera operações COMPRADAS (`LONG`) se o `Preço Atual > EMA200`.
- **Gatilho Principal**: EMA9 cruza a EMA20 de baixo para cima.
- **Filtro de Momento**: O RSI (14) deve estar saudável entre 45 e 68, E um RSI customizado derivado da EMA70 precisa apontar extremos sistêmicos (< 50 ou > 95) para justificar anomalia e expansão iminente de volatilidade.
- **Gerenciamento de Risco**:
  - Alvos de Take Profit e Stop Loss configuráveis (Padrão: TP 0.50%, SL 0.30%).
  - Stop de Segurança Dinâmico (Trailing Stop) que inicia após o TP estourar (trava em `pnl - 0.001`).
  - Criteiro de Kelly que calibra de forma orgânica o tamanho ideal de cada entrada (`0.02` até `0.25` do saldo disponível) baseado no ranqueamento histórico de assertividade de ganhos vs perdas (Winrate).

## 5. Marcos de Desenvolvimento & Correções (Patches)
Durante sua lapidação rigorosa, gargalos críticos foram isolados e destruídos:

### 🔴 O Gatilho da "Morte por Loop" (Event-Loop Starvation Fix)
*Problema:* Requisições estruturadas que ficavam em fila esperando pela API (`requests.get`) travavam a velocidade dos Workers que leem preço a preço no ar, causando atraso de dezenas de segundos e estouro cego no Stop Loss.
*Solução:* Transição completa do código para formato Não-Bloqueante `aiohttp` no aquecimento (Warm-up) e absorção de ticks absolutos via Websockets contínuo (`market_watcher`).

### 🔴 Síndrome da "Thread Zumbi" (Zombie Thread Fix)
*Problema:* Desligar e ligar a interface pela Tela causava criação duplicatas do bot Python correndo no porão do projeto, corrompendo a persistência do banco em concorrência.
*Solução:* Gestão da validade de estado em `_bot_thread` no core `app.py`, não permitindo um novo gatilho Web começar a negociar se sua vida anterior continuava ecoando.

### 🔴 A Corrupção do SQLite Lock
*Problema:* Concorrência insana de atualizações por segundo causava trancamento na hora de salvar o banco "Database Locked".
*Solução:* Criação imediata da `asyncio.Queue` servida ritmicamente por um laço especializado em apenas despejar dados para salvar (`db_writer_loop`), fundido com o PRAGMA `WAL` nativo moderno do sqlite3.

### 🔴 O Acidente Fatal do State Object
*Problema:* Ao rodar uma operação as rotas tentavam acessar a variável em RAM `state_obj = await self.state.get_state(symbol)` antes que os 200 dados vitais estourassem na conexão, lançando a tela do Kernel direto a terra.
*Solução:* Enrolamos todo núcleo de ação do `Symbol Worker` em blocos inquebráveis de checagem. Nenhum loop cai duro caso um número não exista ou a rede pipoque e demore 5 milissegundos a mais; ele cospe `⚠️ KERNEL FAULT` amarelado à console, respira dois compassos de tempo de erro e reinserem-se vivamente de volta na guerra.

## 6. Protocolos de Segurança Tática
- **Escudos de Pânico**: Rasga através de qualquer regra em vigência e despenca todos os ativos comprados pro caixa.
- **Ordem Inicial Absoluta (MVR)**: Finta restrições do bot sob as taxas globais forçando lotes em `$10` cravados pois a rede Binance repele ordens em frações de centavos não qualificadas.
- **Força do Horizonte Diário**: Autoliquidação forçosa de mesa caso a bateria encerre as fronteiras da hora sagrada (07:00 AM), varrendo a mesa pro dia subsequente.

## 7. Status do Projeto Corrente
O motor bate estavelmente no modo "Paper Trading" (Simulação de Negócios) com uma banca oficial injetada de salda base (ex: 1000 reais injetados via Banco de Dados). O simulador internalizou cada engrenagem taxativa das centrais reais com absoluta conformidade técnica.

***
*"Nós não prevemos o futuro. Nós lemos a matemática e agimos na probabilidade."*
