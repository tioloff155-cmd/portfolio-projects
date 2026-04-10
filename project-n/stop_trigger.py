import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("Conectado ao servidor do bot!")
    sio.emit('stop_bot')
    print("Evento 'stop_bot' emitido.")
    time.sleep(1)
    sio.disconnect()

if __name__ == '__main__':
    try:
        sio.connect('http://127.0.0.1:8080')
        time.sleep(2)
    except Exception as e:
        print(f"Erro ao conectar: {e}")
