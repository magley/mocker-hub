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

    print(sort_by, sort_str)

    pag_start = (page_number - 1) * page_size
    pag_end = pag_start + page_size

    s = Search(index=Event.Index.name)
    if sort_str is not None:
        s = s.sort(sort_str)
    s = s[pag_start:pag_end]


    # q = Q('bool',
    #     must = [
    #         Q("match", text_content="wants"),
    #         #Q('term', log_level=EventLevel.Error.value),
    #         Q('range', date_time={"gte": "2025-07-16T07:08:18"}),
    #     ],
    #     must_not = [
    #         Q("match", text_content="Retrying in 5")
    #     ]
    # )
    
    s = s.query(query)
    response = s.execute()

    return response

####################################################### "API"


def doit(query_string: str, page_num: int, page_size: int, sort_by: str, sort_asc: bool):
    model = meta.model_from_str(query_string)
    query = to_query(model)

    print(query)

    res = search(query, page_num, page_size, sort_by, sort_asc)
    total_hits = res.hits.total.value
    total_pages = math.ceil(total_hits / page_size)

    for hit in res:
        print(f"[{hit.date_time}] [{hit.log_level}] {hit.text_content}")

    print()
    print(f"Page ({page_num} / {total_pages}) [{page_size} items of {total_hits}]")



QUERY = '(log_level == "error" or log_level == "info") and (not text_content ~= "ghuyueyeuyeuriey7327983 2")'
QUERY = 'log_level == "error" or log_level == "info"'

PAGE_NUM = 1
PAGE_SIZE = 5
SORT_BY = 'log_level' # 'date_time', 'log_level', ''
SORT_ASC = True

doit(QUERY, PAGE_NUM, PAGE_SIZE, SORT_BY, SORT_ASC)