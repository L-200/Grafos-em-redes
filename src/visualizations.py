"""
Modulo: visualizations.py
Bonus C06: Tabelas de experimentos e graficos de resultados.

Gera:
  - Tabelas formatadas (CSV + LaTeX para insercao direta no Overleaf)
  - Graficos de desempenho em alta resolucao (PNG + PDF, 300 DPI)
"""

import os
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# -- Estilo global compativel com LaTeX ---------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

PALETA = ["#1f4e79", "#c55a11", "#538135", "#7030a0", "#c00000", "#2e75b6"]
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _salvar(fig, nome: str) -> None:
    """Salva figura em PNG e PDF no diretorio de saida."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for ext in ["png", "pdf"]:
        path = os.path.join(OUTPUT_DIR, f"{nome}.{ext}")
        fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [ok] Grafico gerado: {nome}.png  e  {nome}.pdf")


def tabela_escalabilidade(resultados: List[Dict]) -> pd.DataFrame:
    """Gera e exporta a tabela do Experimento 1."""
    rows = []
    for r in resultados:
        rows.append({
            "Vertices": r["n_vertices"],
            "Arestas (aprox.)": r["n_arestas_aprox"],
            "Fluxo Max. (media)": f"{r['fluxo_max_media']:.1f}",
            "Tempo (ms)": f"{r['tempo_ms_media']:.3f} +/- {r['tempo_ms_desvio']:.3f}",
            "Push (media)": f"{r['n_push_media']:.0f} +/- {r['n_push_desvio']:.0f}",
            "Relabel (media)": f"{r['n_relabel_media']:.0f} +/- {r['n_relabel_desvio']:.0f}",
            "Gargalos (media)": f"{r['n_gargalos_media']:.1f}",
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "tabela_escalabilidade.csv"), index=False)

    latex = df.to_latex(
        index=False,
        caption="Desempenho do Push-Relabel em redes de diferentes tamanhos (densidade=0.3).",
        label="tab:escalabilidade",
        column_format="r r r r r r r",
        escape=False
    )
    with open(os.path.join(OUTPUT_DIR, "tabela_escalabilidade.tex"), "w") as f:
        f.write(latex)

    print("\n  TABELA 1: Desempenho por Tamanho de Rede")
    print(df.to_string(index=False))
    print("  Exportado: tabela_escalabilidade.csv  e  tabela_escalabilidade.tex")
    return df


def tabela_densidade(resultados: List[Dict]) -> pd.DataFrame:
    """Gera e exporta a tabela do Experimento 2."""
    rows = []
    for r in resultados:
        rows.append({
            "Densidade": f"{r['density']:.1f}",
            "Rep.": r.get("n_repeticoes", "-"),
            "Arestas (aprox.)": r["n_arestas"],
            "Fluxo Max. (media)": f"{r['fluxo_max_media']:.1f}",
            "Tempo (ms)": f"{r['tempo_ms_media']:.3f} +/- {r['tempo_ms_desvio']:.3f}",
            "Push (media)": f"{r['n_push_media']:.0f} +/- {r['n_push_desvio']:.0f}",
            "Relabel (media)": f"{r['n_relabel_media']:.0f} +/- {r['n_relabel_desvio']:.0f}",
            "Gargalos (media)": f"{r['n_gargalos_media']:.1f}",
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "tabela_densidade.csv"), index=False)

    latex = df.to_latex(
        index=False,
        caption="Desempenho do Push-Relabel em redes com diferentes densidades (n=100).",
        label="tab:densidade",
        column_format="r r r r r r r r",
        escape=False
    )
    with open(os.path.join(OUTPUT_DIR, "tabela_densidade.tex"), "w") as f:
        f.write(latex)

    print("\n  TABELA 2: Impacto da Densidade no Desempenho")
    print(df.to_string(index=False))
    print("  Exportado: tabela_densidade.csv  e  tabela_densidade.tex")
    return df


def tabela_gargalos(resultados_exp3: List[Dict]) -> pd.DataFrame:
    """Gera e exporta a tabela do Experimento 3."""
    rows = []
    for topo in resultados_exp3:
        for g in topo["gargalos"]:
            rows.append({
                "Topologia": topo["topologia"].split("(")[0].strip(),
                "Aresta": g["aresta"],
                "Cap. (Gbps)": g["capacidade"],
                "Fluxo (Gbps)": g["fluxo"],
                "Saturacao (%)": g["saturacao_pct"],
            })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "tabela_gargalos.csv"), index=False)

    latex = df.to_latex(
        index=False,
        caption="Gargalos identificados pelo corte minimo em diferentes topologias de rede.",
        label="tab:gargalos",
        column_format="l c r r r",
        escape=False
    )
    with open(os.path.join(OUTPUT_DIR, "tabela_gargalos.tex"), "w") as f:
        f.write(latex)

    print("\n  TABELA 3: Gargalos Identificados por Topologia")
    print(df.to_string(index=False))
    print("  Exportado: tabela_gargalos.csv  e  tabela_gargalos.tex")
    return df


def grafico_tempo_vs_vertices(resultados: List[Dict]) -> None:
    """
    Gráfico de linha: tempo médio de execução vs número de vértices.
    Escala linear limpa, com separadores de milhares no eixo Y para legibilidade.
    """
    vertices = [r["n_vertices"] for r in resultados]
    tempos = [r["tempo_ms_media"] for r in resultados]
    erros = [r["tempo_ms_desvio"] for r in resultados]

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.errorbar(vertices, tempos, yerr=erros,
                fmt='o-', color=PALETA[0], linewidth=2,
                markersize=6, capsize=4, elinewidth=1.2,
                label="Tempo Médio (+/- Desvio)")

    ax.set_xlabel("Número de Vértices (|V|)")
    ax.set_ylabel("Tempo de Execução (ms)")
    ax.set_title("Escalabilidade por Tamanho de Rede")
    
    ax.set_xticks(vertices)
    ax.set_xticklabels([str(v) for v in vertices])
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    
    ax.legend(loc="upper left")
    _salvar(fig, "grafico_tempo_vertices")


def grafico_operacoes_vs_vertices(resultados: List[Dict]) -> None:
    """
    Gráfico de linha dupla: número de operações Push e Relabel vs vértices.
    Eixo Y formatado em milhares (k) para remover o excesso de zeros.
    """
    vertices = [r["n_vertices"] for r in resultados]
    pushes = [r["n_push_media"] for r in resultados]
    relabels = [r["n_relabel_media"] for r in resultados]
    err_push = [r["n_push_desvio"] for r in resultados]
    err_rel = [r["n_relabel_desvio"] for r in resultados]

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.errorbar(vertices, pushes, yerr=err_push,
                fmt='s-', color=PALETA[0], linewidth=2, markersize=6, 
                capsize=4, elinewidth=1.2, label="Operações Push")
    ax.errorbar(vertices, relabels, yerr=err_rel,
                fmt='^--', color=PALETA[2], linewidth=2, markersize=6, 
                capsize=4, elinewidth=1.2, label="Operações Relabel")

    ax.set_xlabel("Número de Vértices (|V|)")
    ax.set_ylabel("Quantidade de Operações")
    ax.set_title("Volume de Operações Locais vs Tamanho da Rede")
    
    ax.set_xticks(vertices)
    ax.set_xticklabels([str(v) for v in vertices])
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x > 0 else "0"))
    
    ax.legend(loc="upper left")
    _salvar(fig, "grafico_operacoes")


def grafico_tempo_vs_densidade(resultados: List[Dict]) -> None:
    """
    Gráfico de linha: tempo médio de execução vs densidade da rede.
    Anota o PICO de latência para convergir com o texto do artigo.
    """
    densidades = [r["density"] for r in resultados]
    tempos = [r["tempo_ms_media"] for r in resultados]
    erros = [r["tempo_ms_desvio"] for r in resultados]

    erros_inferiores = [min(e, t) for e, t in zip(erros, tempos)]
    erros_superiores = erros
    erros_assimetricos = [erros_inferiores, erros_superiores]

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.errorbar(densidades, tempos, yerr=erros_assimetricos,
                fmt='D-', color=PALETA[3], linewidth=2,
                markersize=6, capsize=4, elinewidth=1.2, 
                label="Tempo Médio (+/- Desvio)")

    idx_max = int(np.argmax(tempos))
    ax.annotate(f"Pico: {tempos[idx_max]:.0f} ms",
                xy=(densidades[idx_max], tempos[idx_max]),
                xytext=(densidades[idx_max] - 0.15, tempos[idx_max] * 1.05),
                arrowprops=dict(arrowstyle="->", color="black"),
                fontsize=10, fontweight="bold")

    ax.set_xlabel("Densidade da Rede")
    ax.set_ylabel("Tempo de Execução (ms)")
    ax.set_title("Impacto da Densidade no Desempenho (n=100)")
    
    ax.set_xticks(densidades)
    ax.legend(loc="lower right")
    
    _salvar(fig, "grafico_densidade")


def grafico_fluxo_vs_densidade(resultados: List[Dict]) -> None:
    """Gráfico de barras: fluxo máximo médio por densidade da rede."""
    densidades = [f"{r['density']:.1f}" for r in resultados]
    fluxos = [r["fluxo_max_media"] for r in resultados]

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(densidades, fluxos, color=PALETA[0],
                  edgecolor="white", linewidth=0.8, width=0.6)

    for bar, val in zip(bars, fluxos):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(fluxos) * 0.01,
                f"{val:.0f}", ha="center", va="bottom", fontsize=9)

    ax.set_xlabel("Densidade da Rede")
    ax.set_ylabel("Fluxo Máximo Médio (Gbps)")
    ax.set_title("Fluxo Máximo vs Densidade da Rede (n=100)")

    _salvar(fig, "grafico_fluxo_densidade")


def grafico_gargalos_rede(
    pr,
    edges: List[Tuple],
    gargalos: List[Tuple],
    n_vertices: int,
    source: int,
    sink: int,
    nome_arquivo: str = "grafico_rede_gargalos"
) -> None:
    """Visualizacao do grafo da rede com destaque nos enlaces gargalo."""
    G = nx.DiGraph()
    G.add_nodes_from(range(n_vertices))

    gargalo_set = {(g[0], g[1]) for g in gargalos}
    gargalo_info = {(g[0], g[1]): (g[2], g[3]) for g in gargalos}

    edge_labels = {}

    for u, v, cap in edges:
        G.add_edge(u, v)
        if (u, v) in gargalo_set:
            c, f = gargalo_info[(u, v)]
            edge_labels[(u, v)] = f"{f:.0f}/{c:.0f}"
        else:
            # Puxa o fluxo real do objeto pr para as arestas não-saturadas
            fluxo = pr.get_flow_on_edge(u, v)
            edge_labels[(u, v)] = f"{fluxo:.0f}/{cap:.0f}"

    node_colors = []
    for node in G.nodes():
        if node == source:
            node_colors.append("#1f4e79")
        elif node == sink:
            node_colors.append("#c00000")
        else:
            node_colors.append("#d9d9d9")

    fig, ax = plt.subplots(figsize=(10, 7))

    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    except Exception:
        pos = nx.spring_layout(G, seed=42, k=2.0)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                           node_size=600, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color="white",
                            font_size=9, font_weight="bold", ax=ax)

    normal_edges = [(u, v) for u, v in G.edges() if (u, v) not in gargalo_set]
    gargalo_edges = [(u, v) for u, v in G.edges() if (u, v) in gargalo_set]

    nx.draw_networkx_edges(G, pos, edgelist=normal_edges,
                           edge_color="#aaaaaa", width=1.5,
                           arrows=True, arrowsize=15,
                           connectionstyle="arc3,rad=0.1", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=gargalo_edges,
                           edge_color="#c00000", width=3.0,
                           arrows=True, arrowsize=20, style="dashed",
                           connectionstyle="arc3,rad=0.1", ax=ax)

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 font_size=7, ax=ax)

    legenda = [
        mpatches.Patch(color="#1f4e79", label=f"Fonte (s={source})"),
        mpatches.Patch(color="#c00000", label=f"Sumidouro (t={sink})"),
        mpatches.Patch(color="#d9d9d9", label="Roteador intermediario"),
        mpatches.Patch(color="#aaaaaa", label="Enlace normal"),
        mpatches.Patch(color="#c00000", label="Enlace gargalo (100% saturado)"),
    ]
    ax.legend(handles=legenda, loc="upper left", fontsize=8)
    ax.set_title("Topologia da Rede com Gargalos Identificados pelo Corte Minimo")
    ax.axis("off")

    _salvar(fig, nome_arquivo)


def gerar_todas_visualizacoes(todos_resultados: Dict) -> None:
    """Gera todas as tabelas e graficos a partir dos resultados dos experimentos."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    exp1 = todos_resultados["experimento_1_escalabilidade"]
    exp2 = todos_resultados["experimento_2_densidade"]
    exp3 = todos_resultados["experimento_3_gargalos"]

    print("\n" + "=" * 60)
    print("  GERANDO TABELAS")
    print("=" * 60)
    tabela_escalabilidade(exp1)
    tabela_densidade(exp2)
    tabela_gargalos(exp3)

    print("\n" + "=" * 60)
    print("  GERANDO GRAFICOS")
    print("=" * 60)
    grafico_tempo_vs_vertices(exp1)
    grafico_operacoes_vs_vertices(exp1)
    grafico_tempo_vs_densidade(exp2)
    grafico_fluxo_vs_densidade(exp2)

    from network_generator import generate_layered_network
    pr, edges, source, sink = generate_layered_network(3, 4, 50.0, seed=42)
    pr.run(source, sink)
    _, _, gargalos = pr.get_min_cut(source)
    grafico_gargalos_rede(pr, edges, gargalos, pr.n, source, sink)

    print("\n  Todas as visualizacoes geradas com sucesso.")