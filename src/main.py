import argparse
from typing import Set, Any

import networkx as nx
from gensim.models import Word2Vec

from src.GraphWalks import Graph


def parse_args():
    """
    Parses the node2vec and fairwalk arguments.
    """
    parser = argparse.ArgumentParser(description="Run node2vec.")

    parser.add_argument('--input', nargs='?', default='../graph/twitter.edgelist',
                        help='Input graph path')

    parser.add_argument('--node-labels', dest='node_labels', default='../graph/twitter.groups',
                        help='Input graph communities')

    parser.add_argument('--output', nargs='?', default='../emb/twitter.emb',
                        help='Embeddings path')

    parser.add_argument('--dimensions', type=int, default=128,
                        help='Number of dimensions. Default is 128.')

    parser.add_argument('--walk-length', type=int, default=80,
                        help='Length of walk per source. Default is 80.')

    parser.add_argument('--num-walks', type=int, default=10,
                        help='Number of walks per source. Default is 10.')

    parser.add_argument('--window-size', type=int, default=10,
                        help='Context size for optimization. Default is 10.')

    parser.add_argument('--iter', default=1, type=int,
                        help='Number of epochs in SGD')

    parser.add_argument('--workers', type=int, default=8,
                        help='Number of parallel workers. Default is 8.')

    parser.add_argument('--p', type=float, default=1,
                        help='Return hyperparameter. Default is 1.')

    parser.add_argument('--q', type=float, default=1,
                        help='Inout hyperparameter. Default is 1.')

    parser.add_argument('--fairwalk', type=bool, default=True,
                        help='Fair Walk. Default is False.')

    parser.add_argument('--weighted', dest='weighted', action='store_true',
                        help='Boolean specifying (un)weighted. Default is unweighted.')
    parser.add_argument('--unweighted', dest='unweighted', action='store_false')
    parser.set_defaults(weighted=False)

    parser.add_argument('--directed', dest='directed', action='store_true',
                        help='Graph is (un)directed. Default is undirected.')
    parser.add_argument('--undirected', dest='undirected', action='store_false')
    parser.set_defaults(directed=False)

    return parser.parse_args()


def read_graph():
    """
    Reads the input network in networkx.
    """
    if args.weighted:
        G = nx.read_edgelist(args.input, nodetype=int, data=(('weight', float),), create_using=nx.DiGraph())
    else:
        G = nx.read_edgelist(args.input, nodetype=int, create_using=nx.DiGraph())
        for edge in G.edges():
            G[edge[0]][edge[1]]['weight'] = 1

    groups: Set[Any] = set()
    if args.node_labels:
        file = open(args.node_labels, 'r')
        lines = file.readlines()
        for line in lines:
            id_, group = line.split()
            id_ = int(id_)
            group = int(group)
            G.nodes[id_]['group'] = group
            groups.add(group)

    if not args.directed:
        G = G.to_undirected()

    return G, list(groups)


def learn_embeddings(walks):
    """
    Learn embeddings by optimizing the Skipgram objective using SGD.
    """
    model = Word2Vec(walks, vector_size=args.dimensions, window=args.window_size, min_count=0, sg=1, workers=args.workers,
                     epochs=args.iter)

    model.wv.save_word2vec_format(args.output)

    return


def main(args):
    """
    Pipeline for representational learning for all nodes in a graph.
    """
    nx_G, groups = read_graph()
    G = Graph(nx_G, args.directed, args.p, args.q, groups)
    from gensim.test.utils import common_texts
    print(type(common_texts))
    print(common_texts)

    # enable fair walk
    if args.fairwalk:
        if groups is None or len(groups) < 2:
            raise Exception("Groups are configured wrong")
        walks = G.simulate_fair_walks(args.num_walks, args.walk_length)
    else:
        G.preprocess_transition_probs()
        walks = G.simulate_walks(args.num_walks, args.walk_length)
    # construct embeddings
    learn_embeddings(walks)


if __name__ == "__main__":
    args = parse_args()
    main(args)
