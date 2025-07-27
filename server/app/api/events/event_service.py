import logging
import math
import os
from typing import Type
from app.api.events.event_model import Event, EventLevel
from app.api.events.event_dto import EventDTO, LogsResultDTO, LogDTO, LogsResultInfoDTO
from datetime import datetime
from app.api.config.logutil import LOGGER
from elasticsearch_dsl import Document, Text, Date, Keyword, Search, Q, connections
from textx import metamodel_from_str

class EventService:
    def __init__(self):
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

        self.meta = metamodel_from_str(query_grammar)

    def log_read(self, user_id: int | None, entity_type: Type, entity_identifier: int | str):
        """
        Log case when user tries to access an entity.
        Example: `log_read(1, Repository, 'user1/reponame')`
        """
        self.log(EventLevel.Info, f"User {user_id} wants to read {entity_type.__name__} {entity_identifier}")

    def log(self, log_level: EventLevel, text_content: str):
        """Generic log function."""
        LOGGER.log(self._event_level_to_log_level(log_level), text_content)

    def _event_level_to_log_level(self, event_level: EventLevel):
        if event_level == EventLevel.Debug:
            return logging.DEBUG
        elif event_level == EventLevel.Info:
            return logging.INFO
        elif event_level == EventLevel.Warning:
            return logging.WARNING
        elif event_level == EventLevel.Error:
            return logging.ERROR
        else:
            raise ValueError(f"Unknown event level: {event_level}")
        
    def _to_query(self, node):
        """
        Convert TextX node to Elasticsearch-dsl Query object.
        """

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
            return self._to_query(node.expr)

        # 3) NOT expressions
        if getattr(node, 'op', None) == 'not' and hasattr(node, 'right'):
            inner_q = self._to_query(node.right)
            return Q('bool', must_not=[inner_q])

        # 4) AND / OR chains
        if hasattr(node, 'left') and hasattr(node, 'op'):
            q = self._to_query(node.left)
            for operator, right_node in zip(node.op, node.right):
                next_q = self._to_query(right_node)
                if operator == 'and':
                    q = Q('bool', must=[q, next_q])
                else:  # 'or'
                    q = Q('bool', should=[q, next_q])
            return q

        # 5) Atom wrapper
        if hasattr(node, 'atom'):
            return self._to_query(node.atom)

        return None

    def _query(self, query: Q, page_number: int, page_size: int, sort_by: str, sort_ascending: bool):
        """
        Low level query method which interacts with Elasticsearch.
        """

        if page_number < 1:
            page_number = 1
        if page_size < 1:
            page_size = 1

        sort_str = f"{'' if sort_ascending else '-'}{sort_by}"
        if sort_by not in ['date_time', 'log_level']: # Not 'text_content' because text is not optimized for aggregation and sorting.
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

    def query(self, query_string: str, page_num: int, page_size: int, sort_by: str, sort_asc: bool) -> dict:
        """
        High-level method for submitting a query.
        """

        model = self.meta.model_from_str(query_string)
        query = self._to_query(model)

        res = self._query(query, page_num, page_size, sort_by, sort_asc)
        total_hits = res.hits.total.value
        total_pages = math.ceil(total_hits / page_size)

        result_info  =LogsResultInfoDTO(
            page=page_num,
            page_size=page_size,
            total_pages=total_pages,
            total_hits=total_hits
        )
        hits = []
        for hit in res:
            h = LogDTO(
                date_time=hit.date_time, 
                level=hit.log_level, 
                text=hit.text_content
            )
            hits.append(h)

        result = LogsResultDTO(hits=hits, info=result_info)
        return result


def get_event_service() -> EventService:
    return EventService()