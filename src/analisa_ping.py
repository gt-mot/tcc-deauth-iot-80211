"""Recalcula as métricas de conectividade dos logs de ping do TCC.

Uso (a partir da raiz do projeto):
    python src/analisa_ping.py            # tabela de todas as execuções
    python src/analisa_ping.py --csv      # mesma tabela em CSV (stdout)

Regras (Seção "Dicionário de métricas" do Cap. 5):
- Resposta válida: linha "bytes from ... icmp_seq=N ... time=X ms" que NÃO
  tenha "(DUP!)", cujo tempo NÃO seja 0.000 ms e que NÃO seja seguida da
  linha "wrong data byte" (eco corrompido). A regra vale também para a
  primeira ocorrência do eco corrompido, que o ping não marca como DUP!.
- Intervalo sem resposta: diferença entre respostas válidas consecutivas
  maior que LIMIAR (2 s).
- Tempo acumulado: soma dos intervalos sem resposta.
- Maior queda contínua: maior intervalo sem resposta.
- Queda até o fim da captura: se o tempo entre a última resposta válida e o
  último quadro da captura (.pcapng de mesmo nome) for maior que LIMIAR, esse
  intervalo entra na soma e no máximo, e o valor é marcado como limite
  inferior (>=), pois a recuperação não foi observada.
- Duração do log: da primeira resposta válida à última resposta válida ou,
  havendo queda até o fim da captura, ao último quadro da captura.
- Fração sem resposta (%) = tempo acumulado / duração do log * 100.
"""
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

LIMIAR = 2.0
RAIZ = Path(__file__).resolve().parent.parent
CAPTURAS = RAIZ / "Capturas"
# capinfos vem com o Wireshark: usa o do PATH (Linux/macOS) ou o caminho padrão do Windows.
CAPINFOS = Path(shutil.which("capinfos") or r"C:\Program Files\Wireshark\capinfos.exe")

RE_RESP = re.compile(r"^\[(\d+\.\d+)\].*bytes from .*icmp_seq=(\d+).*time=([\d.]+) ms")


def respostas_validas(log: Path):
    linhas = log.read_text(encoding="utf-8", errors="replace").splitlines()
    validas, descartadas = [], 0
    for i, linha in enumerate(linhas):
        m = RE_RESP.match(linha)
        if not m:
            continue
        prox = linhas[i + 1] if i + 1 < len(linhas) else ""
        if "DUP!" in linha or m.group(3) == "0.000" or prox.startswith("wrong data byte"):
            descartadas += 1
            continue
        validas.append(float(m.group(1)))
    return validas, descartadas


def fim_captura(pcap: Path):
    if not pcap.exists():
        return None
    saida = subprocess.run([str(CAPINFOS), "-T", "-r", "-e", "-S", str(pcap)],
                           capture_output=True, text=True, check=True).stdout
    return float(saida.strip().split("\t")[-1])


def analisa(log: Path):
    nome = log.name.replace("_ping.txt", "")
    ts, descartadas = respostas_validas(log)
    fim = fim_captura(log.with_name(nome + ".pcapng"))
    gaps = [b - a for a, b in zip(ts, ts[1:]) if b - a > LIMIAR]
    limite_inferior = False
    fim_obs = ts[-1]
    if fim is not None and fim - ts[-1] > LIMIAR:
        gaps.append(fim - ts[-1])
        limite_inferior = True
        fim_obs = fim
    acum = sum(gaps)
    maior = max(gaps) if gaps else 0.0
    duracao = fim_obs - ts[0]
    return {
        "execucao": nome,
        "validas": len(ts),
        "descartadas": descartadas,
        "acumulado_s": acum,
        "maior_queda_s": maior,
        "limite_inferior": limite_inferior,
        "ultima_valida_s": ts[-1] - ts[0],
        "duracao_log_s": duracao,
        "fracao_pct": 100 * acum / duracao if duracao else 0.0,
    }


def fmt(v, li):
    return ("≥" if li else "") + f"{v:.1f}".replace(".", ",")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    logs = sorted(CAPTURAS.glob("*/*_ping.txt"))
    res = [analisa(p) for p in logs]
    if "--csv" in sys.argv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)
        return
    cab = f"{'Execução':<22}{'válidas':>8}{'desc.':>6}{'acum. (s)':>11}{'maior (s)':>11}{'duração (s)':>13}{'fração':>9}"
    print(cab)
    print("-" * len(cab))
    for r in res:
        li = r["limite_inferior"]
        print(f"{r['execucao']:<22}{r['validas']:>8}{r['descartadas']:>6}"
              f"{fmt(r['acumulado_s'], li):>11}{fmt(r['maior_queda_s'], li):>11}"
              f"{fmt(r['duracao_log_s'], False):>13}{fmt(r['fracao_pct'], li) + '%':>9}")
    print("\n≥ = queda até o fim da captura (limite inferior; recuperação não observada).")


if __name__ == "__main__":
    main()
