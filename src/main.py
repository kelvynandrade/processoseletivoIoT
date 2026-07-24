import machine
import time

# ==========================================
# CONFIGURAÇÃO DE HARDWARE
# ==========================================
pino_ldr = machine.ADC(machine.Pin(34))
pino_ldr.atten(machine.ADC.ATTN_11DB)

pino_btn = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)

# ==========================================
# CONSTANTES (Compatíveis com os cenários do Wokwi)
# ==========================================
LIMIAR_LIVRE = 600        # Acima de 600 lux = Esteira livre (Valor de teste: 800)
LIMIAR_BLOQUEIO = 100     # Abaixo de 100 lux = Peça bloqueando (Valor de teste: 50)
TEMPO_MICRO_PARADA = 5000 # 5 segundos para disparar micro-parada
ATRASO_DEBOUNCE = 50      # Tempo de debounce em milissegundos

# ==========================================
# VARIÁVEIS DE ESTADO DO SISTEMA
# ==========================================
pecas_total = 0
estado_bloqueado = False
tempo_inicio_bloqueio = 0
alerta_emitido = False

estado_btn_anterior = 1
tempo_ultimo_debounce = 0

def inicializar_sistema():
    """Função de setup executada ao ligar o dispositivo."""
    print("Contador de Producao Inicializado")

def resetar_turno():
    """Zera contadores e reinicia estados."""
    global pecas_total, estado_bloqueado, alerta_emitido
    pecas_total = 0
    estado_bloqueado = False
    alerta_emitido = False
    print("Turno resetado com sucesso. Contadores zerados.")

def executar_loop():
    """Loop principal rodando como Máquina de Estados não-bloqueante."""
    global pecas_total, estado_bloqueado, tempo_inicio_bloqueio, alerta_emitido
    global estado_btn_anterior, tempo_ultimo_debounce

    while True:
        agora = time.ticks_ms()
        leitura_ldr = pino_ldr.read()
        leitura_btn = pino_btn.value()

        # --------------------------------------------------
        # 1. Lógica do Sensor Óptico (LDR) e Contagem (Cenário 1)
        # --------------------------------------------------
        if leitura_ldr < LIMIAR_BLOQUEIO and not estado_bloqueado:
            estado_bloqueado = True
            tempo_inicio_bloqueio = agora
            alerta_emitido = False

        elif leitura_ldr > LIMIAR_LIVRE and estado_bloqueado:
            estado_bloqueado = False
            pecas_total += 1
            print(f"Peca detectada! Total: {pecas_total}")

        # --------------------------------------------------
        # 2. Lógica de Detecção de Micro-paradas (Cenário 2)
        # --------------------------------------------------
        if estado_bloqueado and not alerta_emitido:
            if time.ticks_diff(agora, tempo_inicio_bloqueio) >= TEMPO_MICRO_PARADA:
                print("Alerta: Micro-parada detectada!")
                alerta_emitido = True

        # --------------------------------------------------
        # 3. Lógica do Botão de Reset (Cenário 3)
        # --------------------------------------------------
        if leitura_btn != estado_btn_anterior:
            tempo_ultimo_debounce = agora

        if time.ticks_diff(agora, tempo_ultimo_debounce) > ATRASO_DEBOUNCE:
            if leitura_btn == 0 and estado_btn_anterior == 1:
                resetar_turno()
                estado_btn_anterior = 0
        
        if leitura_btn == 1:
             estado_btn_anterior = 1

        time.sleep_ms(10)

if __name__ == "__main__":
    inicializar_sistema()
    executar_loop()