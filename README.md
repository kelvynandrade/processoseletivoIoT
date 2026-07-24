# Relatório Técnico - Contador de Produção Não-Intrusivo

### Identificação do Candidato
- **Nome completo:** Kelvyn César Ferreira de Andrade
- **GitHub:** https://github.com/kelvynandrade

---

## Visão Geral da Solução

Este projeto implementa um sistema de monitoramento de linha de produção utilizando um sensor óptico simulado. O objetivo do firmware é detectar e contabilizar a passagem de peças através da interrupção de um feixe de luz (borda de descida e subida), calcular eventuais micro-paradas (gargalos operacionais) e permitir o reset manual do turno pelo operador, tudo isso operando em tempo real e sem a necessidade de um CLP industrial. 

--- 

## Arquitetura do Sistema Embarcado

O sistema foi estruturado em Python (MicroPython) utilizando o conceito de uma Máquina de Estados Finita (FSM) dentro de um loop infinito principal (`main.py`). A arquitetura lógica flui da seguinte maneira:

1. **Leitura de Entradas (Polling):** A cada iteração do loop, o sistema realiza a leitura do conversor Analógico-Digital (ADC) para o LDR e do pino digital para o botão.
2. **Avaliação de Estado (Sensor):** O sistema verifica se a luminosidade cruzou os limites pré-estabelecidos (`LIMIAR_BLOQUEIO` ou `LIMIAR_LIVRE`), alterando o status da variável `estado_bloqueado`.
3. **Temporização Assíncrona:** Em paralelo, caso o sistema esteja em estado de bloqueio, um comparador de tempo avalia se o limite de micro-parada foi atingido.
4. **Acionamento:** As saídas no terminal serial (logs) são acionadas estritamente nas transições de estado, garantindo que não haja "spam" de mensagens.

---

## Componentes Utilizados na Simulação

A simulação de hardware definida no arquivo `diagram.json` conta com:

- **Placa Microcontroladora (ESP32 DevKit C v4):** Cérebro do projeto, responsável por processar o firmware e gerenciar as portas de I/O.
- **Sensor Óptico (LDR - ldr1):** Conectado ao pino 34 (ADC). Atua como o detector de passagem na esteira. A atenuação foi configurada (`ATTN_11DB`) para ler a faixa completa de tensão (0-3.3V).
- **Botão Pushbutton (btn1):** Conectado ao pino 12. Configurado como entrada com resistor de Pull-Up interno para realizar o reset do turno.

---

## Decisões Técnicas Relevantes

Para garantir estabilidade, legibilidade e o cumprimento das restrições de testes automatizados (CI), as seguintes decisões foram tomadas:

- **Arquitetura Não-Bloqueante:** O uso de funções como `time.sleep()` foi descartado. Toda a temporização (micro-paradas e *debounce*) foi construída utilizando `time.ticks_ms()` e `time.ticks_diff()`. Isso garante que o microcontrolador não perca ciclos de processamento e mantenha a capacidade de ler o botão de reset instantaneamente, mesmo durante o monitoramento de uma micro-parada prolongada.
- **Debounce de Software:** Implementou-se uma lógica de *debounce* assíncrona de 50ms na leitura do botão para evitar leituras ruidosas e múltiplos acionamentos acidentais da função de reset.
- **Clean Code e Manutenibilidade:** Todos os limites analógicos (*thresholds*) e tempos de atraso foram extraídos da lógica principal e definidos como constantes globais no início do arquivo, facilitando futuras calibrações sem o risco de alterar a estrutura do algoritmo.

---

## Resultados Obtidos

O sistema atendeu a todos os requisitos propostos com sucesso:
- As transições de luminosidade registram as peças apenas após a passagem completa (borda de subida), evitando falsas contagens.
- O temporizador assíncrono detecta corretamente interrupções longas e dispara o alerta de micro-parada.
- O botão de reset zera as variáveis globais com segurança.
- Todas as mensagens via serial foram formatadas com a sintaxe exata exigida, garantindo compatibilidade total com os critérios de validação do Wokwi CI.

---

## Comentários Adicionais

A experiência prévia com desenvolvimento de lógicas estruturadas e a prototipagem de circuitos eletrônicos virtuais colaborou significativamente para a estruturação rápida deste ambiente. A transição de conceitos habitualmente aplicados em linguagens como C ou Java para a elaboração de máquinas de estado eficientes em Python ocorreu de forma fluida, comprovando a robustez do MicroPython para aplicações ágeis em IoT e controle de automação.