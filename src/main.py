"""
Modulo: main.py
Ponto de entrada do projeto Push-Relabel para Fluxo Maximo em Redes de Computadores.

Artigo: "Maximizacao de Throughput em Redes de Computadores usando Fluxo Maximo em Grafos"
Disciplina: ICC041/PPGINF539 -- Teoria dos Grafos, UFAM 2026/01
Profa. Rosiane de Freitas
"""

import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from push_relabel import PushRelabel
from experiments import executar_todos
from visualizations import gerar_todas_visualizacoes

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def demonstracao_figura1() -> None:
    """
    Demonstra o algoritmo passo a passo usando a rede da Figura 1 do artigo.

    Topologia:
        s (0) -> u (1): cap=15
        s (0) -> v (2): cap=10
        u (1) -> t (3): cap=12
        u (1) -> v (2): cap=5
        v (2) -> t (3): cap=4

    Segue exatamente a Secao 3.4 do artigo (Execucao Passo a Passo).
    Fluxo maximo esperado: 16 Gbps
    Gargalos: (u->t) com 12/12 Gbps e (v->t) com 4/4 Gbps
    """
    print("\n" + "=" * 60)
    print("  DEMONSTRACAO -- REDE DA FIGURA 1 DO ARTIGO")
    print("  (Secao 3.4 -- Execucao Passo a Passo)")
    print("=" * 60)
    print("  Topologia:")
    print("    s(0) -> u(1): cap=15 Gbps")
    print("    s(0) -> v(2): cap=10 Gbps")
    print("    u(1) -> t(3): cap=12 Gbps")
    print("    u(1) -> v(2): cap=5  Gbps")
    print("    v(2) -> t(3): cap=4  Gbps")
    print("-" * 60)

    s, u, v, t = 0, 1, 2, 3
    NOMES = {s: "s", u: "u", v: "v", t: "t"}

    pr = PushRelabel(n_vertices=4, verbose=True)
    pr.add_edge(s, u, 15)
    pr.add_edge(s, v, 10)
    pr.add_edge(u, t, 12)
    pr.add_edge(u, v, 5)
    pr.add_edge(v, t, 4)

    max_flow = pr.run(source=s, sink=t)
    S, T, gargalos = pr.get_min_cut(source=s)

    print("\n" + "-" * 60)
    print(f"  Fluxo Maximo: {max_flow:.0f} Gbps")
    print(f"\n  Corte Minimo encontrado:")
    print(f"    Sub-rede da fonte      S = {{ {', '.join(NOMES[x] for x in S)} }}")
    print(f"    Sub-rede do sumidouro  T = {{ {', '.join(NOMES[x] for x in T)} }}")
    print(f"\n  Gargalos identificados pelo corte minimo:")

    if gargalos:
        for gu, gv, cap, fluxo, sat in gargalos:
            nome_u = NOMES.get(gu, str(gu))
            nome_v = NOMES.get(gv, str(gv))
            print(f"    * Enlace ({nome_u} -> {nome_v}): "
                  f"{fluxo:.0f} de {cap:.0f} Gbps em uso ({sat:.0f}% de saturacao)")

    stats = pr.get_stats()
    print(f"\n  Estatisticas:")
    print(f"    Operacoes Push realizadas:    {stats['n_push']}")
    print(f"    Operacoes Relabel realizadas: {stats['n_relabel']}")
    print("=" * 60)


def main() -> None:
    """
    Ponto de entrada principal do projeto.

    Executa:
      1. Demonstracao didatica com a rede da Figura 1
      2. Bateria completa de experimentos
      3. Geracao de tabelas e graficos (bonus)
      4. Sumario final
    """
    inicio_total = time.perf_counter()

    # Demonstracao didatica
    demonstracao_figura1()

    # Experimentos
    print("\n" + "=" * 60)
    print("  INICIANDO BATERIA DE EXPERIMENTOS")
    print("=" * 60)
    todos = executar_todos(output_path=os.path.join(_DATA_DIR, "resultados_experimentos.json"))

    # Tabelas e Graficos (Bonus C06)
    gerar_todas_visualizacoes(todos)

    # Sumario Final
    fim_total = time.perf_counter()
    tempo_total = fim_total - inicio_total

    print("\n" + "=" * 60)
    print("  SUMARIO FINAL")
    print("=" * 60)

    print("\n  Rede da Figura 1 (Secao 3.4):")
    print("    Fluxo maximo:  16 Gbps")
    print("    Gargalos:      (u -> t) 12 de 12 Gbps  |  (v -> t) 4 de 4 Gbps")

    exp1 = todos["experimento_1_escalabilidade"]
    melhor = min(exp1, key=lambda r: r["tempo_ms_media"] / r["n_vertices"])
    print(f"\n  Melhor relacao tempo/vertice (Exp. 1):")
    print(f"    {melhor['n_vertices']} vertices"
          f"  |  Tempo medio: {melhor['tempo_ms_media']:.3f} ms"
          f"  |  Fluxo: {melhor['fluxo_max_media']:.1f} Gbps")

    exp2 = todos["experimento_2_densidade"]
    maior_fluxo = max(exp2, key=lambda r: r["fluxo_max_media"])
    print(f"\n  Maior fluxo medio encontrado (Exp. 2):")
    print(f"    Densidade={maior_fluxo['density']:.1f}"
          f"  |  Fluxo medio: {maior_fluxo['fluxo_max_media']:.1f} Gbps"
          f"  |  Tempo: {maior_fluxo['tempo_ms_media']:.3f} ms")

    print(f"\n  Arquivos gerados em /data:")
    arquivos = [
        "resultados_experimentos.json",
        "tabela_escalabilidade.csv  e  tabela_escalabilidade.tex",
        "tabela_densidade.csv  e  tabela_densidade.tex",
        "tabela_gargalos.csv  e  tabela_gargalos.tex",
        "grafico_tempo_vertices.png  e  grafico_tempo_vertices.pdf",
        "grafico_operacoes.png  e  grafico_operacoes.pdf",
        "grafico_densidade.png  e  grafico_densidade.pdf",
        "grafico_fluxo_densidade.png  e  grafico_fluxo_densidade.pdf",
        "grafico_rede_gargalos.png  e  grafico_rede_gargalos.pdf",
    ]
    for arq in arquivos:
        print(f"    [ok] {arq}")

    print(f"\n  Tempo total de execucao: {tempo_total:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
