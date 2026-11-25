"""Gera a figura ping_lampada (Cap. 5): respostas a ping da lâmpada durante o ataque,
no cenário WPA2 (sem PMF) e no modo misto WPA2/WPA3 (SAE com PMF obrigatório).

Uso (a partir da raiz do projeto):
    python src/figura_ping_lampada.py                       # grava Imagens/ping_lampada.png
    python src/figura_ping_lampada.py Imagens/outro.png     # grava em outro caminho

Os dados vêm dos logs de ping reais dos ensaios (Capturas/*/LAMP_*_ping.txt), com as
mesmas regras de validade de src/analisa_ping.py (descarta DUP!, time=0.000 e ecos
seguidos de "wrong data byte"). O eixo horizontal é o tempo desde o início da captura
(.pcapng de mesmo nome), o mesmo referencial da janela de ataque da Tabela 8 (Apêndice B).
Intervalos sem resposta: diferença maior que LIMIAR (2 s) entre respostas válidas.
"""
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analisa_ping import CAPINFOS, CAPTURAS, LIMIAR, RAIZ, RE_RESP  # noqa: E402

VERMELHO = "#E04545"
AZUL = "#4A7FEB"
CINZA = "#BBBBBB"

# (execução, título do painel, janela de ataque em s desde o início da captura — Tabela 8)
EXECUCOES = [
    ("LAMP_WPA2_R01", "WPA2 (PSK, sem PMF) — LAMP_WPA2_R01", (50.8, 89.4), VERMELHO),
    ("LAMP_WPA3_R01", "Modo misto WPA2/WPA3 (SAE, PMF obrigatório) — LAMP_WPA3_R01", (31.2, 76.9), AZUL),
]


def respostas(log: Path):
    """Lista (instante, rtt_ms) das respostas válidas, com as regras de analisa_ping.py."""
    linhas = log.read_text(encoding="utf-8", errors="replace").splitlines()
    saida = []
    for i, linha in enumerate(linhas):
        m = RE_RESP.match(linha)
        if not m:
            continue
        prox = linhas[i + 1] if i + 1 < len(linhas) else ""
        if "DUP!" in linha or m.group(3) == "0.000" or prox.startswith("wrong data byte"):
            continue
        saida.append((float(m.group(1)), float(m.group(3))))
    return saida


def tempos_captura(pcap: Path):
    """Instantes (epoch) do primeiro e do último quadro da captura."""
    saida = subprocess.run([str(CAPINFOS), "-T", "-r", "-a", "-e", "-S", str(pcap)],
                           capture_output=True, text=True, check=True).stdout
    _, ini, fim = saida.strip().split("\t")
    return float(ini), float(fim)


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def desenha(saida: Path):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, eixos = plt.subplots(len(EXECUCOES), 1, figsize=(8.8, 5.2), dpi=200, sharex=True)

    for ax, (nome, titulo, (ini_atq, fim_atq), cor) in zip(eixos, EXECUCOES):
        pasta = next(CAPTURAS.glob(f"*/{nome}_ping.txt")).parent
        ini_cap, fim_cap = tempos_captura(pasta / f"{nome}.pcapng")
        resp = [(t - ini_cap, rtt) for t, rtt in respostas(pasta / f"{nome}_ping.txt")]
        ts = [t for t, _ in resp]

        ax.axvspan(ini_atq, fim_atq, color=CINZA, alpha=0.35, lw=0, zorder=0)
        gaps = [(a, b) for a, b in zip(ts, ts[1:]) if b - a > LIMIAR]
        if fim_cap - ini_cap - ts[-1] > LIMIAR:
            gaps.append((ts[-1], fim_cap - ini_cap))
        for a, b in gaps:
            ax.axvspan(a, b, color=VERMELHO, alpha=0.18, lw=0, zorder=1)
        ax.plot(ts, [r for _, r in resp], marker="o", markersize=2.6, linestyle="none", color=cor, zorder=3)
        ax.set_yscale("log")
        ax.set_ylabel("RTT (ms)")
        ax.set_title(titulo, fontsize=10, loc="left")
        ax.grid(axis="y", color="#DDDDDD", lw=0.6, zorder=0)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)

        acum = sum(b - a for a, b in gaps)
        resumo = (f"{len(resp)} respostas válidas; tempo acumulado sem resposta: {virgula(acum)} s"
                  if gaps else f"{len(resp)} respostas válidas; nenhum intervalo sem resposta > 2 s")
        ax.text(0.99, 0.95, resumo, transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "#CCCCCC", "boxstyle": "round,pad=0.3"})
        print(f"{nome}: {len(resp)} respostas válidas, {len(gaps)} intervalo(s) > 2 s, acumulado {virgula(acum)} s")

    eixos[-1].set_xlabel("Tempo desde o início da captura (s)")
    fig.legend(handles=[Patch(color=CINZA, alpha=0.35, label="Janela de ataque (Apêndice B)"),
                        Patch(color=VERMELHO, alpha=0.18, label="Intervalo sem resposta (> 2 s)")],
               loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida, bbox_inches="tight")
    print(f"Figura gravada em {saida}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "Imagens" / "ping_lampada.png"
    desenha(destino)
