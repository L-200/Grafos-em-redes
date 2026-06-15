"""
Modulo: network_generator.py
Geracao de redes sinteticas de computadores para experimentos com Push-Relabel.

Gera diferentes topologias de rede para avaliar desempenho e escalabilidade
do algoritmo em redes de diferentes tamanhos e densidades.
"""

import random
import json
from typing import List, Tuple, Optional, Dict
from push_relabel import PushRelabel


def generate_random_network(
    n_vertices: int,
    density: float,
    max_capacity: float,
    seed: Optional[int] = None
) -> Tuple[PushRelabel, List[Tuple], int, int]:
    """
    Gera uma rede de computadores aleatoria com densidade controlada.

    A densidade controla o numero de arestas geradas:
      |E| ~ density * n * (n - 1)

    Garante que existe ao menos um caminho de s=0 ate t=n-1,
    assegurando que o fluxo maximo seja sempre positivo.

    Args:
        n_vertices (int): Numero de roteadores/switches na rede.
        density (float): Fracao de arestas presentes em [0.0, 1.0].
        max_capacity (float): Capacidade maxima de enlace em Mbps/Gbps.
        seed (Optional[int]): Semente para reprodutibilidade.

    Returns:
        Tuple contendo:
          - pr (PushRelabel): Instancia configurada com a rede gerada.
          - edges (List[Tuple]): Lista de (u, v, capacidade).
          - source (int): Vertice fonte (sempre 0).
          - sink (int): Vertice sumidouro (sempre n-1).

    Raises:
        ValueError: Se density nao estiver em (0, 1].
        ValueError: Se n_vertices < 2.
    """
    if not (0 < density <= 1.0):
        raise ValueError(f"Densidade deve estar em (0, 1]. Recebido: {density}")
    if n_vertices < 2:
        raise ValueError("Rede precisa de ao menos 2 vertices.")

    if seed is not None:
        random.seed(seed)

    source = 0
    sink = n_vertices - 1
    pr = PushRelabel(n_vertices)
    edges = []

    # Garante caminho minimo s -> v1 -> v2 -> ... -> t
    # (evita fluxo maximo = 0 por desconexao)
    path = list(range(n_vertices))
    random.shuffle(path[1:-1])
    cap_path = random.uniform(max_capacity * 0.3, max_capacity)
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        pr.add_edge(u, v, cap_path)
        edges.append((u, v, cap_path))

    # Gera arestas adicionais conforme a densidade solicitada
    n_extra = int(density * n_vertices * (n_vertices - 1)) - (n_vertices - 1)
    n_extra = max(0, n_extra)

    all_pairs = [(u, v) for u in range(n_vertices)
                 for v in range(n_vertices) if u != v]
    path_edges = set(zip(path[:-1], path[1:]))
    candidates = [p for p in all_pairs if p not in path_edges]
    random.shuffle(candidates)

    for u, v in candidates[:n_extra]:
        cap = random.uniform(1, max_capacity)
        pr.add_edge(u, v, cap)
        edges.append((u, v, cap))

    return pr, edges, source, sink


def generate_layered_network(
    n_layers: int,
    nodes_per_layer: int,
    max_capacity: float,
    seed: Optional[int] = None
) -> Tuple[PushRelabel, List[Tuple], int, int]:
    """
    Gera uma rede em camadas, topologia comum em data centers e redes corporativas.

    Cada no na camada i conecta-se aleatoriamente a 1..3 nos na camada i+1.
    Um vertice-fonte conecta-se a todos da camada 0 e todos da ultima camada
    conectam-se ao sumidouro.

    Args:
        n_layers (int): Numero de camadas intermediarias.
        nodes_per_layer (int): Nos por camada.
        max_capacity (float): Capacidade maxima de enlace.
        seed (Optional[int]): Semente para reprodutibilidade.

    Returns:
        Tuple contendo:
          - pr (PushRelabel): Instancia configurada.
          - edges (List[Tuple]): Lista de (u, v, capacidade).
          - source (int): Vertice fonte.
          - sink (int): Vertice sumidouro.
    """
    if seed is not None:
        random.seed(seed)

    total = 1 + n_layers * nodes_per_layer + 1
    source = 0
    sink = total - 1

    pr = PushRelabel(total)
    edges = []

    def node_id(layer: int, pos: int) -> int:
        return 1 + layer * nodes_per_layer + pos

    # Fonte -> primeira camada
    for pos in range(nodes_per_layer):
        v = node_id(0, pos)
        cap = random.uniform(max_capacity * 0.5, max_capacity)
        pr.add_edge(source, v, cap)
        edges.append((source, v, cap))

    # Camada i -> camada i+1
    for layer in range(n_layers - 1):
        for pos in range(nodes_per_layer):
            u = node_id(layer, pos)
            n_conn = random.randint(1, min(3, nodes_per_layer))
            targets = random.sample(range(nodes_per_layer), n_conn)
            for t_pos in targets:
                v = node_id(layer + 1, t_pos)
                cap = random.uniform(1, max_capacity)
                pr.add_edge(u, v, cap)
                edges.append((u, v, cap))

    # Ultima camada -> sumidouro
    for pos in range(nodes_per_layer):
        u = node_id(n_layers - 1, pos)
        cap = random.uniform(max_capacity * 0.5, max_capacity)
        pr.add_edge(u, sink, cap)
        edges.append((u, sink, cap))

    return pr, edges, source, sink


def generate_worst_case_network(n: int) -> Tuple[PushRelabel, List[Tuple], int, int]:
    """
    Gera uma instancia de pior caso para algoritmos de caminhos aumentantes.

    Esta topologia e projetada para forcar muitas iteracoes em Ford-Fulkerson,
    mas e tratada eficientemente pelo Push-Relabel, demonstrando sua vantagem.

    Args:
        n (int): Parametro de tamanho (gera 2n vertices).

    Returns:
        Tuple contendo:
          - pr (PushRelabel): Instancia configurada.
          - edges (List[Tuple]): Lista de (u, v, capacidade).
          - source (int): Vertice fonte.
          - sink (int): Vertice sumidouro.
    """
    total = 2 * n
    source = 0
    sink = total - 1
    pr = PushRelabel(total)
    edges = []

    BIG = 1_000_000

    for i in range(n - 1):
        pr.add_edge(i, i + 1, BIG)
        edges.append((i, i + 1, BIG))
        pr.add_edge(n + i, n + i + 1, BIG)
        edges.append((n + i, n + i + 1, BIG))
        pr.add_edge(i, n + i, 1)
        edges.append((i, n + i, 1))
        pr.add_edge(n + i, i, 1)
        edges.append((n + i, i, 1))

    pr.add_edge(n - 1, sink, BIG)
    edges.append((n - 1, sink, BIG))
    pr.add_edge(2 * n - 1, sink, BIG)
    edges.append((2 * n - 1, sink, BIG))

    return pr, edges, source, sink


def network_to_dict(
    edges: List[Tuple],
    n_vertices: int,
    source: int,
    sink: int
) -> Dict:
    """
    Serializa a rede para formato JSON (para reprodutibilidade dos experimentos).

    Args:
        edges (List[Tuple]): Lista de (u, v, capacidade).
        n_vertices (int): Numero total de vertices.
        source (int): Vertice fonte.
        sink (int): Vertice sumidouro.

    Returns:
        Dict serializavel em JSON com a topologia completa da rede.
    """
    return {
        "n_vertices": n_vertices,
        "source": source,
        "sink": sink,
        "n_edges": len(edges),
        "edges": [{"u": u, "v": v, "capacity": cap} for u, v, cap in edges]
    }
