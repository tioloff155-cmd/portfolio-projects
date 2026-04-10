import os
import threading
import time
from dotenv import load_dotenv
from flask import Flask, render_template, make_response
from flask_socketio import SocketIO
from strategy import run_iq_strategy, DatabaseManager

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Estado global
_bot_running = False
_panic_mode  = False
_bot_thread  = None


@app.route('/')
def index():
    resp = make_response(render_template('index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma']  = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


# ─── Emitters ───────────────────────────────────
def log(msg, t="info"):    socketio.emit('new_log',       {'message': msg, 'type': t})
def bal(b):                socketio.emit('update_balance', {'balance': b})
def metric(d):             socketio.emit('update_metric',  d)
def trade(d):              socketio.emit('trade_executed', d)
def net(s):                socketio.emit('update_net',     {'status': s})
def progress(d):           socketio.emit('update_progress', d)


# ─── Socket events ──────────────────────────────
@socketio.on('connect')
def on_connect():
    try:
        current_balance = DatabaseManager().load_balance()
        if current_balance and current_balance > 0:
            bal(current_balance)
        status = 'running' if _bot_running else 'stopped'
        socketio.emit('bot_status', {'status': status})
    except Exception as e:
        print(f"Erro ao carregar saldo inicial: {e}")

@socketio.on('start_bot')
def on_start(data):
    global _bot_running, _panic_mode, _bot_thread

    # Verifica limite diário
    locked_until = DatabaseManager().get_lock()
    if locked_until > time.time():
        dt = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(locked_until))
        log(f"SISTEMA BLOQUEADO: Limite diário atingido. O robô só poderá religar a partir de {dt}.", "error")
        socketio.emit('bot_status', {'status': 'stopped'})
        return

    if _bot_running:
        log("⚠️ Motor já está em execução.", "warning")
        return

    if _bot_thread is not None and _bot_thread.is_alive():
        log("⏳ Aguarde o motor anterior ser totalmente finalizado...", "error")
        return

    # Parâmetros do frontend
    ativos_raw    = data.get('ativos', 'EURUSD-OTC, GBPUSD-OTC, USDJPY-OTC')
    ativos        = [a.strip().upper() for a in ativos_raw.split(',') if a.strip()]
    initial_risk_pct = float(data.get('risk_pct', 0.5))
    duration      = int(data.get('duration', 1))
    max_gales     = int(data.get('gales', 2))
    max_trades    = int(data.get('max_trades', 100))
    stop_win_pct  = float(data.get('stop_win', 3.0))
    stop_loss_pct = float(data.get('stop_loss', 5.0))
    min_payout    = float(data.get('min_payout', 80.0))

    # Credenciais IQ Option
    load_dotenv(override=True)
    email        = os.getenv("IQ_EMAIL", "")
    password     = os.getenv("IQ_PASSWORD", "")
    account_type = os.getenv("IQ_ACCOUNT_TYPE", "PRACTICE")

    if not email or not password:
        log("❌ Credenciais IQ Option não configuradas no .env", "error")
        return

    _bot_running = True
    _panic_mode  = False

    log(f"🚀 Sessão IQ Digital iniciada — {len(ativos)} pares | SW: {stop_win_pct}% | SL: {stop_loss_pct}%", "success")
    socketio.emit('bot_status', {'status': 'running'})

    def on_complete():
        global _bot_running
        _bot_running = False
        socketio.emit('session_complete', {'max_trades': max_trades})
        socketio.emit('bot_status', {'status': 'stopped'})

    _bot_thread = socketio.start_background_task(
        run_iq_strategy,
        email=email,
        password=password,
        account_type=account_type,
        ativos=ativos,
        initial_risk_pct=initial_risk_pct,
        duration=duration,
        max_gales=max_gales,
        max_trades=max_trades,
        stop_win_pct=stop_win_pct,
        stop_loss_pct=stop_loss_pct,
        min_payout=min_payout,
        emit_log=log,
        emit_bal=bal,
        emit_metric=metric,
        emit_trade=trade,
        emit_net=net,
        emit_progress=progress,
        check_running=lambda: _bot_running,
        check_panic=lambda: _panic_mode,
        on_complete=on_complete,
    )

@socketio.on('stop_bot')
def on_stop():
    global _bot_running
    if _bot_running:
        _bot_running = False
        log("⏸️ Sinal de parada enviado. Encerrando após trades pendentes...", "warning")
        socketio.emit('bot_status', {'status': 'stopped'})
    else:
        log("O bot já está parado.", "info")

@socketio.on('panic_button')
def on_panic():
    global _panic_mode
    if _bot_running:
        _panic_mode = True
        log("🚨 PANIC acionado — Impedindo novas entradas. Trades pendentes serão finalizados.", "error")


@socketio.on('get_history')
def handle_get_history():
    try:
        trades = DatabaseManager().load_trades(limit=100)
        socketio.emit('history_data', trades)
    except Exception as e:
        log(f"Erro ao buscar histórico: {str(e)}", "error")


if __name__ == '__main__':
    print("""
    =========================================
      [+] OmniQuant // IQ Digital Engine
      [+] Servidor Local: http://127.0.0.1:8080
    =========================================
    """)
    socketio.run(app, debug=False, host='127.0.0.1', port=8080, allow_unsafe_werkzeug=True)
