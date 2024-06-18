import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import time
from datetime import datetime

# Configuração do GPIO
RELE_PIN = 16
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELE_PIN, GPIO.OUT)

# Inicializa o relé como desligado
GPIO.output(RELE_PIN, GPIO.HIGH)

# Configuração do leitor RC522
reader = SimpleMFRC522()

db_path = 'dataBase/laboratorio.db'

def registrar_acesso(matricula, nome):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registro_acesso (matricula, nome, timestamp) VALUES (?, ?, ?)", (matricula, nome, timestamp))
    conn.commit()
    cursor.close()
    conn.close()

def verificar_solicitacao():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM solicitacoes_cartao WHERE status='pendente' LIMIT 1")
    solicitacao = cursor.fetchone()
    cursor.close()
    conn.close()
    return solicitacao

def atualizar_solicitacao(solicitacao_id, card_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE solicitacoes_cartao SET status='concluido', card_id=? WHERE id=?", (card_id, solicitacao_id))
    conn.commit()
    cursor.close()
    conn.close()

def verificar_usuario(card_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, matricula FROM usuarios WHERE card_id=?", (card_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario

try:
    while True:
        solicitacao = verificar_solicitacao()

        if solicitacao:
            print("Aproxime seu cartão para cadastro...")
            card_id, text = reader.read()
            
            print(f"ID do cartão lido: {card_id}")

            # Atualiza a solicitação com o ID do cartão lido
            atualizar_solicitacao(solicitacao[0], card_id)
            print("Cartão lido e registrado com sucesso.")
        
        else:
            print("Aproxime seu cartão...")
            card_id, text = reader.read()
            
            print(f"ID do cartão lido: {card_id}")

            usuario = verificar_usuario(card_id)

            if usuario:
                print("Cartão autorizado! Acionando o relé...")
                GPIO.output(RELE_PIN, GPIO.LOW)  # Ativa o relé (ativo baixo)
                time.sleep(1)
                GPIO.output(RELE_PIN, GPIO.HIGH)  # Desativa o relé
                registrar_acesso(usuario[1], usuario[0])
                print("Relé desativado e acesso registrado.")
            else:
                print("Cartão não autorizado.")
        
        time.sleep(2)  # Pausa para evitar leituras consecutivas muito rápidas

except KeyboardInterrupt:
    print("Script interrompido pelo usuário.")

finally:
    GPIO.cleanup()
    print("GPIO liberado e script encerrado.")
