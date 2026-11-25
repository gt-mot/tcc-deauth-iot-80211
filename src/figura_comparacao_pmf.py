"""Gera a Figura comparacao_pmf (Cap. 5) a partir dos logs de ping.

Uso (a partir da raiz do projeto):
    python src/figura_comparacao_pmf.py                  # grava Imagens/comparacao_pmf_novo.png
    python src/figura_comparacao_pmf.py Imagens/comparacao_pmf.png   # substitui a figura

Os valores vêm de src/analisa_ping.py (mesmas regras de validade das respostas).
Barra = média das frações das execuções; quando alguma execução é limite
inferior (queda até o fim da captura), a média também é limite inferior e o
rótulo recebe "≥"; o ponto dessa execução é desenhado como triângulo.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analisa_ping import CAPTURAS, RAIZ, analisa  # noqa: E402

VERMELHO = "#E04545"
AZUL = "#4A7FEB"

# (dispositivo, [execuções WPA2], [execuções misto], cor misto, anotação misto)
GRUPOS = [
    ("Câmera", ["CAM_WPA2_R03", "CAM_WPA2_R04"], ["CAM_WPA2_R02", "CAM_WPA3_R01"], VERMELHO, "PSK\nsem PMF"),
    ("Tomada", ["TOMADA_WPA2_R01", "TOMADA_WPA2_R02", "TOMADA_WPA2_R03"], ["TOMADA_WPA3_R01"], VERMELHO, "PSK\nsem PMF"),
    ("Lâmpada", ["LAMP_WPA2_R01", "LAMP_WPA2_R02", "LAMP_WPA2_R03"], ["LAMP_WPA3_R01"], AZUL, "SAE\nPMF obrig."),
    ("Smartphone", ["PHONE_WPA2_R01", "PHONE_WPA2_R02", "PHONE_WPA2_R03"], ["PHONE_WPA3_R01", "PHONE_WPA3_R03"], AZUL, "PMF\n(indício)"),
]


def resultados():
    return {p.name.replace("_ping.txt", ""): analisa(p) for p in sorted(CAPTURAS.glob("*/*_ping.txt"))}


def desenha(saida: Path):
    res = resultados()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(8.8, 3.55), dpi=200)
    largura = 0.38

    for i, (disp, wpa2, misto, cor_misto, nota) in enumerate(GRUPOS):
        for lado, execs, cor, hachura in ((-1, wpa2, VERMELHO, None), (1, misto, cor_misto, "//")):
            x = i + lado * largura / 2
            vals = [res[e]["fracao_pct"] for e in execs]
            li = [res[e]["limite_inferior"] for e in execs]
            media = sum(vals) / len(vals)
            ax.bar(x, media, largura, color=cor, hatch=hachura, edgecolor="white", linewidth=0.8, zorder=2)
            rot = ("≥" if any(li) else "") + f"{media:.0f}%"
            topo = max([media] + vals) + 1.5
            ax.text(x, topo, rot, ha="center", va="bottom", fontsize=11)
            desloc = [0.0] if len(vals) == 1 else [(-0.12 + 0.24 * k / (len(vals) - 1)) * largura for k in range(len(vals))]
            for dx, v, l in zip(desloc, vals, li):
                ax.plot(x + dx, v, marker="^" if l else "o", color="black", markeredgecolor="white",
                        markersize=6 if l else 5, linestyle="none", zorder=3)
            ax.text(x, -3, f"n={len(vals)}", ha="center", va="top", fontsize=9, color="#333333")
            if lado == 1:
                ax.text(x, topo + 6, nota, ha="center", va="bottom",
                        fontsize=8, style="italic", color="#444444", linespacing=1.1)

    ax.set_xticks(range(len(GRUPOS)))
    ax.set_xticklabels([g[0] for g in GRUPOS])
    ax.tick_params(axis="x", length=0, pad=24)
    ax.set_ylim(0, 80)
    ax.set_yticks(range(0, 81, 10))
    ax.set_xlim(-0.6, len(GRUPOS) - 0.4)
    ax.set_ylabel("Tempo sem resposta a ping\n(% da duração do log; > 2 s)")
    ax.set_title("Impacto do ataque de desautenticação por dispositivo e cenário", pad=26)
    ax.yaxis.grid(True, linestyle=":", color="#cccccc", zorder=0)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    legenda = [
        Patch(facecolor=VERMELHO, label="Sem PMF negociado"),
        Patch(facecolor=AZUL, label="Com PMF negociado"),
        Patch(facecolor="#bbbbbb", label="Cenário WPA2"),
        Patch(facecolor="#bbbbbb", hatch="//", edgecolor="white", label="Cenário misto WPA2/WPA3"),
        Line2D([], [], marker="o", color="black", markeredgecolor="white", linestyle="none", label="Execução individual"),
        Line2D([], [], marker="^", color="black", markeredgecolor="white", linestyle="none", label="Limite inferior (≥)"),
    ]
    ax.legend(handles=legenda, loc="upper center", bbox_to_anchor=(0.45, -0.22), ncol=3, fontsize=9,
              frameon=True, columnspacing=1.2, handletextpad=0.5)
    fig.savefig(saida, dpi=200, bbox_inches="tight", pad_inches=0.12)
    print(f"Figura gravada em {saida}")
    for disp, wpa2, misto, _, _ in GRUPOS:
        for cen, execs in (("WPA2", wpa2), ("misto", misto)):
            vals = [res[e]["fracao_pct"] for e in execs]
            li = any(res[e]["limite_inferior"] for e in execs)
            print(f"  {disp:<11}{cen:<6} n={len(vals)}  {'≥' if li else ''}{sum(vals)/len(vals):.1f}%  "
                  + ", ".join(f"{'≥' if res[e]['limite_inferior'] else ''}{res[e]['fracao_pct']:.1f}" for e in execs))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "Imagens" / "comparacao_pmf_novo.png"
    desenha(destino)
