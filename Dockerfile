# Use the official ESP-IDF image
FROM espressif/idf:v5.2.2
# Set ESP-IDF path
ENV IDF_PATH="/opt/esp/idf/"
WORKDIR "/"

COPY src/main.py /main.py

# ---------------------------------------------------------------------------
# 1) Gera o filesystem LittleFS contendo apenas o codigo do candidato
# ---------------------------------------------------------------------------
RUN git clone https://github.com/earlephilhower/mklittlefs.git && \
  cd mklittlefs && \
  git submodule update --init && \
  make dist && \
  ./mklittlefs --version

RUN cd mklittlefs && \
  mkdir -p ~/fs && \
  cp /*.py ~/fs/ && \
  ./mklittlefs -c ~/fs -b 4096 -p 256 -s 0x200000 /fs.bin

# ---------------------------------------------------------------------------
# 2) Baixa o firmware base do MicroPython para ESP32 (versao fixa, para
#    o build ser reprodutivel)
# ---------------------------------------------------------------------------
RUN curl -L -o /micropython.bin \
  https://micropython.org/resources/firmware/ESP32_GENERIC-20240602-v1.23.0.bin

# ---------------------------------------------------------------------------
# 3) Mescla o firmware do MicroPython com o filesystem (fs.bin) num unico
#    binario flashavel/simulavel. O firmware vai no offset 0x1000 (padrao
#    de boot do ESP32) e o filesystem no offset 0x200000 (onde a particao
#    "vfs" do build ESP32_GENERIC comeca).
# ---------------------------------------------------------------------------
RUN pip install esptool && \
  esptool --chip esp32 merge_bin -o /firmware_lfs.bin \
  --flash_mode dio --flash_size 4MB \
  0x1000 /micropython.bin \
  0x200000 /fs.bin

CMD ["/bin/bash"]