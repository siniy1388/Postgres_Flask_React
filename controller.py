"""rir_exchange module."""

from flask import (Blueprint)
from webargs import fields
from ..lpumodel.rir_send import RirSend
from app.utilsdirectories.resultrest import (get_data, wargs_uuid, wargs_str, wargs_int)
from typing import Dict

Args_Request = Dict[str, any]

rir_send = Blueprint('rir_send', __name__)


# Запись направления в РИР
@get_data(rir_send, '/web_appoint', ['post'], None, {
    'cdnap': fields.UUID(required=True, error_messages=wargs_uuid),
})
def web_appoint(args):
    """Запрос списка широкого."""
    code, res = RirSend.web_appoint(args)
    return code, res


# Получить Страховую пациента
@get_data(rir_send, '/test_strah', ['post'], None, {
    'cdpac': fields.UUID(required=True, error_messages=wargs_uuid),
})
def test_strah(args):
    """Запрос списка широкого."""
    res = RirSend.get_info_str_pac(args)
    return res


# Получить инфу по направлению
@get_data(rir_send, '/get_appoint_info', ['post'], None, {
    'cdnap': fields.UUID(required=True, error_messages=wargs_uuid),
})
def get_appoint_info(args):
    """Запрос списка широкого."""
    res = RirSend.get_appoint_info(args)
    return res


# Получить инфу по госпитализации
@get_data(rir_send, '/get_hospital', ['post'], None, {
    'ruid': fields.String(required=True, error_messages=wargs_str),
})
def get_hospital(args):
    """Запрос списка широкого."""
    res = RirSend.get_hospital(args)
    return res


# Запись направления в РИР
@get_data(rir_send, '/web_appoint_cancel', ['post'], None, {
    'cdnap': fields.UUID(required=True, error_messages=wargs_uuid),
    'ruid': fields.String(required=True, error_messages=wargs_str),
    'org': fields.Integer(required=True, error_messages=wargs_int),
    'code_pr': fields.Integer(required=True, error_messages=wargs_int),

})
def web_appoint_cancel(args):
    """Запрос списка широкого."""
    res = RirSend.web_appoint_cancel(args)
    return res


# Запись направления в РИР
@get_data(rir_send, '/web_appoint_corr', ['post'], None, {
    'cdnap': fields.UUID(required=True, error_messages=wargs_uuid),
})
def web_appoint_corr(args):
    """Запрос списка широкого."""
    res = RirSend.web_appoint_corr(args)
    return res


# Запись направления в РИР или корректировка
@get_data(rir_send, '/web_appoint_cap', ['post'], None, {
    'cdnap': fields.UUID(required=True, error_messages=wargs_uuid),
})
def web_appoint_cap(args):
    """Запись направления в РИР или корректировка ."""
    req, res = RirSend.web_appoint_cap(args)
    return req, res
