from machine import Pin, ADC
import time

# ==========================
# Configurações
# ==========================

LDR_PIN = 34
BUTTON_PIN = 4

LIGHT_THRESHOLD = 500      # Lux considerado iluminado
DARK_THRESHOLD = 100       # Lux considerado bloqueado

MICROSTOP_TIME = 5000      # ms
DEBOUNCE_TIME = 50         # ms

# ==========================
# Hardware
# ==========================

ldr = ADC(Pin(LDR_PIN))
ldr.atten(ADC.ATTN_11DB)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# ==========================
# Variáveis
# ==========================

piece_count = 0

beam_blocked = False

block_start = 0
microstop_reported = False

last_button_state = 1
last_button_change = time.ticks_ms()

print("Contador de Producao Inicializado")


# ==========================
# Funções
# ==========================

def read_lux():
    """
    Converte leitura ADC para uma escala aproximada de lux.
    """
    raw = ldr.read()

    # ADC ESP32 = 0..4095
    lux = int((raw / 4095) * 1000)

    return lux


def detect_piece(lux):
    global beam_blocked
    global piece_count
    global block_start
    global microstop_reported

    # Peça entrou
    if not beam_blocked and lux < DARK_THRESHOLD:
        beam_blocked = True
        block_start = time.ticks_ms()
        microstop_reported = False

    # Peça saiu
    elif beam_blocked and lux > LIGHT_THRESHOLD:
        beam_blocked = False

        piece_count += 1

        print(f"Peca detectada! Total: {piece_count}")


def detect_microstop():
    global microstop_reported

    if beam_blocked and not microstop_reported:

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            block_start
        )

        if elapsed >= MICROSTOP_TIME:
            microstop_reported = True
            print("Alerta: Micro-parada detectada!")


def reset_shift():
    global piece_count
    global beam_blocked
    global microstop_reported
    global block_start

    piece_count = 0
    beam_blocked = False
    microstop_reported = False
    block_start = 0

    print("Turno resetado com sucesso. Contadores zerados.")


def handle_button():
    global last_button_state
    global last_button_change

    current = button.value()

    if current != last_button_state:
        last_button_change = time.ticks_ms()
        last_button_state = current

    else:

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            last_button_change
        )

        if elapsed > DEBOUNCE_TIME:

            # Pull-up: pressionado = 0
            if current == 0:

                reset_shift()

                while button.value() == 0:
                    time.sleep_ms(10)


# ==========================
# Loop Principal
# ==========================

while True:

    lux = read_lux()

    detect_piece(lux)

    detect_microstop()

    handle_button()

    time.sleep_ms(20)