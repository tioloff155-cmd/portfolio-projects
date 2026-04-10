import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("Conectado ao servidor do bot!")
    data = {
        'ativos': 'EURUSD-OTC, GBPUSD-OTC, USDJPY-OTC',
        'bet': 1,
        'duration': 1,
        'gales': 2,
        'max_trades': 50
    }
    sio.emit('start_bot', data)
    print(f"Evento 'start_bot' emitido com parâmetros: {data}")

@sio.on('new_log')
def on_new_log(data):
    print(f"BOT LOG: {data['message']}")

if __name__ == '__main__':
    try:
        time.sleep(2)
        sio.connect('http://127.0.0.1:8080')
        time.sleep(5)
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        if sio.connected:
            sio.disconnect()
