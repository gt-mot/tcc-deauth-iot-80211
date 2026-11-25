# Vulnerabilidades do IEEE 802.11 em ambientes IoT

**Estudo de caso utilizando microcontroladores de baixo custo**

Trabalho de Conclusão de Curso — Bacharelado em Ciência da Computação,
Centro Universitário Dinâmica das Cataratas (UDC), Foz do Iguaçu, 2026.
Autor: Gustavo Mota do Nascimento · Orientador: Prof. Me. Luciano Santos Cardoso

📄 **Texto completo:** [`main.pdf`](main.pdf)

Ensaios de desautenticação IEEE 802.11 feitos em laboratório, numa rede própria, com um microcontrolador de
baixo custo (LILYGO T-Embed CC1101 Plus, ESP32-S3, firmware Bruce 1.16.1). Os alvos foram uma câmera IP, uma
lâmpada, uma tomada e um smartphone, em dois cenários: WPA2 (sem PMF) e modo misto WPA2/WPA3. A captura foi feita
com um adaptador Atheros AR9271 em modo monitor (Kali Linux, tcpdump/tshark), junto com `ping -D` para cada
dispositivo.

## Conteúdo

| Pasta / arquivo | O que é | Onde aparece no TCC |
|---|---|---|
| `main.pdf` | Texto do TCC | — |
| `main.tex`, `Capitulos/`, `Extras/`, `Apresentacao/`, `Configuracoes/`, `Imagens/` | Código-fonte LaTeX (abnTeX2, classe `abnt-UDC-CC.cls`) | — |
| `Capturas/camera/` | Validação da captura, controle e ensaio piloto da câmera (3 nov. 2026) | Seção 5.4.2 |
| `Capturas/wpa2/` | Ensaios no cenário WPA2 (8 e 17 nov. 2026) | Cap. 5; Apêndice B |
| `Capturas/wpa3/` | Ensaios no modo misto WPA2/WPA3 (8 nov. 2026) | Cap. 5; Apêndices A e B |
| `Capturas/*/*_ping.txt` | Log de `ping -D` de cada execução (sem alteração) | Tabelas 4, 5 e 9 |
| `Capturas/*/*.pcapng` | Capturas **filtradas** (ver abaixo) | Tabelas 3, 7, 8 e 9 |
| `Capturas/mapa_quadros/` | Número de cada quadro filtrado → número na captura original | Apêndice A |
| `src/analisa_ping.py` | Calcula as métricas de conectividade de todos os logs | Tabelas 4, 5 e 9 |
| `src/figura_comparacao_pmf.py` | Gera a Figura 28 | Figura 28 |
| `src/figura_ping_lampada.py` | Gera a Figura 29 | Figura 29 |
| `coleta/tcc_cap.sh` | Script usado na estação Kali para gravar cada ensaio (tcpdump + `ping -D -i 0.5`) | Cap. 4; Apêndice C |
| `coleta/captura_tcc.sh` | Primeira versão do script de coleta | — |
| `SHA256SUMS.txt` | Hash de cada arquivo de `Capturas/` | — |

Cada execução tem um identificador `DISPOSITIVO_CENARIO_Rnn` (ex.: `LAMP_WPA2_R01`), usado nos nomes dos arquivos
e nas Tabelas 8 e 9 (Apêndice B). `CAM_WPA2_R05` e `CAM_WPA2_R06` (sem linha de base) e `PHONE_WPA3_R02` (sem
desautenticação direcionada) foram invalidadas. `CAM_WPA2_R07` é teste de bancada e `CAM_WPA2_R08` é descritiva
(Seção 4.10 e Apêndice B).

## Sobre as capturas filtradas

As capturas originais também registram quadros de redes vizinhas, captados em modo monitor, e o *handshake*
EAPOL da rede de laboratório. Para publicar os dados sem expor terceiros, cada `.pcapng` deste repositório
mantém só os quadros da rede de laboratório:

```
(wlan.bssid == b4:c0:c3:29:48:ca || wlan.addr == b4:c0:c3:29:48:ca) && !eapol
```

A filtragem preserva todos os quadros usados no TCC: desautenticação, associação (elemento RSN), quadros
*Action* protegidos e dados. As contagens de desautenticação por dispositivo e a saída de `src/analisa_ping.py`
são idênticas às obtidas com as capturas originais. Os números de quadro citados no Apêndice A referem-se às
capturas originais. Para achar o quadro equivalente na versão filtrada, use `Capturas/mapa_quadros/<execução>.csv`.
As capturas originais foram entregues ao orientador em mídia digital.

## Como reproduzir

Requisitos: Python 3.10+, `matplotlib` e Wireshark (`tshark` e `capinfos` no PATH).

```bash
pip install matplotlib
python src/analisa_ping.py           # tempo acumulado sem resposta, maior queda e fração, por execução
python src/analisa_ping.py --csv     # o mesmo em CSV
python src/figura_comparacao_pmf.py saida_fig28.png
python src/figura_ping_lampada.py   saida_fig29.png
```

Regras (Seção 5.3.2, "Dicionário de métricas"): resposta válida = linha do ping sem `DUP!`, com tempo diferente de
0,000 ms e não seguida de `wrong data byte`; intervalo sem resposta = mais de 2 s entre respostas válidas; se a
queda vai até o fim da captura, o valor é limite inferior (≥).

### Conferir nas capturas com o tshark

Quadros de desautenticação por origem e destino:

```bash
tshark -r Capturas/wpa2/TOMADA_WPA2_R02.pcapng -Y "wlan.fc.type_subtype==12" -T fields -e wlan.sa -e wlan.da | sort | uniq -c
```

Desautenticação envolvendo um dispositivo (coluna "Deauth no disp."):

```bash
tshark -r <arquivo>.pcapng -Y "wlan.fc.type_subtype==12 && wlan.addr==<MAC do dispositivo>" | wc -l
```

Segurança negociada no *Association Request* (AKM 2 = PSK, 8 = SAE; MFPC/MFPR = PMF), base das Tabelas 3 e 7:

```bash
tshark -r Capturas/wpa3/LAMP_WPA3_R01.pcapng -Y "wlan.fc.type_subtype==0" \
  -T fields -e frame.number -e wlan.sa -e wlan.rsn.akms.type \
  -e wlan.rsn.capabilities.mfpc -e wlan.rsn.capabilities.mfpr
```

Integridade dos arquivos publicados:

```bash
sha256sum -c SHA256SUMS.txt
```

## Compilar o texto

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Ética e uso de IA

Todos os ensaios foram feitos apenas na rede e nos dispositivos do autor, em ambiente controlado (Seção 4.2,
RNF01). O conteúdo deste repositório serve à reprodução científica dos resultados. Não use essas técnicas em
redes ou dispositivos de terceiros sem autorização.

O uso de ferramentas de inteligência artificial está declarado na Seção 3.1.2 do TCC. Nenhum dado experimental
foi gerado por ferramenta: todos os valores vêm das capturas e dos logs deste repositório.
