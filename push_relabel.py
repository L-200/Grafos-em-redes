"""
Modulo: push_relabel.py
Implementacao do algoritmo Push-Relabel para o problema do Fluxo Maximo.

Referencia:
    Goldberg, A. V. and Tarjan, R. E. (1988). A new approach to the
    maximum-flow problem. Journal of the ACM (JACM), 35(4):921-940.

Complexidade: O(V^2 * E)
"""

from typing import List, Tuple, Dict, Optional


class PushRelabel:
    """
    Implementacao do algoritmo Push-Relabel para calculo de Fluxo Maximo.

    O grafo e representado internamente como uma lista de adjacencia
    sobre a rede residual, contendo arestas diretas e reversas.

    Atributos:
        n (int): Numero de vertices do grafo.
        graph (List[List[int]]): Lista de adjacencia (indices de arestas).
        edges (List[List]): Lista de arestas [destino, capacidade_residual,
                            indice_reverso].
        h (List[int]): Vetor de alturas (rotulos de distancia).
        e (List[int]): Vetor de excesso de fluxo por vertice.
        n_push (int): Contador de operacoes Push realizadas.
        n_relabel (int): Contador de operacoes Relabel realizadas.
        capacity (Dict): Capacidades originais (u,v) -> c(u,v).
        flow (Dict): Fluxo atual (u,v) -> f(u,v).
        verbose (bool): Se True, imprime o passo a passo das operacoes.
    """

    def __init__(self, n_vertices: int, verbose: bool = False) -> None:
        """
        Inicializa as estruturas de dados do algoritmo.

        Args:
            n_vertices (int): Numero de vertices da rede.
            verbose (bool): Ativa impressao passo a passo.

        Raises:
            ValueError: Se n_vertices for menor que 2.
        """
        if n_vertices < 2:
            raise ValueError("A rede deve ter pelo menos 2 vertices (fonte e sumidouro).")

        self.n = n_vertices
        self.graph: List[List[int]] = [[] for _ in range(n_vertices)]
        # Cada aresta: [destino, capacidade_residual, indice_da_reversa]
        self.edges: List[List] = []
        self.h: List[int] = [0] * n_vertices
        self.e: List[float] = [0.0] * n_vertices
        self.n_push: int = 0
        self.n_relabel: int = 0
        # Armazena capacidades e fluxos originais para consulta externa
        self.capacity: Dict[Tuple[int, int], float] = {}
        self.flow: Dict[Tuple[int, int], float] = {}
        self.verbose = verbose

    def add_edge(self, u: int, v: int, capacity: float) -> None:
        """
        Adiciona uma aresta dirigida (u -> v) com a capacidade informada.

        Adiciona tambem a aresta reversa (v -> u) com capacidade 0,
        necessaria para o funcionamento correto do algoritmo na rede residual.

        Args:
            u (int): Vertice de origem.
            v (int): Vertice de destino.
            capacity (float): Capacidade do enlace (ex: largura de banda em Gbps).

        Raises:
            ValueError: Se os vertices estiverem fora do intervalo valido.
            ValueError: Se a capacidade for negativa.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError(f"Vertices {u} ou {v} fora do intervalo [0, {self.n - 1}].")
        if capacity < 0:
            raise ValueError(f"Capacidade negativa ({capacity}) nao e permitida.")

        # Registra a capacidade original para consulta posterior
        self.capacity[(u, v)] = self.capacity.get((u, v), 0) + capacity
        self.flow[(u, v)] = 0.0

        # Indices das arestas direta e reversa na lista self.edges
        idx_direta = len(self.edges)
        idx_reversa = idx_direta + 1

        # Aresta direta: u -> v com capacidade plena
        self.edges.append([v, capacity, idx_reversa])
        # Aresta reversa: v -> u com capacidade 0 (permite cancelamento de fluxo)
        self.edges.append([u, 0, idx_direta])

        self.graph[u].append(idx_direta)
        self.graph[v].append(idx_reversa)

    def push(self, u: int, edge_idx: int) -> bool:
        """
        Operacao Push: empurra fluxo do vertice ativo u para um vizinho v.

        Ocorre quando:
          - r(u,v) > 0  (ha capacidade residual no enlace)
          - h[u] == h[v] + 1  (u esta exatamente um nivel acima de v)

        O delta transferido e limitado pelo gargalo imediato:
          Delta = min(e[u], r(u,v))

        Args:
            u (int): Vertice ativo com excesso e[u] > 0.
            edge_idx (int): Indice da aresta na lista self.edges.

        Returns:
            bool: True se o Push foi realizado, False caso contrario.
        """
        v, residual, rev_idx = self.edges[edge_idx]

        # Verifica condicoes de push: ha capacidade e gradiente de altura valido
        if residual <= 0 or self.h[u] != self.h[v] + 1:
            return False

        # Delta: nao se pode enviar mais do que o excesso nem mais que a capacidade residual
        delta = min(self.e[u], residual)

        if delta <= 0:
            return False

        # Atualiza capacidade residual direta (diminui) e reversa (aumenta)
        self.edges[edge_idx][1] -= delta   # r(u,v) -= delta
        self.edges[rev_idx][1] += delta    # r(v,u) += delta

        # Atualiza os excessos: u perde, v ganha
        self.e[u] -= delta
        self.e[v] += delta

        # Atualiza fluxo real (para consulta externa e extracao do corte minimo)
        if (u, v) in self.flow:
            self.flow[(u, v)] = self.flow.get((u, v), 0) + delta
        elif (v, u) in self.flow:
            self.flow[(v, u)] = self.flow.get((v, u), 0) - delta

        self.n_push += 1

        if self.verbose:
            print(f"    Push {delta:.1f} Gbps: {u} -> {v}"
                  f"  (excesso: {u}={self.e[u]:.1f}, {v}={self.e[v]:.1f}"
                  f"  |  residual restante: {self.edges[edge_idx][1]:.1f})")

        return True

    def relabel(self, u: int) -> None:
        """
        Operacao Relabel: eleva a altura logica do vertice ativo u.

        Ocorre quando u possui excesso (e[u] > 0) mas nao tem vizinhos
        validos para empurrar fluxo (nenhum v com r(u,v)>0 e h[u]=h[v]+1).

        A nova altura e calculada como:
          h[u] = 1 + min{ h[v] | r(u,v) > 0 }

        O "min sobre vizinhos com capacidade residual" garante que u se
        posicione exatamente um nivel acima do vizinho acessivel mais
        proximo do sumidouro, criando o menor gradiente possivel para
        retomar os pushes sem criar ciclos.

        Args:
            u (int): Vertice ativo sem vizinhos validos para push.
        """
        # Coleta alturas de todos os vizinhos com capacidade residual positiva
        min_h = float('inf')
        for edge_idx in self.graph[u]:
            v, residual, _ = self.edges[edge_idx]
            if residual > 0:
                min_h = min(min_h, self.h[v])

        old_h = self.h[u]
        # Nova altura: exatamente um nivel acima do vizinho acessivel mais baixo
        self.h[u] = 1 + min_h
        self.n_relabel += 1

        if self.verbose:
            print(f"    Relabel do vertice {u}: altura ajustada de {old_h} para {self.h[u]}")

    def initialize_preflow(self, source: int) -> None:
        """
        Inicializa o pre-fluxo antes do laco principal.

        Tres etapas:
          1. Zera todos os fluxos: f(u,v) = 0 para todo (u,v) em E
          2. Define o gradiente de altura: h[source] = |V|, demais h[v] = 0
          3. Satura todos os enlaces diretos da fonte: f(source,v) = c(source,v)
             gerando os primeiros excessos e[v] > 0 que ativam os roteadores.

        Args:
            source (int): Vertice fonte s.
        """
        # Altura maxima para a fonte, base para todos os demais
        self.h = [0] * self.n
        self.h[source] = self.n  # h[s] = |V|

        # Excesso inicial zerado para todos
        self.e = [0.0] * self.n

        # Satura todos os enlaces saindo da fonte.
        # Isso injeta o maximo possivel de dados na rede imediatamente,
        # ativando os roteadores adjacentes para o inicio do laco principal.
        for edge_idx in self.graph[source]:
            v, cap, rev_idx = self.edges[edge_idx]
            if cap > 0:
                # f(source, v) = c(source, v)
                self.edges[edge_idx][1] = 0       # r(source,v) = 0 (saturado)
                self.edges[rev_idx][1] = cap       # r(v,source) = cap (reversa)
                self.e[v] += cap                   # e[v] recebe a capacidade total
                self.e[source] -= cap              # fonte "perde" o que enviou

                # Registra o fluxo inicial
                if (source, v) in self.flow:
                    self.flow[(source, v)] = cap

                if self.verbose:
                    print(f"  Enlace ({source} -> {v}) saturado com {cap:.1f} Gbps"
                          f"  [excesso acumulado em {v}: {self.e[v]:.1f}]")

    def run(self, source: int, sink: int) -> float:
        """
        Executa o algoritmo Push-Relabel e retorna o valor do fluxo maximo.

        O laco principal mantem uma fila de vertices ativos (u != source,
        u != sink, e[u] > 0). Para cada vertice ativo, tenta realizar um
        Push para algum vizinho valido. Se nenhum Push for possivel,
        realiza Relabel para elevar a altura e criar novo gradiente.

        Complexidade: O(V^2 * E)

        Args:
            source (int): Vertice fonte s.
            sink (int): Vertice sumidouro t.

        Returns:
            float: Valor do fluxo maximo |f*| = e[sink] apos convergencia.

        Raises:
            ValueError: Se source ou sink estiverem fora do intervalo valido.
            ValueError: Se source == sink.
        """
        if not (0 <= source < self.n and 0 <= sink < self.n):
            raise ValueError("Fonte ou sumidouro fora do intervalo de vertices.")
        if source == sink:
            raise ValueError("Fonte e sumidouro devem ser vertices distintos.")

        self.n_push = 0
        self.n_relabel = 0

        if self.verbose:
            print(f"\n{'='*52}")
            print(f"  INICIALIZACAO DO PRE-FLUXO")
            print(f"{'='*52}")

        self.initialize_preflow(source)

        if self.verbose:
            print(f"\n  Altura da fonte h[{source}] = {self.h[source]}")
            excessos = {i: self.e[i] for i in range(self.n) if self.e[i] != 0}
            print(f"  Excessos iniciais por vertice: {excessos}")

        # Fila de vertices ativos (excluindo fonte e sumidouro)
        active = [u for u in range(self.n)
                  if u != source and u != sink and self.e[u] > 0]

        step = 0
        while active:
            u = active[0]

            if self.verbose:
                step += 1
                print(f"\n{'-'*52}")
                print(f"  Passo {step}: vertice ativo {u}"
                      f"  (excesso={self.e[u]:.1f}, altura={self.h[u]})")

            pushed = False
            for edge_idx in self.graph[u]:
                if self.e[u] <= 0:
                    break
                if self.push(u, edge_idx):
                    pushed = True
                    # Ativa vizinho se tornou ativo apos receber fluxo
                    v = self.edges[edge_idx][0]
                    if v != source and v != sink and self.e[v] > 0 and v not in active:
                        active.append(v)

            if not pushed:
                # Nenhum push possivel: eleva a altura de u
                self.relabel(u)

            # Remove u da fila se nao tem mais excesso
            if self.e[u] <= 0:
                active.pop(0)

        if self.verbose:
            print(f"\n{'='*52}")
            print(f"  CONVERGENCIA ATINGIDA")
            print(f"  Fluxo maximo encontrado: {self.e[sink]:.1f} Gbps")
            print(f"  Total de operacoes:  Push={self.n_push}  |  Relabel={self.n_relabel}")
            print(f"{'='*52}\n")

        return self.e[sink]

    def get_min_cut(self, source: int) -> Tuple[List[int], List[int], List[Tuple]]:
        """
        Identifica o corte minimo da rede apos a convergencia do algoritmo.

        Metodo baseado no vetor final de alturas h[], conforme descrito em
        Cormen et al. (2009) e Goldberg & Tarjan (1988).

        Apos a convergencia, o vetor h[] particiona V em dois conjuntos:
          S = {v in V | h[v] >= |V|}  ->  sub-rede da fonte
          T = {v in V | h[v] <  |V|}  ->  sub-rede do sumidouro

        Complexidade:
          - O(|V|) para a varredura de particionamento (identificacao de S e T)
          - O(|E|) para a identificacao das arestas gargalo

        Os gargalos sao os enlaces (u,v) com u em S, v em T operando em
        capacidade maxima: f(u,v) = c(u,v), ou seja, saturacao = 100%.

        Args:
            source (int): Vertice fonte s (usado para verificacao de consistencia).

        Returns:
            Tuple contendo:
              - S (List[int]): Vertices da sub-rede da fonte.
              - T (List[int]): Vertices da sub-rede do sumidouro.
              - gargalos (List[Tuple]): Lista de (u, v, capacidade, fluxo, saturacao%).
        """
        # O(|V|): varredura linear para particionar os vertices
        S = [v for v in range(self.n) if self.h[v] >= self.n]
        T = [v for v in range(self.n) if self.h[v] < self.n]

        S_set = set(S)
        T_set = set(T)

        # O(|E|): identifica as arestas gargalo cruzando o corte S -> T
        gargalos = []
        for (u, v), cap in self.capacity.items():
            if u in S_set and v in T_set and cap > 0:
                fluxo = self.flow.get((u, v), 0)
                saturacao = (fluxo / cap * 100) if cap > 0 else 0
                gargalos.append((u, v, cap, fluxo, saturacao))

        return S, T, gargalos

    def get_flow_on_edge(self, u: int, v: int) -> float:
        """
        Retorna o fluxo atual na aresta (u -> v).

        Args:
            u (int): Vertice de origem.
            v (int): Vertice de destino.

        Returns:
            float: Fluxo f(u,v) atual. Retorna 0 se a aresta nao existir.
        """
        return self.flow.get((u, v), 0.0)

    def get_stats(self) -> Dict:
        """
        Retorna estatisticas da ultima execucao do algoritmo.

        Returns:
            Dict com n_push, n_relabel e alturas finais h[].
        """
        return {
            "n_push": self.n_push,
            "n_relabel": self.n_relabel,
            "alturas_finais": self.h.copy()
        }
