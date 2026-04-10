import time
import threading
import sqlite3
import numpy as np
import logging
import collections
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("omniquant_kernel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OmniQuant")


# ═══════════════════════════════════════════════════════════════
#  DATABASE MANAGER — Persistência SQLite (adaptada para opções)
# ═══════════════════════════════════════════════════════════════
class DatabaseManager:
    """Manages SQLite database operations for bot persistence and state."""
    def __init__(self, db_name='omni_quant.db'):
        self.db_name = db_name
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_name, timeout=10.0)

    def _init_db(self):
        """Initializes the database schema for IQ Option digital options."""
        with self._get_conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            # Pending orders — trades esperando resultado da IQ
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_orders (
                    order_id TEXT PRIMARY KEY,
                    asset TEXT,
                    direction TEXT,
                    amount REAL,
                    duration INTEGER,
                    placed_at REAL
                )
            """)
            # Trades finalizados — histórico completo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT,
                    direction TEXT,
                    amount REAL,
                    pnl_usd REAL,
                    pnl_pct REAL,
                    result TEXT,
                    time REAL
                )
            """)
            # Estado persistente (saldo virtual de referência)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value REAL
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO state (key, value) VALUES ('balance', 0.0)")
            conn.commit()

    def save_pending(self, order_id, asset, direction, amount, duration):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pending_orders (order_id, asset, direction, amount, duration, placed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(order_id), asset, direction, amount, duration, time.time())
            )

    def delete_pending(self, order_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM pending_orders WHERE order_id = ?", (str(order_id),))

    def load_pending(self) -> List[Dict]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_orders")
            rows = cursor.fetchall()
            return [
                {"order_id": r[0], "asset": r[1], "direction": r[2],
                 "amount": r[3], "duration": r[4], "placed_at": r[5]}
                for r in rows
            ]

    def save_balance(self, balance):
        with self._get_conn() as conn:
            conn.execute("UPDATE state SET value = ? WHERE key = 'balance'", (balance,))

    def load_balance(self) -> float:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM state WHERE key = 'balance'")
            row = cursor.fetchone()
            return row[0] if row else 0.0

    def set_lock(self, timestamp: float):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES ('locked_until', ?)", (timestamp,))

    def get_lock(self) -> float:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM state WHERE key = 'locked_until'")
            row = cursor.fetchone()
            return row[0] if row else 0.0

    def save_trade(self, asset, direction, amount, pnl_usd=0, pnl_pct=0, result='', time_val=None):
        if not time_val:
            time_val = time.time()
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO trades (asset, direction, amount, pnl_usd, pnl_pct, result, time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (asset, direction, amount, pnl_usd, pnl_pct, result, time_val))

    def load_trades(self, limit=50) -> List:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY time DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "asset": r[1], "direction": r[2], "amount": r[3],
                    "pnl_usd": r[4], "pnl_pct": r[5], "result": r[6], "time": r[7]
                } for r in rows
            ]

    def backup_database(self, dest_path='backup_omni_quant.db'):
        try:
            with sqlite3.connect(self.db_name) as src:
                with sqlite3.connect(dest_path) as dst:
                    src.backup(dst)
            logger.info("Database backup created successfully.")
        except Exception as e:
            logger.error(f"Database backup failed: {e}")


# ═══════════════════════════════════════════════════════════════
#  QUANT MEMORY — Cache in-memory para Kelly Criterion
# ═══════════════════════════════════════════════════════════════
class QuantMemory:
    """In-memory cache for ultra-fast kelly evaluation without DB locking."""
    def __init__(self, db_manager):
        self.stats = {}
        self.global_wins = 0
        self.global_losses = 0
        self.recent_outcomes = []
        try:
            trades = db_manager.load_trades(limit=1000)
            for t in reversed(trades):
                sym = t['asset']
                if sym not in self.stats:
                    self.stats[sym] = {"wins": 0, "losses": 0, "outcomes": []}
                is_win = 1 if t['pnl_usd'] > 0 else 0
                if is_win:
                    self.stats[sym]["wins"] += 1
                    self.global_wins += 1
                else:
                    self.stats[sym]["losses"] += 1
                    self.global_losses += 1
                self.stats[sym]["outcomes"].insert(0, is_win)
                self.recent_outcomes.insert(0, is_win)
                if len(self.stats[sym]["outcomes"]) > 20:
                    self.stats[sym]["outcomes"].pop()
                if len(self.recent_outcomes) > 50:
                    self.recent_outcomes.pop()
        except:
            pass

    def get_recent_outcomes(self, symbol, limit=20):
        if symbol not in self.stats:
            return []
        return self.stats[symbol]["outcomes"][:limit]

    def record_trade(self, symbol, pnl_usd):
        if symbol not in self.stats:
            self.stats[symbol] = {"wins": 0, "losses": 0, "outcomes": []}
        is_win = 1 if pnl_usd > 0 else 0
        if is_win:
            self.stats[symbol]["wins"] += 1
            self.global_wins += 1
        else:
            self.stats[symbol]["losses"] += 1
            self.global_losses += 1
        self.stats[symbol]["outcomes"].insert(0, is_win)
        self.recent_outcomes.insert(0, is_win)
        if len(self.stats[symbol]["outcomes"]) > 20:
            self.stats[symbol]["outcomes"].pop()
        if len(self.recent_outcomes) > 50:
            self.recent_outcomes.pop()


# ═══════════════════════════════════════════════════════════════
#  ROLLING STATE — Indicadores técnicos por ativo (EMA/RSI)
# ═══════════════════════════════════════════════════════════════
class RollingState:
    def __init__(self):
        self.count = 0
        self.price = 0.0
        self.last_price = 0.0
        self.ema5 = 0.0
        self.ema10 = 0.0
        self.ema200 = 0.0
        self.ag = 0.0
        self.al = 0.0
        self.rsi = 50.0
        self.returns = collections.deque(maxlen=20)

    def update(self, close_price: float):
        """Atualiza indicadores com o preço de fechamento de um candle."""
        self.last_price = self.price if self.count > 0 else close_price
        self.price = close_price
        self.count += 1

        if self.count > 1 and self.last_price > 0:
            self.returns.append((close_price - self.last_price) / self.last_price)

        if self.count == 1:
            self.ema5 = self.ema10 = self.ema200 = close_price
            return

        # EMA 5 e 10 (Turbo — reação rápida)
        self.ema5 = (close_price * (2 / 6)) + (self.ema5 * (1 - 2 / 6))
        self.ema10 = (close_price * (2 / 11)) + (self.ema10 * (1 - 2 / 11))

        # EMA 200 (Trend Mestra)
        self.ema200 = (close_price * (2 / 201)) + (self.ema200 * (1 - 2 / 201))

        # RSI 14 (Wilder)
        delta = close_price - self.last_price
        gain = max(0, delta)
        loss = max(0, -delta)

        if self.count <= 15:
            self.ag = (self.ag * (self.count - 2) + gain) / (self.count - 1)
            self.al = (self.al * (self.count - 2) + loss) / (self.count - 1)
        else:
            self.ag = (self.ag * 13 + gain) / 14
            self.al = (self.al * 13 + loss) / 14

        if self.al == 0:
            self.rsi = 100.0 if self.ag > 0 else 50.0
        else:
            self.rsi = 100.0 - (100.0 / (1.0 + (self.ag / self.al)))

    def get_volatility(self):
        if len(self.returns) < 2:
            return 1.0
        return float(np.std(self.returns) * 100)


class StateManager:
    """Gerencia estado dos indicadores para múltiplos ativos."""
    def __init__(self):
        self.data: Dict[str, RollingState] = {}
        self._lock = threading.Lock()

    def update(self, symbol: str, close_price: float):
        with self._lock:
            if symbol not in self.data:
                self.data[symbol] = RollingState()
            self.data[symbol].update(close_price)

    def get_state(self, symbol: str) -> Optional[RollingState]:
        return self.data.get(symbol)


# ═══════════════════════════════════════════════════════════════
#  IQ CONNECTOR — Wrapper resiliente para iqoptionapi
# ═══════════════════════════════════════════════════════════════
class IQConnector:
    """Gerencia conexão persistente com a IQ Option."""

    def __init__(self, email: str, password: str, account_type: str = 'PRACTICE'):
        from iqoptionapi.stable_api import IQ_Option
        self.api = IQ_Option(email, password)
        self.account_type = account_type.upper()
        self.connected = False

    def connect(self, emit_log=None) -> bool:
        """Conecta à IQ Option com até 3 tentativas, timeout de 30s por tentativa."""
        for attempt in range(1, 4):
            try:
                if emit_log:
                    emit_log(f"🔌 Tentativa de conexão {attempt}/3...", "info")

                # Wrapper com timeout para evitar travamento infinito da iqoptionapi
                result = [False, "timeout"]
                def _do_connect():
                    try:
                        c, r = self.api.connect()
                        result[0] = c
                        result[1] = r
                    except Exception as ex:
                        result[1] = str(ex)

                t = threading.Thread(target=_do_connect, daemon=True)
                t.start()
                t.join(timeout=30)  # 30s max por tentativa

                if t.is_alive():
                    if emit_log:
                        emit_log(f"⏰ Timeout na tentativa {attempt} (30s). Recriando conexão...", "warning")
                    # Recria o objeto API para limpar o estado interno travado
                    from iqoptionapi.stable_api import IQ_Option
                    self.api = IQ_Option(self.api.email, self.api.password)
                    time.sleep(3 * attempt)
                    continue

                check, reason = result[0], result[1]
                if check:
                    time.sleep(2)  # Handshake estabilizar
                    self.api.change_balance(self.account_type)
                    time.sleep(1)
                    self.connected = True
                    if emit_log:
                        emit_log(f"✅ Conectado à IQ Option ({self.account_type})", "success")
                    return True
                else:
                    if emit_log:
                        emit_log(f"❌ Falha na tentativa {attempt}: {reason}", "error")
            except Exception as e:
                if emit_log:
                    emit_log(f"🌐 Erro de rede na tentativa {attempt}: {e}", "error")
                logger.error(f"Connection attempt {attempt} failed: {e}")
            time.sleep(3 * attempt)  # Backoff: 3s, 6s, 9s

        self.connected = False
        return False

    def reconnect(self, emit_log=None) -> bool:
        """Reconexão automática com backoff exponencial."""
        if emit_log:
            emit_log("🔄 Reconectando à IQ Option...", "warning")
        self.connected = False
        return self.connect(emit_log)

    def get_balance(self) -> Optional[float]:
        """Retorna saldo atual. None se falhar."""
        try:
            bal = self.api.get_balance()
            return bal
        except:
            return None

    def get_open_assets(self, asset_type='binary') -> List[str]:
        """Retorna lista de ativos abertos para trading."""
        try:
            # get_all_open_time() pode crashar internamente no tipo 'digital'
            # então ignoramos erros e retornamos lista vazia
            all_assets = self.api.get_all_open_time()
            if all_assets and asset_type in all_assets:
                return [name for name, info in all_assets[asset_type].items() if info.get('open')]
            return []
        except (KeyError, TypeError, Exception) as e:
            logger.warning(f"get_open_assets fallback (não-crítico): {e}")
            return []

    def get_candles_hist(self, asset: str, tf: int, count: int) -> list:
        """Puxa candles históricos para warmup de indicadores."""
        try:
            return self.api.get_candles(asset, tf, count, time.time())
        except Exception as e:
            logger.error(f"get_candles_hist error [{asset}]: {e}")
            return []

    def start_stream(self, asset: str, timeframe: int = 60, buffer: int = 20):
        """Inicia stream de candles real-time."""
        try:
            self.api.start_candles_stream(asset, timeframe, buffer)
        except Exception as e:
            logger.error(f"start_stream error [{asset}]: {e}")

    def stop_stream(self, asset: str, timeframe: int = 60):
        """Para stream de candles para um ativo."""
        try:
            self.api.stop_candles_stream(asset, timeframe)
        except:
            pass

    def get_candles_rt(self, asset: str, timeframe: int = 60) -> dict:
        """Retorna candles em tempo real do buffer."""
        try:
            return self.api.get_realtime_candles(asset, timeframe)
        except Exception as e:
            logger.error(f"get_candles_rt error [{asset}]: {e}")
            return {}

    def buy(self, amount: float, asset: str, direction: str, duration: int) -> tuple:
        """Executa trade. Retorna (success, order_id)."""
        try:
            status, op_id = self.api.buy(amount, asset, direction, duration)
            return (status, op_id)
        except Exception as e:
            logger.error(f"buy error [{asset}]: {e}")
            return (False, None)

    def check_result(self, order_id) -> float:
        """Verifica resultado do trade (bloqueante). Retorna lucro/perda."""
        try:
            return self.api.check_win_v3(order_id)
        except Exception as e:
            logger.error(f"check_result error [{order_id}]: {e}")
            return 0.0

    def get_profit_dict(self) -> dict:
        """Retorna dicionário de lucros para todas as moedas abertas nas opções binárias/digitais."""
        try:
            return self.api.get_all_profit()
        except:
            return {}


# ═══════════════════════════════════════════════════════════════
#  OMNIQUANT BOT — Motor principal (IQ Option Digital Engine)
# ═══════════════════════════════════════════════════════════════
class OmniQuantBot:
    def __init__(self, connector: IQConnector, assets: List[str], duration: int,
                 max_gales: int, max_trades: int, stop_win_pct: float, stop_loss_pct: float, callbacks: Dict):
        self.iq = connector
        self.assets = assets
        self.duration = duration
        self.max_gales = max_gales
        self.max_trades = max_trades
        self.stop_win_pct = stop_win_pct
        self.stop_loss_pct = stop_loss_pct
        self.callbacks = callbacks

        self.state = StateManager()
        self.db = DatabaseManager()
        self.quant_memory = QuantMemory(self.db)

        self.trades_count = 0
        self.wins_count = 0
        self.losses_count = 0
        self.pending_count = 0

        # Martingale state por ativo
        self.gale_state: Dict[str, int] = {a: 0 for a in assets}
        self.last_bet: Dict[str, float] = {}

        # EMA crossover tracking
        self.prev_ema9: Dict[str, float] = {}
        self.prev_ema20: Dict[str, float] = {}

        # Lock para operações de trade
        self.trade_lock = threading.Lock()

        # Balance inicial e alvos
        self.initial_balance = self.iq.get_balance() or 0.0
        self.win_target = self.initial_balance * (1 + (self.stop_win_pct / 100))
        self.loss_target = self.initial_balance * (1 - (self.stop_loss_pct / 100))

        # Emite saldo inicial
        bal = self.iq.get_balance()
        if bal is not None:
            self.db.save_balance(bal)
            self.callbacks['emit_bal'](bal)

    def _check_limits(self, balance: float) -> bool:
        if not balance: return False

        if 'emit_progress' in self.callbacks:
            self.callbacks['emit_progress']({
                'current': balance,
                'start': self.initial_balance,
                'win_target': self.win_target,
                'loss_target': self.loss_target
            })

        # Lock diário trigger
        if self.win_target > self.initial_balance and balance >= self.win_target:
            self.callbacks['emit_log'](rf"🏆 STOP WIN BATIDO! Meta atingida com saldo ${balance:.2f}. Protegendo capital.", "success")
            self._trigger_kill_switch()
            return True
        elif self.loss_target < self.initial_balance and balance <= self.loss_target:
            self.callbacks['emit_log'](rf"🛑 STOP LOSS BATIDO! Sangramento contido com saldo ${balance:.2f}. Protegendo capital.", "error")
            self._trigger_kill_switch()
            return True
            
        return False

    def _trigger_kill_switch(self):
        # Calculate midnight timestamp local
        now = datetime.now()
        midnight = datetime(now.year, now.month, now.day, 23, 59, 59)
        if midnight.timestamp() < now.timestamp():
            midnight = datetime(now.year, now.month, now.day + 1, 23, 59, 59)
        self.db.set_lock(midnight.timestamp())
        self.stop_all_streams()
        if 'on_complete' in self.callbacks:
            self.callbacks['on_complete']()

    # ─── KELLY CRITERION (MODO AGRESSIVO — PRACTICE) ─────────
    def get_kelly_size(self, symbol: str, balance: float, initial_risk_pct: float = 0.5) -> float:
        """Calcula tamanho da aposta via Full Kelly, escalando com banca."""
        sym_stats = self.quant_memory.stats.get(symbol, {"wins": 0, "losses": 0})
        total = sym_stats['wins'] + sym_stats['losses']

        dynamic_base = balance * (initial_risk_pct / 100.0)
        safe_floor = max(2.0, dynamic_base)

        if total < 3:
            wins = self.quant_memory.global_wins
            losses = self.quant_memory.global_losses
            total = wins + losses
            if total < 3:
                # Sem dados suficientes: usa dynamic base
                return safe_floor
            p = wins / total
        else:
            p = sym_stats['wins'] / total

        q = 1 - p
        # Payout médio IQ ~80%
        b = 0.80
        kelly_full = p - (q / b)

        if kelly_full <= 0 or p < 0.25:
            # Edge negativo: aposta mínima de proteção baseada na porcentagem
            return safe_floor

        # Volatility penalty (suavizada para modo agressivo)
        state_obj = self.state.get_state(symbol)
        vol_penalty = 1.0
        if state_obj:
            volatility = state_obj.get_volatility()
            if volatility > 1.0:
                vol_penalty = 0.7

        # FULL KELLY limit
        final_kelly = max(0.01, min(0.15, kelly_full * vol_penalty)) # Internamente Kelly normaliza
        calculated = balance * final_kelly

        # RMSE smoothing (penaliza inconsistência)
        outcomes = self.quant_memory.get_recent_outcomes(symbol, limit=20)
        if len(outcomes) >= 5:
            mse = sum((p - outcome) ** 2 for outcome in outcomes) / len(outcomes)
            rmse = mse ** 0.5
            calculated = calculated * max(0.6, 1.0 - rmse)

        # Floor: 2.0 garantido | Cap: 1.5% max
        return max(2.0, min(calculated, balance * 0.015))

    # ─── WARMUP — Pré-carrega indicadores ────────────────────
    def warmup_indicators(self):
        """Puxa candles históricos para inicializar os indicadores."""
        self.callbacks['emit_log']("🔥 Aquecendo indicadores (Pré-carregando Candles)...", "info")

        for asset in self.assets:
            if not self.callbacks['check_running']():
                break
            try:
                candles = self.iq.get_candles_hist(asset, 300, 500)
                if candles:
                    for c in candles:
                        self.state.update(asset, c['close'])
                    self.callbacks['emit_log'](f"✅ {asset} aquecido ({len(candles)} candles).", "info")
                else:
                    self.callbacks['emit_log'](f"⚠️ {asset} sem dados históricos.", "warning")
            except Exception as e:
                self.callbacks['emit_log'](f"🌐 Falha no warmup de {asset}: {e}", "warning")
                logger.error(f"Warmup error [{asset}]: {e}")
            time.sleep(0.5)

        self.callbacks['emit_log']("✅ Fase de aquecimento finalizada.", "success")

    # ─── STREAM SETUP ────────────────────────────────────────
    def start_all_streams(self):
        """Inicia streams de candle real-time para todos os ativos."""
        for asset in self.assets:
            if not self.callbacks['check_running']():
                break
            self.iq.start_stream(asset, 300, 20)
            time.sleep(0.3)
        self.callbacks['emit_log'](f"📡 Streams ativos para {len(self.assets)} pares.", "success")
        if self.callbacks.get('emit_net'):
            self.callbacks['emit_net']('online')

    def stop_all_streams(self):
        """Para todos os streams."""
        for asset in self.assets:
            self.iq.stop_stream(asset, 300)

    # ─── RESULT CHECKER (roda em thread separada por trade) ──
    def _check_trade_result(self, order_id, asset, direction, amount):
        """Thread bloqueante que aguarda resultado de um trade."""
        try:
            profit = self.iq.check_result(order_id)

            if not self.callbacks['check_running']():
                return

            with self.trade_lock:
                self.pending_count = max(0, self.pending_count - 1)
                self.db.delete_pending(order_id)

                if profit > 0:
                    # WIN
                    self.wins_count += 1
                    self.gale_state[asset] = 0
                    result = 'win'
                    self.callbacks['emit_log'](
                        f"💰 WIN [{asset}] {direction.upper()} | +${profit:.2f}", "success"
                    )
                elif profit < 0:
                    # LOSS
                    self.losses_count += 1
                    result = 'loss'

                    if self.gale_state.get(asset, 0) < self.max_gales:
                        self.gale_state[asset] = self.gale_state.get(asset, 0) + 1
                        self.callbacks['emit_log'](
                            f"🛑 LOSS [{asset}] {direction.upper()} | ${profit:.2f} | Gale {self.gale_state[asset]}/{self.max_gales}",
                            "error"
                        )
                    else:
                        self.gale_state[asset] = 0
                        self.callbacks['emit_log'](
                            f"🛑 LOSS [{asset}] {direction.upper()} | ${profit:.2f} | Limite Gale atingido. Reset.",
                            "error"
                        )
                else:
                    # TIE (doji)
                    self.gale_state[asset] = 0
                    result = 'tie'
                    self.callbacks['emit_log'](
                        f"⚖️ EMPATE [{asset}] {direction.upper()} | Devolvido.", "info"
                    )

                self.trades_count += 1
                self.quant_memory.record_trade(asset, profit)

                # Salva no DB
                pnl_pct = (profit / amount * 100) if amount > 0 else 0
                self.db.save_trade(asset, direction, amount, profit, pnl_pct, result)

                # Atualiza saldo
                new_balance = self.iq.get_balance()
                if new_balance is not None:
                    self.db.save_balance(new_balance)
                    self.callbacks['emit_bal'](new_balance)
                    if self._check_limits(new_balance):
                        return # Kill Switch atuou

                # Emite trade para dashboard
                self.callbacks['emit_trade']({
                    "asset": asset,
                    "direction": direction,
                    "amount": round(amount, 2),
                    "pnl_usd": round(profit, 2),
                    "result": result,
                    "time": int(time.time())
                })

                # Check session limit
                if self.trades_count >= self.max_trades:
                    self.callbacks['emit_log'](
                        f"📊 Limite de {self.max_trades} trades atingido. Sessão encerrada.", "warning"
                    )
                    self.callbacks['on_complete']()

        except Exception as e:
            self.callbacks['emit_log'](f"⚠️ Erro ao verificar resultado [{asset}]: {e}", "error")
            logger.error(f"Result check error [{order_id}]: {e}", exc_info=True)
            with self.trade_lock:
                self.pending_count = max(0, self.pending_count - 1)

    # ─── OPEN TRADE ──────────────────────────────────────────
    def _open_trade(self, asset: str, direction: str, initial_risk_pct: float):
        """Executa um trade na IQ Option."""
        balance = self.iq.get_balance()
        if balance is None or balance < 1:
            self.callbacks['emit_log']("⚠️ Saldo indisponível ou insuficiente.", "warning")
            return

        # Kelly sizing
        kelly_amount = self.get_kelly_size(asset, balance, initial_risk_pct)

        # Martingale multiplier
        gale_mult = 2 ** self.gale_state.get(asset, 0)
        final_amount = kelly_amount * gale_mult

        # Safety caps (Limitado agressivamente a 1.5% exceto em Gale, protegendo Stop Diário)
        final_amount = max(2.0, min(final_amount, balance * 0.05)) # Hardcap total global
        final_amount = round(final_amount)  # IQ não aceita centavos em opções

        if final_amount > balance:
            self.callbacks['emit_log'](
                f"⚠️ Aposta ${final_amount} excede saldo ${balance:.2f}. Pulando.", "warning"
            )
            return

        # Executa trade
        status, op_id = self.iq.buy(final_amount, asset, direction, self.duration)

        if status:
            self.pending_count += 1
            self.last_bet[asset] = final_amount
            self.db.save_pending(op_id, asset, direction, final_amount, self.duration)

            gale_info = f" (Gale {self.gale_state[asset]})" if self.gale_state.get(asset, 0) > 0 else ""
            actual_pct = (final_amount / balance) * 100
            
            # Formatin log as requested: Entrada CALL de $50 (0.50%)
            self.callbacks['emit_log'](
                f"🎯 Entrada {direction.upper()} de ${final_amount} ({actual_pct:.2f}% da banca) no {asset}{gale_info} | {self.duration}min",
                "success"
            )
            self.callbacks['emit_trade']({
                "asset": asset,
                "direction": direction,
                "amount": final_amount,
                "pnl_usd": 0,
                "result": "pending",
                "time": int(time.time())
            })

            # Spawna thread para aguardar resultado
            t = threading.Thread(
                target=self._check_trade_result,
                args=(op_id, asset, direction, final_amount),
                daemon=True
            )
            t.start()
        else:
            self.callbacks['emit_log'](
                f"❌ ENTRADA RECUSADA: {asset} — Mercado fechado ou sem payout.", "error"
            )

    # ─── STRATEGY LOOP ───────────────────────────────────────
    def strategy_loop(self, initial_risk_pct: float, min_payout: float = 80.0):
        """Loop principal da estratégia EMA Crossover + RSI."""
        self.callbacks['emit_log']("🧠 TURBO ENGINE ativado. EMA5/EMA10 Crossover + Pullback + RSI14.", "info")

        scan_count = 0
        last_candle_ts: Dict[str, float] = {}

        while self.callbacks['check_running']():
            try:
                # Check panic
                if self.callbacks.get('check_panic') and self.callbacks['check_panic']():
                    self.callbacks['emit_log']("🚨 PANIC recebido. Parando novas entradas.", "error")
                    self.callbacks['on_complete']()
                    break

                # Check trade limit
                if self.trades_count >= self.max_trades:
                    break

                # Check balance
                balance = self.iq.get_balance()
                if balance is None:
                    self.callbacks['emit_log']("📡 Conexão perdida. Tentando reconectar...", "warning")
                    if self.callbacks.get('emit_net'):
                        self.callbacks['emit_net']('offline')
                    if not self.iq.reconnect(self.callbacks['emit_log']):
                        time.sleep(15)
                        continue
                    if self.callbacks.get('emit_net'):
                        self.callbacks['emit_net']('online')

                # 🎯 TARGET CHECK DIÁRIO
                if balance and self._check_limits(balance):
                    break

                # Puxa tabela de payout do broker
                profit_dict = self.iq.get_profit_dict()

                for asset in self.assets:
                    if not self.callbacks['check_running']():
                        break
                    if self.trades_count >= self.max_trades:
                        break

                    try:
                        # Lê candles real-time (M5)
                        rt_candles = self.iq.get_candles_rt(asset, 300)
                        if not rt_candles:
                            continue

                        # Pega o candle mais recente
                        sorted_ts = sorted(rt_candles.keys())
                        if not sorted_ts:
                            continue

                        latest_ts = sorted_ts[-1]

                        # Só processa se for um candle novo
                        if latest_ts == last_candle_ts.get(asset, 0):
                            continue
                        last_candle_ts[asset] = latest_ts

                        candle = rt_candles[latest_ts]
                        close_price = candle['close']

                        # Salva EMA anterior ANTES de atualizar
                        state_obj = self.state.get_state(asset)
                        if state_obj and state_obj.count >= 2:
                            self.prev_ema9[asset] = state_obj.ema5
                            self.prev_ema20[asset] = state_obj.ema10

                        # Atualiza indicadores
                        self.state.update(asset, close_price)
                        state_obj = self.state.get_state(asset)

                        if not state_obj or state_obj.count < 15:
                            continue  # Aguarda mínimo de dados (Turbo: 15)

                        ema9 = state_obj.ema5
                        ema20 = state_obj.ema10
                        ema200 = state_obj.ema200
                        rsi = state_obj.rsi
                        prev_e9 = self.prev_ema9.get(asset, ema9)
                        prev_e20 = self.prev_ema20.get(asset, ema20)

                        # ─ EMITE MÉTRICAS PARA DASHBOARD ─
                        spread = ((ema9 - ema20) / ema20) * 100 if ema20 > 0 else 0
                        signal = "CALL" if ema9 > ema20 else "PUT"
                        self.callbacks['emit_metric']({
                            "asset": asset,
                            "price": close_price,
                            "ema9": ema9,
                            "ema20": ema20,
                            "rsi": rsi,
                            "spread": spread,
                            "signal": signal
                        })

                        # ─ DETECÇÃO DE CROSSOVER (TURBO) ─
                        crossover_up = (prev_e9 <= prev_e20) and (ema9 > ema20)
                        crossover_down = (prev_e9 >= prev_e20) and (ema9 < ema20)

                        # ─ DETECÇÃO DE PULLBACK (TURBO) ─
                        pullback_call = (ema9 > ema20) and (close_price <= ema9 * 1.0002) and (close_price >= ema9 * 0.9998)
                        pullback_put  = (ema9 < ema20) and (close_price >= ema9 * 0.9998) and (close_price <= ema9 * 1.0002)

                        direction = None
                        
                        if (crossover_up or pullback_call) and 25 <= rsi <= 65:
                            if close_price > ema200:
                                direction = "call"
                            else:
                                self.callbacks['emit_log'](rf"🛑 CALL bloqueado em {asset}. Preço abaixo da EMA 200.", "warning")
                        elif (crossover_down or pullback_put) and 35 <= rsi <= 75:
                            if close_price < ema200:
                                direction = "put"
                            else:
                                self.callbacks['emit_log'](rf"🛑 PUT bloqueado em {asset}. Preço acima da EMA 200.", "warning")

                        if direction:
                            # Filtro Mínimo Payout
                            asset_profit = profit_dict.get(asset, {})
                            turbo_p = asset_profit.get('turbo', 0.0) * 100 if isinstance(asset_profit, dict) else 0.0
                            binary_p = asset_profit.get('binary', 0.0) * 100 if isinstance(asset_profit, dict) else 0.0
                            current_payout = max(turbo_p, binary_p)
                            
                            if 0 < current_payout < min_payout:
                                self.callbacks['emit_log'](
                                    f"⚠️ Sinal Abortado: {asset} pagando apenas {current_payout:.0f}% (Mínimo exigido: {min_payout}%).", 
                                    "warning"
                                )
                                direction = None

                        if direction:
                            with self.trade_lock:
                                # Limita trades simultâneos pendentes (agressivo: 8)
                                if self.pending_count < 8:
                                    self._open_trade(asset, direction, initial_risk_pct)

                    except Exception as e:
                        logger.error(f"Symbol scan error [{asset}]: {e}")
                        continue

                scan_count += 1
                if scan_count % 30 == 0:
                    bal = self.iq.get_balance()
                    if bal is not None:
                        self.callbacks['emit_bal'](bal)

                time.sleep(1)  # Turbo: polling acelerado

            except Exception as e:
                self.callbacks['emit_log'](f"⚠️ KERNEL FAULT: {e}", "error")
                logger.error(f"Strategy loop error: {e}", exc_info=True)
                time.sleep(10)

    # ─── BACKUP LOOP ─────────────────────────────────────────
    def backup_loop(self):
        """Backup periódico do SQLite."""
        while self.callbacks['check_running']():
            time.sleep(300)
            self.db.backup_database()
            self.callbacks['emit_log']("💾 Backup de redundância concluído.", "success")

    # ─── RUN (entry point) ───────────────────────────────────
    def run(self, initial_risk_pct: float = 0.5, min_payout: float = 80.0):
        """Ponto de entrada principal do bot."""
        try:
            # 1. Warmup dos indicadores
            self.warmup_indicators()

            # 2. Filtra ativos abertos
            open_assets = self.iq.get_open_assets('binary')
            if open_assets:
                filtered = [a for a in self.assets if a in open_assets]
                closed = [a for a in self.assets if a not in open_assets]
                if closed:
                    self.callbacks['emit_log'](
                        f"⚠️ Ativos fechados (removidos): {', '.join(closed)}", "warning"
                    )
                if filtered:
                    self.assets = filtered
                    self.callbacks['emit_log'](
                        f"✅ Ativos ativos: {', '.join(self.assets)}", "success"
                    )
                else:
                    self.callbacks['emit_log'](
                        "❌ Nenhum ativo configurado está aberto. Mantendo lista original.", "error"
                    )

            # 3. Inicia streams
            self.start_all_streams()

            # 4. Inicia backup em thread separada
            backup_t = threading.Thread(target=self.backup_loop, daemon=True)
            backup_t.start()

            # 5. Loop principal (bloqueante)
            self.strategy_loop(initial_risk_pct, min_payout)

        except Exception as e:
            self.callbacks['emit_log'](f"💀 ERRO FATAL: {e}", "error")
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.stop_all_streams()
            self.callbacks['emit_log']("🔌 Motor desligado. Streams encerrados.", "info")
            if self.callbacks.get('emit_net'):
                self.callbacks['emit_net']('offline')


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT — Chamado pelo app.py
# ═══════════════════════════════════════════════════════════════
def run_iq_strategy(**kwargs):
    """Função de entrada para o Flask iniciar o bot em background."""
    connector = IQConnector(
        kwargs['email'],
        kwargs['password'],
        kwargs.get('account_type', 'PRACTICE')
    )

    if not connector.connect(kwargs['emit_log']):
        kwargs['emit_log']("💀 Falha total na conexão. Encerrando.", "error")
        return

    bot = OmniQuantBot(
        connector=connector,
        assets=kwargs['ativos'],
        duration=kwargs.get('duration', 1),
        max_gales=kwargs.get('max_gales', 2),
        max_trades=kwargs.get('max_trades', 100),
        stop_win_pct=kwargs.get('stop_win_pct', 3.0),
        stop_loss_pct=kwargs.get('stop_loss_pct', 5.0),
        callbacks={
            'emit_log':      kwargs['emit_log'],
            'emit_bal':      kwargs['emit_bal'],
            'emit_metric':   kwargs.get('emit_metric', lambda d: None),
            'emit_trade':    kwargs.get('emit_trade', lambda d: None),
            'check_running': kwargs['check_running'],
            'check_panic':   kwargs.get('check_panic', lambda: False),
            'on_complete':   kwargs.get('on_complete', lambda: None),
            'emit_net':      kwargs.get('emit_net', lambda x: None),
            'emit_progress': kwargs.get('emit_progress', lambda d: None),
        }
    )

    bot.run(
        initial_risk_pct=kwargs.get('initial_risk_pct', 0.5),
        min_payout=kwargs.get('min_payout', 80.0)
    )
