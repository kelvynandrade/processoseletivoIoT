import machine
import time

# ==========================================
# CONFIGURAÇÃO DE HARDWARE
# ==========================================
# LDR no pino 34 (ADC - Conversor Analógico Digital)
pino_ldr = machine.ADC(machine.Pin(34))
pino_ldr.atten(machine.ADC.ATTN_11DB) # Permite leitura de tensão de 0 a 3.3V (Valores de 0 a 4095)

# Botão no pino 12 configurado com Resistor Pull-Up interno
pino_btn = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)

# ==========================================
# CONSTANTES "CLEAN CODE" (Sem Números Mágicos)
# ==========================================
# Valores aproximados de ADC simulados no Wokwi para os limites de Lux exigidos
LIMIAR_LIVRE = 2000      # Representa linha livre (Ex: > 500 lux)
LIMIAR_BLOQUEIO = 1000   # Representa peça obstruindo (Ex: < 100 lux)
TEMPO_MICRO_PARADA = 5000 # Tempo limite em milissegundos (5 segundos)
ATRASO_DEBOUNCE = 50      # Tempo em milissegundos para evitar bouncing do botão

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
    # STRING EXATA EXIGIDA PELO CI
    print("Contador de Producao Inicializado")

def resetar_turno():
    """Zera contadores e reinicia estados."""
    global pecas_total, estado_bloqueado, alerta_emitido
    pecas_total = 0
    estado_bloqueado = False
    alerta_emitido = False
    # STRING EXATA EXIGIDA PELO CI
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
        # 1. Lógica do Sensor Óptico (LDR) e Contagem
        # --------------------------------------------------
        # Detecta transição de descida (Luz foi interrompida = Peça entrou)
        if leitura_ldr < LIMIAR_BLOQUEIO and not estado_bloqueado:
            estado_bloqueado = True
            tempo_inicio_bloqueio = agora
            alerta_emitido = False

        # Detecta transição de subida (Luz retornou = Peça passou completamente)
        elif leitura_ldr > LIMIAR_LIVRE and estado_bloqueado:
            estado_bloqueado = False
            pecas_total += 1
            # STRING EXATA EXIGIDA PELO CI
            print(f"Peca detectada! Total: {pecas_total}")

        # --------------------------------------------------
        # 2. Lógica de Detecção de Micro-paradas
        # --------------------------------------------------
        if estado_bloqueado and not alerta_emitido:
            # Compara o tempo atual com o momento em que bloqueou
            if time.ticks_diff(agora, tempo_inicio_bloqueio) >= TEMPO_MICRO_PARADA:
                # STRING EXATA EXIGIDA PELO CI
                print("Alerta: Micro-parada detectada!")
                alerta_emitido = True

        # --------------------------------------------------
        # 3. Lógica do Botão de Reset (Com Debounce Assíncrono)
        # --------------------------------------------------
        if leitura_btn != estado_btn_anterior:
            tempo_ultimo_debounce = agora

        # Se o sinal se manteve estável além do tempo de debounce
        if time.ticks_diff(agora, tempo_ultimo_debounce) > ATRASO_DEBOUNCE:
            if leitura_btn == 0 and estado_btn_anterior == 1:
                # Gatilho executado apenas no instante do aperto (borda de descida do pull-up)
                resetar_turno()
                estado_btn_anterior = 0 # Atualiza para evitar múltiplas chamadas
        
        # Prepara para a próxima leitura quando o botão for solto
        if leitura_btn == 1:
             estado_btn_anterior = 1

        # Pequena pausa inofensiva de 10ms apenas para evitar Watchdog Timer Reset no ESP32
        time.sleep_ms(10)

if __name__ == "__main__":
    inicializar_sistema()
    executar_loop()