#!/usr/bin/env python
#-*-coding: utf8-*-
# vim: set fenc=utf8:
# vim: set tw=100 ts=4 sts=4 sw=4 ai ci:
#
# @description:
# @author: xiaozongyang

import sys
import re
from itertools import combinations
from functools import reduce

import networkx as nx
import matplotlib.pyplot as plt

class Relation:
    equality   = 0
    derivative = 1


#def split_requests(filename):

def add_nodes(G, schema_list):
    if not isinstance(G, nx.DiGraph):
        raise TypeError('type {} required but {} got !'.format(nx.Graph, type(G)))
    for s in schema_list:
        G.add_node(s)


def add_edge(G, f, t):
    if not isinstance(G, nx.DiGraph):
        raise TypeError('parameter G type {} required but {} got !'.format(nx.Graph, type(G)))
    if not isinstance(f, str):
        raise TypeError('parameter f type {} required buf {} got !'.format(str, type(f)))
    if not isinstance(t, str):
        raise TypeError('parameter t type {} required buf {} got !'.format(str, type(t)))
    #print('add edge from {} to {}', f, t)
    if G.has_edge(f, t):
        G[f][t]['weight'] += 1
    else:
        G.add_edge(f, t)
        G[f][t]['weight'] = 1

def add_edges(G, log_seq, whitelist={}, blacklist={}, window_size=5):

    for (i, seq) in enumerate(log_seq):
        for pre in seq:
            for j in range(i + 1, len(log_seq)):
                for post in log_seq[j]:

                    for f in pre.split(','):
                        df, tf, cf = f.split('#')
                        for t in post.split(','):
                            if '{}-{}'.format(f, t) in whitelist:
                                add_edge(G, f, t)
                                continue
                            if '{}-{}'.format(f, t) in blacklist:
                                continue

                            #print(t)
                            dt, tt, ct = t.split('#')


                            if '{}-{}'.format(cf, ct) in blacklist:
                                continue
                            if df == dt and tf == tt:
                                continue

                            if '{}_{}'.format(tf, cf) == ct:
                                add_edge(G, f, t)
                            if '{}_{}'.format(tt, ct) == cf:
                                add_edge(G, t, f)
                            if cf == ct:
                                add_edge(G, t, f)


def refine(G):
    G.remove_edges_from(
        [
            (f, t) for (f, t) in G.edges \
                if G.has_edge(t, f) and G[f][t]['weight'] < G[t][f]['weight']
        ]
    )



def generate_log_seq(logfile, window_size=5):
    with open(logfile) as handle:
        logs = [line.strip().split(';') for line in handle]
    for i in range(0, len(logs) - window_size):
        yield logs[i: i + window_size]


def draw(G, savepath):
    #pos = nx.spring_layout(G)
    pos = nx.nx_agraph.graphviz_layout(G)
    nx.draw(G, pos, with_labels=True)


    #edge_labels = nx.get_edge_attributes(G, 'weight')
    #nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    plt.savefig(savepath)
    plt.clf()


def min_cut(G, factor=0.5):
    # add source and sink
    source = 'source'
    sink = 'sink'
    for (f, t) in G.edges:
        G[f][t]['capacity'] = float(G[f][t]['weight'])

    G.add_node(source)
    G.add_node(sink)

    for n in G.nodes:
        if G.in_degree(n) == 0:
            G.add_edge(source, n, capacity=float("inf"))
        if G.out_degree(n) == 0:
            G.add_edge(n, sink, capacity=float("inf"))

    cut_value, partition = nx.minimum_cut(G, source, sink)
    reachable, non_reachable = partition

    G.remove_node(source)
    G.remove_node(sink)


    reachable.remove(source)
    Gr = nx.DiGraph()
    Gr.add_nodes_from(reachable)
    for r in reachable:
        Gr.add_edges_from(
            [(f,t) for (f, t) in G.edges(r) if t in reachable]
        )


    non_reachable.remove(sink)
    Gn = nx.DiGraph()
    Gn.add_nodes_from(non_reachable)
    for n in non_reachable:
        Gn.add_edges_from(
            [(f, t) for (f, t) in G.edges(n) if t in non_reachable]
        )

    return (Gr, Gn)


def build_graph(
     schema_list,
     log_sequence,
     whitelist={},
     blacklist={},
     window_size=5):
    G = nx.DiGraph()

    for seq in log_sequence:
        add_edges(G, seq, whitelist, blacklist, window_size)

    #refine(G)

    return G


def evaluate(expected_edges, actual_edges):
    total = len(expected_edges)

    # recall = ...
    found = len(actual_edges)
    if found == 0:
        return (0.0, 0.0, 0.0)
    recall = 1.0 if found >= total else float(found) / total

    # precision = ...
    correct = len([(f, t) for (f, t) in actual_edges if (f, t) in expected_edges])
    precision = float(correct) / found

    f1 = (2 * precision * recall) / (precision + recall)
    return (round(precision, 4), round(recall,4), round(f1, 4))


def expected_graph():
    G = nx.DiGraph()

    G.add_edge('User#user#id', 'Sale#comment#from_user_id')
    G.add_edge('User#user#id', 'Sale#comment#to_user_id')
    G.add_edge('User#user#id', 'User#user_bahavior#user_id')
    G.add_edge('User#user#id', 'Delivery#express#user_id')

    G.add_edge('Sale#store#id', 'Sale#commodity#store_id')

    G.add_edge('Sale#order#id', 'Sale#payment#order_id')
    G.add_edge('Sale#order#id', 'Delivery#express#order_id')

    G.add_edge('Sale#commodity#id', 'Sale#commodity_detail#commodity_id')
    G.add_edge('Sale#commodity#id', 'Sale#order#commodity_id')
    G.add_edge('Sale#commodity#id', 'Sale#comment#commodity_id')

    G.add_edge('Sale#image#id', 'Sale#commodity_detail#image_id')

    G.add_edge('Sale#comment#id', 'Sale#commodity#comment_id')


    return G

def main():
    #logfile = 'development.log'
    logfile = 'data/generated-log'
    schema_file = 'data/schema-list'
    with open(schema_file) as handle:
        schema_list = [line.strip() for line in handle]

    #segments = split_requests(logfile)
    log_segments = list(generate_log_seq(logfile))

    whitelist = {
        'User#user#id-Sale#comment#from_user_id',
        'User#user#id-Sale#comment#to_user_id',
    }
    blacklist = {
        'id-id',
        'user_id-user_id'
    }

    #G = nx.DiGraph()
    ##add_nodes(G, schema_list)
    #for seq in generate_log_seq(logfile):
    #    add_edges(G, seq, whitelist, blacklist)

    #refine(G)
    expected_edges = expected_graph().edges

    window_size_list = [3, 5, 7, 9]
    whitelists = [{}, whitelist]
    blacklists = [{}, blacklist]

    x = []
    y = []

    for ws in window_size_list:
        for wl in whitelists:
            for bl in blacklists:
                G = build_graph(schema_list, log_segments, wl, bl, ws)
                (precision, recall, f1) = evaluate(expected_edges, G.edges)
                print('wl = {}, bl = {}, ws = {}, precision = {} recall = {} f1 = {}'.format(
                    wl, bl, ws, precision, recall, f1
                ))
                # print(evaluate(expected_edges, G.edges))




    draw(G, 'graph-before.png')

    # minimum cut
    # (Gr, Gn) = min_cut(G)

    # draw(Gr, 'graph-sub-r.png')
    # draw(Gn, 'graph-sub-n.png')


if __name__ == '__main__':
    main()
