# Maximização de Throughput em Redes de Computadores

Este repositório contém a implementação nativa em Python 3 do algoritmo **Push-Relabel** para a resolução do problema clássico de Fluxo Máximo, aplicado à engenharia de tráfego em redes de computadores. 

O projeto foi desenvolvido como Trabalho Final da disciplina de Introdução à Teoria dos Grafos (ICC041 / PPGINF539) do Instituto de Computação da Universidade Federal do Amazonas (UFAM).

## Estrutura do Projeto

A arquitetura do código foi modularizada para separar a lógica matemática da instrumentação de testes:

* `push_relabel.py`: Motor central do algoritmo, contendo as lógicas de inicialização de pré-fluxo e as operações locais (*Push* e *Relabel*), operando sobre listas de adjacência.
* `network_generator.py`: Gerador sintético de grafos capaz de instanciar topologias de redes aleatórias, redes em camadas (*data centers*) e redes de pior caso.
* `experiments.py`: Bateria completa de simulações para extração de métricas de escalabilidade, impacto de densidade e identificação de corte mínimo (gargalos físicos).
* `visualizations.py`: Módulo de automação para exportação de tabelas `.csv`/`.tex` e renderização de gráficos estruturais e de desempenho.
* `main.py`: Ponto de entrada que executa uma demonstração didática e dispara todos os experimentos.

## Requisitos e Execução

A bateria de testes foi homologada em ambiente **Ubuntu Linux**. Para executar localmente, certifique-se de ter o Python 3 instalado.

1. Clone o repositório:

        git clone https://github.com/L-200/Grafos-em-redes
        cd Grafos-em-redes/src

2. Instale as bibliotecas necessárias para a modelagem de rede e geração de gráficos:

        pip install networkx matplotlib pandas numpy

3. Inicie a execução:

        python3 main.py

Ao final da execução, os arquivos `.pdf`, `.png` e `.tex` serão gerados automaticamente no diretório /data com todas as visualizações do fluxo e resultados tabelados.