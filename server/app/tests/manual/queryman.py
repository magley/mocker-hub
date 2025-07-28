"""
This is a utility script for running ElasticSearch queries without starting the entire server.

How to use:

`python ./queryman.py`

You need flask, elasticsearch_dsl amd textX

This script and any of its functions should NOT be used by the program, but I'm keeping it here for now.
"""

import os
from typing import List
from enum import Enum
import math
from elasticsearch_dsl import Document, Text, Date, Keyword, Search, Q, connections
from textx import metamodel_from_str

####################################################### MODEL

class EventLevel(Enum):
    Debug = "debug"
    Info = "info"
    Warning = "warning"
    Error = "error"

class Event(Document):
    date_time = Date()
    log_level = Keyword()
    text_content = Text()

    class Index:
        name = 'events'

####################################################### GRAMMAR

query_grammar = r'''
Model: expr ;

expr: or_expr ;

or_expr:
    left=and_expr
    ( op='or' right=and_expr )*
;

and_expr:
    left=not_expr
    ( op='and' right=not_expr )*
;

not_expr:
    op='not' right=not_expr
  | atom=atom
;

atom:
    condition
  | '(' expr ')'
;

condition:
    field=ID op=Op value=STRING
;

Op: '==' | '!=' | '~=' | '~~=' | '>=' | '>' | '<=' | '<';
'''

meta = metamodel_from_str(query_grammar)

def to_query(node):
    # 1) Leaf conditions
    if hasattr(node, 'op') and hasattr(node, 'field'):
        field, op, val = node.field, node.op, node.value.strip('"')
        if op == '==':
            return Q('term', **{field: val})
        if op == '!=':
            return Q('bool', must_not=[Q('term', **{field: val})])
        if op == '~=':
            return Q('match', **{field: val})
        if op == '~~=':
            return Q('match_phrase', **{field: val})
        if op in ['>', '<', '>=', '<=']:
            op_map = {
                '>': 'gt', 
                '<': 'lt', 
                '>=': 'gte', 
                '<=': 'lte'
            }
            return Q('range', **{field: {op_map[op]: val}})

    # 2) Parenthesized subexpression
    if hasattr(node, 'expr'):
        return to_query(node.expr)

    # 3) NOT expressions
    if getattr(node, 'op', None) == 'not' and hasattr(node, 'right'):
        inner_q = to_query(node.right)
        return Q('bool', must_not=[inner_q])

    # 4) AND / OR chains
    if hasattr(node, 'left') and hasattr(node, 'op'):
        q = to_query(node.left)
        for operator, right_node in zip(node.op, node.right):
            next_q = to_query(right_node)
            if operator == 'and':
                q = Q('bool', must=[q, next_q])
            else:  # 'or'
                q = Q('bool', should=[q, next_q])
        return q

    # 5) Atom wrapper
    if hasattr(node, 'atom'):
        return to_query(node.atom)

    return None

####################################################### QUERY BUILDER

def search(query: Q, page_number: int, page_size: int, sort_by: str, sort_ascending: bool) -> List:
    hostname = os.getenv("ES_HOST", "localhost:9200")
    connections.create_connection(hosts=[f"http://{hostname}"])

    if page_number < 1:
        page_number = 1
    if page_size < 1:
        page_size = 1

    sort_str = f"{'' if sort_ascending else '-'}{sort_by}"
    if sort_by not in ['date_time', 'log_level']: # But not 'text_content' because text is not optimized for aggregation and sorting.
        sort_str = None

    pag_start = (page_number - 1) * page_size
    pag_end = pag_start + page_size

    s = Search(index=Event.Index.name)
    if sort_str is not None:
        s = s.sort(sort_str)
    s = s[pag_start:pag_end]

    s = s.query(query)
    response = s.execute()

    return response

####################################################### "API"


def doit(query_string: str, page_num: int, page_size: int, sort_by: str, sort_asc: bool) -> dict:
    model = meta.model_from_str(query_string)
    query = to_query(model)

    res = search(query, page_num, page_size, sort_by, sort_asc)
    total_hits = res.hits.total.value
    total_pages = math.ceil(total_hits / page_size)

    result = {}
    result["info"] = {
        "page": page_num,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_hits": total_hits,
    }
    result["hits"] = []
    for hit in res:
        h = {
            "date_time": hit.date_time,
            "level": hit.log_level,
            "text": hit.text_content
        }
        result["hits"].append(h)
    return result

def printme(result: dict):
    for hit in result["hits"]:
        print(f"[{hit['date_time']}] [{hit['level']}] {hit['text']}")

    print()
    print(f"Page ({result['info']['page']} / {result['info']['total_pages']}) [{result['info']['page_size']} items of {result['info']['total_hits']}")


def local():     
    QUERY = '(log_level == "error" or log_level == "info") and (not text_content ~= "ghuyueyeuyeuriey7327983 2")'
    QUERY = 'log_level == "error" or log_level == "info"'

    PAGE_NUM = 1
    PAGE_SIZE = 5
    SORT_BY = 'log_level' # 'date_time', 'log_level', ''
    SORT_ASC = True

    res = doit(QUERY, PAGE_NUM, PAGE_SIZE, SORT_BY, SORT_ASC)
    printme(res)


#################### Temp flask server.

from flask import Flask, request, jsonify
from operator import itemgetter
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/search_logs', methods=['GET'])
def search_logs():
    # Get query parameters
    query = request.args.get('query', '', type=str)
    page_number = request.args.get('page_number', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    sort_by = request.args.get('sort_by', 'text_content', type=str)
    sort_ascending = request.args.get('sort_ascending', 'true').lower() == 'true'

    res = doit(query, page_number, page_size, sort_by, sort_ascending)
    printme(res)

    return jsonify(res)

if __name__ == '__main__':
    app.run(host='localhost', port=8068)