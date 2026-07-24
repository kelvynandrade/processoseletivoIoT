from machine import Pin, ADC
import utime

# ---------------------------------------------------------------------------
# Configuracao de hardware
# ---------------------------------------------------------------------------
LDR_PIN = 34   # GPIO34 (ADC1_CH6) - conectado ao pino AO do sensor ldr1
BTN_PIN = 4    # GPIO4 - conectado ao botao btn1

ldr = ADC(Pin(LDR_PIN))
ldr.atten(ADC.ATTN_11DB)   # Permite ler a faixa completa 0 - 3.3V (0 - 4095)

btn = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)  # nivel baixo = botao pressionado

# ---------------------------------------------------------------------------
# Parametros do sistema
# ---------------------------------------------------------------------------
# Limiares em "contagem bruta do ADC" (0-4095), calculados a partir dos
# parametros padrao do componente wokwi-photoresistor-sensor (rl10=50k ohm,
# gamma=0.7, resistor fixo de 10k em serie com o LDR, AO entre os dois):
#   R(lux)   = rl10 * (lux/10) ^ (-gamma)
#   Vout     = VCC * Rfixo / (R(lux) + Rfixo)
# Com VCC=3.3V isso da aproximadamente:
#   lux=800 (linha livre)   -> ADC ~ 3300
#   lux=50  (peca passando) -> ADC ~ 1560
# Os limiares abaixo ficam entre esses dois valores, com folga (histerese)
# para evitar oscilacao por ruido perto da transicao.
LUX_ALTO = 2500   # acima disso = linha livre (> 500 lux no enunciado)
LUX_BAIXO = 2000  # abaixo disso = peca bloqueando o sensor (< 100 lux no enunciado)

DEBOUNCE_MS = 50
MICRO_PARADA_MS = 5000

# ---------------------------------------------------------------------------
# Estado do sistema
# ---------------------------------------------------------------------------
contador_pecas = 0
linha_bloqueada = False
inicio_bloqueio = 0
alerta_emitido = False

btn_estado_anterior = 1
btn_ultima_mudanca = utime.ticks_ms()
btn_estavel = 1


def ler_botao():
    """Debounce nao-bloqueante. Retorna o novo estado estavel (0 ou 1)
    somente no instante em que ele muda, ou None caso contrario."""
    global btn_estado_anterior, btn_ultima_mudanca, btn_estavel

    leitura = btn.value()
    agora = utime.ticks_ms()

    if leitura != btn_estado_anterior:
        btn_ultima_mudanca = agora
        btn_estado_anterior = leitura

    if utime.ticks_diff(agora, btn_ultima_mudanca) > DEBOUNCE_MS:
        if leitura != btn_estavel:
            btn_estavel = leitura
            return btn_estavel

    return None


def resetar_turno():
    global contador_pecas, linha_bloqueada, alerta_emitido
    contador_pecas = 0
    linha_bloqueada = False
    alerta_emitido = False
    print("Turno resetado com sucesso. Contadores zerados.")


def main():
    global contador_pecas, linha_bloqueada, inicio_bloqueio, alerta_emitido

    print("Contador de Producao Inicializado")

    while True:
        valor_ldr = ldr.read()
        agora = utime.ticks_ms()

        # --- Deteccao de peca: incrementa somente na borda de subida ---
        # (linha livre -> bloqueada -> livre = uma peca completa passou)
        if not linha_bloqueada and valor_ldr < LUX_BAIXO:
            linha_bloqueada = True
            inicio_bloqueio = agora
            alerta_emitido = False

        elif linha_bloqueada and valor_ldr > LUX_ALTO:
            linha_bloqueada = False
            contador_pecas += 1
            print("Peca detectada! Total: {}".format(contador_pecas))

        # --- Deteccao de micro-parada (temporizador nao-bloqueante) ---
        if linha_bloqueada and not alerta_emitido:
            if utime.ticks_diff(agora, inicio_bloqueio) > MICRO_PARADA_MS:
                print("Alerta: Micro-parada detectada!")
                alerta_emitido = True

        # --- Botao de reset (com debounce) ---
        # Dispara na borda de subida (quando SOLTA o botao), seguindo o
        # mesmo padrao usado na contagem de pecas: a acao so e considerada
        # completa quando o evento termina, nao quando comeca.
        novo_estado = ler_botao()
        if novo_estado == 1:
            resetar_turno()

        utime.sleep_ms(20)


main()