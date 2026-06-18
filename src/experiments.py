"""
Modulo: experiments.py
Bateria de experimentos para avaliacao do algoritmo Push-Relabel.

Experimentos:
  1. Escalabilidade por tamanho de rede (diferentes n_vertices)
  2. Impacto da densidade de arestas no desempenho
  3. Identificacao de gargalos via corte minimo
"""

import time
import json
import os
import statistics
from typing import List, Dict, Any

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

from push_relabel import PushRelabel
from network_generator import (
    generate_random_network,
    generate_layered_network,
    generate_worst_case_network,
)

# EXPERIMENTO 1 -- Escalabilidade por Tamanho de Rede

def experimento_escalabilidade(
    tamanhos: List[int] = None,
    density: float = 0.3,
    max_cap: float = 100.0,
    n_repeticoes: int = 5
) -> List[Dict[str, Any]]:
    """
    Avalia a escalabilidade do Push-Relabel em redes de diferentes tamanhos.

    Mantém a densidade fixa em 0.3 e varia o numero de vertices,
    medindo tempo, Push, Relabel, fluxo maximo e numero de gargalos.

    Args:
        tamanhos (List[int]): Lista de tamanhos de rede a testar.
        density (float): Densidade de arestas (fixada em 0.3).
        max_cap (float): Capacidade maxima dos enlaces.
        n_repeticoes (int): Redes distintas por configuracao (para media e desvio).

    Returns:
        List[Dict]: Lista de resultados por tamanho de rede.
    """
    if tamanhos is None:
        tamanhos = [10, 50, 100, 250, 500, 1000]

    resultados = []
    print("\n" + "=" * 60)
    print("  EXPERIMENTO 1 -- Escalabilidade por Tamanho")
    print("=" * 60)
    print(f"  Densidade: {density} | Capacidade max: {max_cap}")
    print(f"  Repeticoes por tamanho: {n_repeticoes}")
    print("-" * 60)

    for n in tamanhos:
        tempos, pushes, relabels, fluxos, n_gargalos = [], [], [], [], []

        for rep in range(n_repeticoes):
            pr, edges, source, sink = generate_random_network(
                n_vertices=n,
                density=density,
                max_capacity=max_cap,
                seed=rep * 100 + n
            )

            inicio = time.perf_counter()
            max_flow = pr.run(source, sink)
            fim = time.perf_counter()

            tempo_ms = (fim - inicio) * 1000
            stats = pr.get_stats()
            _, _, gargalos = pr.get_min_cut(source)

            tempos.append(tempo_ms)
            pushes.append(stats["n_push"])
            relabels.append(stats["n_relabel"])
            fluxos.append(max_flow)
            n_gargalos.append(len(gargalos))

        n_arestas_aprox = int(density * n * (n - 1))
        resultado = {
            "n_vertices": n,
            "n_arestas_aprox": n_arestas_aprox,
            "density": density,
            "tempo_ms_media": round(statistics.mean(tempos), 3),
            "tempo_ms_desvio": round(statistics.stdev(tempos) if len(tempos) > 1 else 0, 3),
            "n_push_media": round(statistics.mean(pushes), 1),
            "n_push_desvio": round(statistics.stdev(pushes) if len(pushes) > 1 else 0, 1),
            "n_relabel_media": round(statistics.mean(relabels), 1),
            "n_relabel_desvio": round(statistics.stdev(relabels) if len(relabels) > 1 else 0, 1),
            "fluxo_max_media": round(statistics.mean(fluxos), 2),
            "n_gargalos_media": round(statistics.mean(n_gargalos), 1),
        }
        resultados.append(resultado)

        print(f"  {n:>4d} vertices  (~{n_arestas_aprox:>6d} enlaces)"
              f"  |  Tempo: {resultado['tempo_ms_media']:>8.3f} ms (+/- {resultado['tempo_ms_desvio']:.3f})"
              f"  |  Push: {resultado['n_push_media']:.0f}"
              f"  |  Relabel: {resultado['n_relabel_media']:.0f}")

    return resultados


# EXPERIMENTO 2 -- Impacto da Densidade de Arestas

def experimento_densidade(
    densidades: List[float] = None,
    n_vertices: int = 100,
    max_cap: float = 100.0,
    n_repeticoes_padrao: int = 7,
    n_repeticoes_instavel: int = 15
) -> List[Dict[str, Any]]:
    """
    Avalia o impacto da densidade de arestas no desempenho do Push-Relabel.

    Mantém o tamanho da rede fixo em 100 vertices e varia a densidade.
    Densidades instáveis (0.3 e 1.0) recebem mais repeticoes para
    reduzir o desvio padrao e tornar as medias estatisticamente confiaveis.

    Args:
        densidades (List[float]): Lista de densidades a testar.
        n_vertices (int): Numero de vertices (fixado em 100).
        max_cap (float): Capacidade maxima dos enlaces.
        n_repeticoes_padrao (int): Repeticoes para densidades estaveis.
        n_repeticoes_instavel (int): Repeticoes para densidades instáveis (0.3 e 1.0).

    Returns:
        List[Dict]: Lista de resultados por densidade.
    """
    if densidades is None:
        densidades = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    # Densidades que apresentaram desvio padrao maior que a media nas execucoes anteriores
    densidades_instaveis = {0.3, 1.0}

    resultados = []
    print("\n" + "=" * 60)
    print("  EXPERIMENTO 2 -- Impacto da Densidade")
    print("=" * 60)
    print(f"  Vertices: {n_vertices} | Capacidade max: {max_cap}")
    print(f"  Repeticoes padrao: {n_repeticoes_padrao} | "
          f"Repeticoes densidades instaveis: {n_repeticoes_instavel}")
    print("-" * 60)

    for density in densidades:
        # Usa mais repeticoes nas densidades que historicamente apresentaram alta variancia
        n_rep = n_repeticoes_instavel if density in densidades_instaveis else n_repeticoes_padrao

        tempos, pushes, relabels, fluxos, n_gargalos = [], [], [], [], []

        for rep in range(n_rep):
            pr, edges, source, sink = generate_random_network(
                n_vertices=n_vertices,
                density=density,
                max_capacity=max_cap,
                seed=rep * 200 + int(density * 100)
            )

            inicio = time.perf_counter()
            max_flow = pr.run(source, sink)
            fim = time.perf_counter()

            tempo_ms = (fim - inicio) * 1000
            stats = pr.get_stats()
            _, _, gargalos = pr.get_min_cut(source)

            tempos.append(tempo_ms)
            pushes.append(stats["n_push"])
            relabels.append(stats["n_relabel"])
            fluxos.append(max_flow)
            n_gargalos.append(len(gargalos))

        n_arestas = int(density * n_vertices * (n_vertices - 1))
        resultado = {
            "density": density,
            "n_vertices": n_vertices,
            "n_arestas": n_arestas,
            "n_repeticoes": n_rep,
            "tempo_ms_media": round(statistics.mean(tempos), 3),
            "tempo_ms_desvio": round(statistics.stdev(tempos) if len(tempos) > 1 else 0, 3),
            "n_push_media": round(statistics.mean(pushes), 1),
            "n_push_desvio": round(statistics.stdev(pushes) if len(pushes) > 1 else 0, 1),
            "n_relabel_media": round(statistics.mean(relabels), 1),
            "n_relabel_desvio": round(statistics.stdev(relabels) if len(relabels) > 1 else 0, 1),
            "fluxo_max_media": round(statistics.mean(fluxos), 2),
            "n_gargalos_media": round(statistics.mean(n_gargalos), 1),
        }
        resultados.append(resultado)

        print(f"  densidade={density:.1f}  ({n_rep:>2d} rep, ~{n_arestas:>5d} enlaces)"
              f"  |  Tempo: {resultado['tempo_ms_media']:>7.3f} ms (+/- {resultado['tempo_ms_desvio']:.3f})"
              f"  |  Fluxo: {resultado['fluxo_max_media']:.1f} Gbps"
              f"  |  Gargalos: {resultado['n_gargalos_media']:.1f}")

    return resultados


# EXPERIMENTO 3 -- Identificacao de Gargalos (Corte Minimo)

def experimento_gargalos() -> List[Dict[str, Any]]:
    """
    Avalia a identificacao de gargalos via corte minimo em topologias distintas.

    Testa tres topologias:
      - Rede aleatoria esparsa (simula rede corporativa simples)
      - Rede em camadas (simula topologia de data center)
      - Rede de pior caso (para demonstrar robustez do Push-Relabel)

    Para cada topologia, extrai os enlaces gargalo com suas saturacoes.

    Returns:
        List[Dict]: Resultados com gargalos identificados por topologia.
    """
    resultados = []
    print("\n" + "=" * 60)
    print("  EXPERIMENTO 3 -- Identificacao de Gargalos")
    print("=" * 60)

    topologias = [
        ("Rede Aleatoria Esparsa (n=20, d=0.2)", "aleatoria_esparsa"),
        ("Rede em Camadas (3 camadas, 4 nos/camada)", "camadas"),
        ("Rede de Pior Caso (n=8)", "pior_caso"),
    ]

    for nome, tipo in topologias:
        print(f"\n  -- {nome}")

        if tipo == "aleatoria_esparsa":
            pr, edges, source, sink = generate_random_network(
                20, 0.2, 50.0, seed=42
            )
        elif tipo == "camadas":
            pr, edges, source, sink = generate_layered_network(
                3, 4, 50.0, seed=42
            )
        else:
            pr, edges, source, sink = generate_worst_case_network(4)

        max_flow = pr.run(source, sink)
        S, T, gargalos = pr.get_min_cut(source)

        gargalos_info = []
        for u, v, cap, fluxo, sat in gargalos:
            gargalos_info.append({
                "aresta": f"{u}->{v}",
                "capacidade": round(cap, 2),
                "fluxo": round(fluxo, 2),
                "saturacao_pct": round(sat, 1)
            })
            print(f"     Enlace ({u} -> {v}): "
                  f"{fluxo:.1f} de {cap:.1f} Gbps em uso ({sat:.0f}% de saturacao)")

        resultado = {
            "topologia": nome,
            "tipo": tipo,
            "n_vertices": pr.n,
            "n_edges": len(edges),
            "source": source,
            "sink": sink,
            "fluxo_maximo": round(max_flow, 2),
            "n_gargalos": len(gargalos),
            "gargalos": gargalos_info,
            "S": S,
            "T": T
        }
        resultados.append(resultado)
        print(f"     Fluxo maximo: {max_flow:.2f} Gbps  |  Gargalos encontrados: {len(gargalos)}")

    return resultados


# Execucao e persistencia dos resultados

def executar_todos(output_path: str = None) -> Dict:
    """
    Executa todos os experimentos e salva os resultados em JSON.

    Args:
        output_path (str): Caminho do arquivo de saida.

    Returns:
        Dict: Dicionario com todos os resultados.
    """
    if output_path is None:
        output_path = os.path.join(_DATA_DIR, "resultados_experimentos.json")
    todos = {
        "experimento_1_escalabilidade": experimento_escalabilidade(),
        "experimento_2_densidade": experimento_densidade(),
        "experimento_3_gargalos": experimento_gargalos()
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"\n  Resultados salvos em: {output_path}")
    return todos
