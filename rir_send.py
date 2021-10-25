"""Модуль отправки документов в РИР."""
import datetime

import requests
from sqlalchemy import bindparam
from sqlalchemy import (
    Date,
    Integer,
    String,
)
import xmltodict

from app.utilsdirectories.dbutils import get_scalar, get_dict, exec_command_autocomit
from app.utilsdirectories.uuid import UUIDType
from flask_jwt_extended import (current_user)

endpoint = 'http://192.168.0.253/fomsinsurance/webservices/servicerir.asmx'
headers = {'Content-Type': 'application/soap+xml; charset=utf-8', }
t_body = """<?xml version="1.0" encoding="utf-8"?>
                <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Body>
                <replace_web_f xmlns="http://tempuri.org/">
                   replace_in
                </replace_web_f>
                </soap12:Body>
                </soap12:Envelope>"""


class RirSend:
    """Модуль отправки документов в РИР."""

    @staticmethod
    def get_lpu():
        """Получаем Утв Код ЛПУ."""
        res = get_dict("""
                            select s.cdlpu_u, s.reestr_nom from sllpu s
                            where s.cdlpu = :cdlpu
                            and s.cduser = :cduser
                           """, [
            bindparam('cduser', type_=UUIDType, value=current_user.sessiondata['cduser']),
            bindparam('cdlpu', type_=UUIDType, value=current_user.sessiondata['cdlpu']),
        ])
        return res

    @staticmethod
    def write_result(wres: dict):
        """
        Запись результата обмена с РИР.

        Пишем в xmlrir_263
        """
        if_err = wres['vozvrat']
        oshib = 0
        if if_err != '0':
            oshib = wres['vozvrat']
            # oshib = t1[wres['vozvrat'].index('<OSHIB>') + 7:wres['OSHIB'].index('</COMMENT>')]
        # Отправка завершилась удачно - 1
        vozvrat = 2 if int(oshib) > 0 else 1
        tres = get_dict("""select DOCZAG.CDREG, doclpu.cddoc
                from public.docnapr
                left JOIN public.DOCZAG on DOCNAPR.CDREG = DOCZAG.CDREG
                INNER JOIN public.DOCLPU on DOCZAG.CDREG = DOCLPU.CDREG
                where docnapr.cdnap = :cdnap
                                      """, [
            bindparam('cdnap', type_=UUIDType, value=wres['cdnap']),
        ])
        respdate = datetime.datetime.now()
        is_first = get_scalar("""select count(*)
                from public.xmlrir_263
                where cdreg = :cdreg
                and cddoc = :cddoc
                                      """, [
            bindparam('cdreg', type_=UUIDType, value=tres['cdreg']),
            bindparam('cddoc', type_=UUIDType, value=tres['cddoc']),
        ])
        if is_first == 0:
            exec_command_autocomit("""insert into public.xmlrir_263
                    (cdreg, cddoc, type_, vozvrat, insdate, xmlresp, respdate,
                    cdlpuparent, change_date, cduser, cduserizm)
                    values
                    (:cdreg, :cddoc, :type_, :vozvrat, :insdate, :xmlresp, :respdate,
                    :cdlpuparent, :change_date, :cduser, :cduserizm)
                              """, [
                bindparam('cdreg', type_=UUIDType, value=tres['cdreg']),
                bindparam('cddoc', type_=UUIDType, value=tres['cddoc']),
                bindparam('type_', type_=Integer, value=wres['type_']),
                bindparam('vozvrat', type_=Integer, value=vozvrat),
                bindparam('insdate', type_=Date, value=wres['insdate']),
                bindparam('xmlresp', type_=String, value=wres['xmlresp']),
                bindparam('respdate', type_=Date, value=respdate),
                bindparam('change_date', type_=Date, value=respdate),
                bindparam('cduser', type_=UUIDType, value=current_user.sessiondata['cduser']),
                bindparam('cduserizm', type_=UUIDType, value=current_user.sessiondata['cduser']),
                bindparam('cdlpuparent', type_=UUIDType, value=current_user.sessiondata['cdlpuparent']),
            ])
        else:
            exec_command_autocomit("""update public.xmlrir_263 set
                                vozvrat = :vozvrat,
                                insdate = :insdate,
                                xmlresp = :xmlresp,
                                respdate = :respdate,
                                change_date = :change_date,
                                cduserizm = :cduserizm
                                where
                                cdreg = :cdreg and
                                cddoc = :cddoc and
                                type_ = :type_ and
                                cdlpuparent = :cdlpuparent
                                          """, [
                bindparam('cdreg', type_=UUIDType, value=tres['cdreg']),
                bindparam('cddoc', type_=UUIDType, value=tres['cddoc']),
                bindparam('type_', type_=Integer, value=wres['type_']),
                bindparam('vozvrat', type_=Integer, value=vozvrat),
                bindparam('insdate', type_=Date, value=wres['insdate']),
                bindparam('xmlresp', type_=String, value=wres['xmlresp']),
                bindparam('respdate', type_=Date, value=respdate),
                bindparam('change_date', type_=Date, value=respdate),
                bindparam('cduserizm', type_=UUIDType, value=current_user.sessiondata['cduser']),
                bindparam('cdlpuparent', type_=UUIDType, value=current_user.sessiondata['cdlpuparent']),
            ])
            # Закрываем документ на редактирование
            if vozvrat == 1:
                exec_command_autocomit("""update public.doclpu set
                                                isdone = 1
                                                where
                                                cddoc = :cddoc and
                                                cdlpuparent = :cdlpuparent
                                                          """, [
                    bindparam('cddoc', type_=UUIDType, value=tres['cddoc']),
                    bindparam('cdlpuparent', type_=UUIDType, value=current_user.sessiondata['cdlpuparent']),
                ])

    @staticmethod
    def get_new_ruid():
        """Получаем номер RUID из РИР Для записи направления."""
        user = "lpu_a"
        paswd = "lpu_a"
        v_cdlpu = '2560101'  # rir_send.get_lpu()
        v_in = """<_in>
                        <LOGIN>%(u)s</LOGIN>
                        <PASSWORD>%(p)s</PASSWORD>
                        <CDLPU>%(l)s</CDLPU>
                   </_in>""" % {'u': user, 'p': paswd, 'l': v_cdlpu}
        body = t_body.replace('replace_web_f', 'WEB_Get_New_RUID').replace('replace_in', v_in)

        try:
            result = requests.post(endpoint, headers=headers, data=body.encode('utf-8')).text
        except Exception as err:
            result = err
        start_p = result.find('<RUID_OUT>')
        end_p = result.find('</RUID_OUT>')
        return result[start_p + 10:end_p]

    @staticmethod
    def get_ruid_from_db(args):
        """Получаем номер RUID из БД по cdnap."""
        res = get_scalar("""
                            select nomnapr from public.docnapr
                            where cdnap = :cdnap
                            and cdlpuparent = :cdlpuparent
                                   """, [
            bindparam('cdnap', type_=UUIDType, value=args['cdnap']),
            bindparam('cdlpuparent', type_=UUIDType, value=args['cdlpuparent']),
        ])
        return res

    @staticmethod
    def web_appoint(args) -> str:
        """Собираем строку для отправки в в РИР."""
        v_cddoc = args['cdnap']  # '84501391-ca56-411f-a5fa-47bcdc5a14f3'
        user = "lpu_a"
        paswd = "lpu_a"
        version = "1.7"
        # v_ruid = RirSend.get_new_ruid()
        rec = get_scalar("""
                     select em_rir_make_xml(:cduser, :cddoc);
                   """, [
            bindparam('cduser', type_=UUIDType, value=current_user.sessiondata['cduser']),
            bindparam('cddoc', type_=UUIDType, value=v_cddoc),
        ])

        trec = rec.replace('<', '&lt;').replace('>', '&gt;').replace('b\'', '', 1)
        date_send = datetime.datetime.now()
        v_in = """<_in>
                             <LOGIN>%(u)s</LOGIN>
                             <PASSWORD>%(p)s</PASSWORD>
                             <VERS>%(v)s</VERS>
                             <ZAP>%(r)s</ZAP>
                             <COMMENT>No Comment</COMMENT>
                           </_in>""" % {'u': user, 'p': paswd, 'v': version, 'r': trec}
        body = t_body.replace('replace_web_f', 'WEB_Appoint').replace('replace_in', v_in)
        try:
            rest = requests.post(endpoint, headers=headers, data=body.encode('utf-8'))
            req = rest.status_code
            result = rest.text
            RUID_OUT = result[result.index('<RUID_OUT>') + 10:result.index('</RUID_OUT>')] if '</RUID_OUT>' in result else ''
            STR_OUT = result[result.index('<STR_OUT>') + 9:result.index('</STR_OUT>')] if '</STR_OUT>' in result else ''
            CNT_OSHIB = result[result.index('<CNT_OSHIB>') + 11:result.index(
                '</CNT_OSHIB>')] if '</CNT_OSHIB>' in result else ''
            PR = result[result.index('<PR>') + 4:result.index('</PR>')].replace('&lt;', '<').replace('&gt;',
                                                                                                     '>') if '</PR>' in result else ''
            t_dict = xmltodict.parse(PR)
            res = {
                'RUID_OUT': RUID_OUT,
                'STR_OUT': STR_OUT,
                'CNT_OSHIB': CNT_OSHIB,
                'PR': t_dict
            }
            # Запись в таблицу public.xmlrir_263

            wres = {
                'cdnap': v_cddoc,
                'type_': 1,
                'vozvrat': CNT_OSHIB,
                'insdate': date_send,
                'xmlresp': PR,
            }
            RirSend.write_result(wres)
        except Exception as err:
            res = err
        return req, res

    @staticmethod
    def get_info_str_pac(args):
        """
        Функция определения страховой принадлежности пациента.

        Предназначена для получения сведений о ЗЛ
        """
        user = "lpu_a"
        paswd = "lpu_a"
        version = "1.7"
        rec = get_scalar("""
                             select em_rir_get_info_str(:cduser, :cdpac);
                           """, [
            bindparam('cduser', type_=UUIDType, value=current_user.sessiondata['cduser']),
            bindparam('cdpac', type_=UUIDType, value=args['cdpac']),
        ])
        trec = rec.replace('<', '&lt;').replace('>', '&gt;').replace('b\'', '', 1)
        v_in = """<_in>
                   <LOGIN>%(u)s</LOGIN>
                   <PASSWORD>%(p)s</PASSWORD>
                   <VERS>%(v)s</VERS>
                   <ZL>%(r)s</ZL>
                  </_in>""" % {'u': user, 'p': paswd, 'v': version, 'r': trec}
        body = t_body.replace('replace_web_f', 'WEB_Get_Info_ZL_RS_ERZ').replace('replace_in', v_in)
        try:
            rest = requests.post(endpoint, headers=headers, data=body.encode('utf-8'))
            req = rest.status_code
            res = rest.text
            ID_ZL_OUT = res[res.index('<ID_ZL_OUT>') + 11:res.index('</ID_ZL_OUT >')] if '</ID_ZL_OUT >' in res else ''
            STR_OUT = res[res.index('<STR_OUT>') + 9:res.index('</STR_OUT>')] if '</STR_OUT>' in res else ''
            ZL = res[res.index('<ZL>') + 4:res.index('</ZL>')] if '</ZL>' in res else ''
            resq = {
                'ID_ZL_OUT ': ID_ZL_OUT,
                'STR_OUT': STR_OUT,
                "ZL": ZL,
            }
        except Exception as err:
            resq = err
        return req, resq

    @staticmethod
    def get_appoint_info(args):
        """Функция для поиска сведений о конкретном направлении на госпитализацию."""
        truid = RirSend.get_ruid_from_db(args)
        user = "lpu_a"
        paswd = "lpu_a"
        v_in = """<_in>
                           <LOGIN>%(u)s</LOGIN>
                           <PASSWORD>%(p)s</PASSWORD>
                           <RUID>%(r)s</RUID>
                          </_in>""" % {'u': user, 'p': paswd, 'r': truid}
        body = t_body.replace('replace_web_f', 'WEB_Get_Appoint').replace('replace_in', v_in)
        try:
            rest = requests.post(endpoint, headers=headers, data=body.encode('utf-8'))
            req = rest.status_code
            res = rest.text
            ID_ZL_OUT = res[res.index('<ID_ZL_OUT>') + 11:res.index('</ID_ZL_OUT >')] if '</ID_ZL_OUT >' in res else ''
            STR_OUT = res[res.index('<STR_OUT>') + 9:res.index('</STR_OUT>')] if '</STR_OUT>' in res else ''
            ZAP = res[res.index('<ZAP>') + 4:res.index('</ZAP>')] if '</ZAP>' in res else ''
            resq = {
                'ID_ZL_OUT ': ID_ZL_OUT,
                'STR_OUT': STR_OUT,
                "ZAP": ZAP,
            }
        except Exception as err:
            resq = err
        return req, resq

    @staticmethod
    def get_hospital(args):
        """Функция для поиска сведений о конкретной госпитализации."""
        user = "lpu_a"
        paswd = "lpu_a"
        truid = args['ruid']
        v_in = """<_in>
                    <LOGIN>%(u)s</LOGIN>
                    <PASSWORD>%(p)s</PASSWORD>
                    <RUID>%(r)s</RUID>
                  </_in>""" % {'u': user, 'p': paswd, 'r': truid}
        body = t_body.replace('replace_web_f', 'WEB_Get_Hospital').replace('replace_in', v_in)
        try:
            rest = requests.post(endpoint, headers=headers, data=body.encode('utf-8'))
            req = rest.status_code
            res = rest.text
            ID_ZL_OUT = res[res.index('<ID_ZL_OUT>') + 11:res.index('</ID_ZL_OUT >')] if '</ID_ZL_OUT >' in res else ''
            STR_OUT = res[res.index('<STR_OUT>') + 9:res.index('</STR_OUT>')] if '</STR_OUT>' in res else ''
            ZAP = res[res.index('<ZAP>') + 4:res.index('</ZAP>')] if '</ZAP>' in res else ''
            resq = {
                'ID_ZL_OUT ': ID_ZL_OUT,
                'STR_OUT': STR_OUT,
                "ZAP": ZAP,
            }
        except Exception as err:
            resq = err
        return req, resq

    @staticmethod
    def web_appoint_cancel(args) -> str:
        """
        Вносит в базу сведения об аннулировании направления на госпитализацию.

        Сохраняет информацию об отмене направления в БД РИР
        """
        user = "lpu_a"
        paswd = "lpu_a"
        version = "1.7"
        lpu_dat = RirSend.get_lpu()
        date_send = datetime.date.today()
        v_cdnapr = args['cdnap']
        vvar = {
            'N_ZAP': '1',
            'RUID_NAPR': args['ruid'],
            'ORG': args['org'],
            'CODE': lpu_dat['reestr_nom'],
            'KODLPU': lpu_dat['cdlpu_u'],
            'D_CANC': date_send,
            'CODE_PR': args['code_pr'],
        }
        # trec = ''
        trec = '&lt;ZAP&gt;'
        for key in vvar:
            trec0 = '&lt;' + key.upper() + '&gt;' + str(vvar[key]) + '&lt;/' + key.upper() + '&gt;'
            trec = trec + trec0
        trec = trec + '&lt;/ZAP&gt;'
        v_in = """<_in>
                   <LOGIN>%(u)s</LOGIN>
                   <PASSWORD>%(p)s</PASSWORD>
                   <VERS>%(v)s</VERS>
                   <ZL>%(r)s</ZL>
                 </_in>""" % {'u': user, 'p': paswd, 'v': version, 'r': trec}
        body = t_body.replace('replace_web_f', 'WEB_AppCancel').replace('replace_in', v_in)
        # body_a = body.encode('utf-8').decode('utf-8')
        try:
            rest = requests.post(endpoint, headers=headers, data=body.encode('utf-8'))
            req = rest.status_code
            result = rest.text
            RUID_OUT = result[result.index('<RUID_OUT>') + 10:result.index('</RUID_OUT>')] if '</RUID_OUT>' in result else ''
            STR_OUT = result[result.index('<STR_OUT>') + 9:result.index('</STR_OUT>')] if '</STR_OUT>' in result else ''
            CNT_OSHIB = result[result.index('<CNT_OSHIB>') + 11:result.index(
                '</CNT_OSHIB>')] if '</CNT_OSHIB>' in result else ''
            PR = result[result.index('<PR>') + 4:result.index('</PR>')].replace('&lt;', '<').replace('&gt;',
                                                                                                     '>') if '</PR>' in result else ''
            res = {
                'RUID_OUT': RUID_OUT,
                'STR_OUT': STR_OUT,
                'CNT_OSHIB': CNT_OSHIB,
                'PR': PR
            }
            wres = {
                'cdnap': v_cdnapr,
                'type_': 1,
                'vozvrat': CNT_OSHIB,
                'insdate': date_send,
                'xmlresp': PR,
            }
            RirSend.write_result(wres)
        except Exception as err:
            res = err
        return req, res

    @staticmethod
    def web_appoint_corr(args) -> str:
        """
        Функция отправки информации о корректировке направлении на госпитализацию.

        Сохраняет информацию о корректировке направления в БД РИР
        """
        v_cddoc = args['cdnap']  # '84501391-ca56-411f-a5fa-47bcdc5a14f3'
        user = "lpu_a"
        paswd = "lpu_a"
        version = "1.7"
        date_send = datetime.date.today()
        v_ruid = RirSend.get_new_ruid()
        rec = get_scalar("""
                         select em_rir_make_xml_correct(:cduser, :cddoc);
                       """, [
            bindparam('cduser', type_=UUIDType, value=current_user.sessiondata['cduser']),
            bindparam('cddoc', type_=UUIDType, value=v_cddoc),
        ])
        ttrec = rec.replace('<', '&lt;').replace('>', '&gt;').replace('b\'', '', 1)
        trec = ttrec.replace('xxx', v_ruid, 1)  # .encode('Windows-1251')
        v_in = """<_in>
                    <LOGIN>%(u)s</LOGIN>
                    <PASSWORD>%(p)s</PASSWORD>
                    <VERS>%(v)s</VERS>
                    <ZAP>%(r)s</ZAP>
                   </_in>""" % {'u': user, 'p': paswd, 'v': version, 'r': trec}
        body = t_body.replace('replace_web_f', 'WEB_AppointCorr').replace('replace_in', v_in)
        try:
            rest = requests.post(endpoint, headers=headers, data=body.encode('utf-8'))
            req = rest.status_code
            result = rest.text
            RUID_OUT = result[result.index('<RUID_OUT>') + 10:result.index('</RUID_OUT>')] if '</RUID_OUT>' in result else ''
            STR_OUT = result[result.index('<STR_OUT>') + 9:result.index('</STR_OUT>')] if '</STR_OUT>' in result else ''
            CNT_OSHIB = result[result.index('<CNT_OSHIB>') + 11:result.index(
                '</CNT_OSHIB>')] if '</CNT_OSHIB>' in result else ''
            PR = result[result.index('<PR>') + 4:result.index('</PR>')].replace('&lt;', '<').replace('&gt;',
                                                                                                     '>') if '</PR>' in result else ''
            t_dict = xmltodict.parse(PR) if PR != '' else ''
            res = {
                'RUID_OUT': RUID_OUT,
                'STR_OUT': STR_OUT,
                'CNT_OSHIB': CNT_OSHIB,
                'PR': t_dict
            }
            wres = {
                'cdnap': v_cddoc,
                'type_': 1,
                'vozvrat': CNT_OSHIB,
                'insdate': date_send,
                'xmlresp': PR,
            }
            RirSend.write_result(wres)
        except Exception as err:
            res = err
        return req, res

    @staticmethod
    def web_appoint_cap(args):
        """Функция для поиска сведений о конкретной госпитализации."""
        req, res = RirSend.get_appoint_info(args)
        if req == 200:
            iz_first = res['STR_OUT']
            req, res = RirSend.web_appoint(args) if iz_first != '' else RirSend.web_appoint_corr(args)
        return req, res
