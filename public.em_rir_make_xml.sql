--Function: public.em_rir_make_xml(uuid, uuid)

--DROP FUNCTION public.em_rir_make_xml(uuid, uuid);

CREATE OR REPLACE FUNCTION public.em_rir_make_xml
(
  IN  v_cduser  uuid,
  IN  v_cddoc   uuid
)
RETURNS text AS
$$
import os
  import datetime
  from datetime import datetime as dt
  import xml.etree.cElementTree as ET  
  from xml.etree.ElementTree import Element
  from lxml import etree
  from lxml.builder import E as buildE 
  # Sinelnikov 16092021.   
  # функция формирует XML для отправки в РИР doclpu.npoli
  # docnapr.cdpom::text FOR_POM,
  plan1=plpy.prepare('SELECT \'1\' as N_ZAP, ' \
                'DOCNAPR.nomnapr as RUID_NAPR, '\
                'DOCNAPR.DATNAPR as D_NAPR, ' \
                'case when docnapr.isvmp = 1 ' \
                ' then \'1\' ' \
                ' else \'0\' ' \
                ' end as PR_VMP, ' \
                ' \'3\' FOR_POM, ' \
                'sllpus.reestr_nom::text as CODE_MO_S, ' \
                'sllpus.cdlpu_u::text as KODLPU_S, ' \
                'sllpunapr.reestr_nom::text as CODE_MO_R, ' \
                'sllpunapr.CDLPU_U::text as KODLPU_R, ' \
                'unloader_schet.tag_vpolis(doclpu.spoli,doclpu.npoli)::text as VPOLIS, ' \
                'doclpu.spoli::text as SPOLIS, ' \
                'doclpu.npoli::text as NPOLIS,' \
                'em_nvl(slstrah.reestr_nom)::text as SMO,' \
                'em_nvl(slstrah.nmstr)::text as SMO_NAM,' \
                'em_nvl(slterr.okato)::text as SMO_OK,' \
                'em_nvl(SLDOCUM.cddoc_u)::text as DOCTYPE,' \
                'em_nvl(pacientdoc.seria)::text as DOCSER,' \
                'em_nvl(pacientdoc.nomer)::text as DOCNUM,' \
                'case when (sltypesoc.cdtypesoc_u=\'2\' and slsocgr.cdsocgr_fed=\'1\' ) ' \
                ' then \'1\' ' \
                ' else \'0\' ' \
                ' end  as NOVOR, ' \
                'case when (sltypesoc.cdtypesoc_u=\'2\' and slsocgr.cdsocgr_fed=\'1\' ) ' \
                ' then pac_parent.famip ' \
                ' else pacient.famip end as FAM, ' \
                'case when (sltypesoc.cdtypesoc_u=\'2\' and slsocgr.cdsocgr_fed=\'1\' )' \
                ' then pac_parent.namep ' \
                ' else  pacient.namep end as IM,' \
                'case when (sltypesoc.cdtypesoc_u=\'2\' and slsocgr.cdsocgr_fed=\'1\' ) ' \
                ' then pac_parent.otchp ' \
                ' else  pacient.otchp end as OT, ' \
                'case when  (sltypesoc.cdtypesoc_u=\'2\' and slsocgr.cdsocgr_fed=\'1\' ) ' \
                ' then em_decode_pol(pac_parent.polpa)::text  else em_decode_pol(pacient.polpa)::text end as W, ' \
                '  case when (sltypesoc.cdtypesoc_u=\'2\' and slsocgr.cdsocgr_fed=\'1\' ) ' \
                '  then pac_parent.drogd::text ' \
                '  else pacient.drogd::text end as DR,' \
                '  pacient.tel::text as PHONE,' \
                '  DOCNAPR.shdinapr::text as DS,' \
                '  slmedprof_v020.kod_ef::text as PROFIL,' \
                '  slotdprof_reg.cdotdprof_reg_u::text as PODR,' \
                '  docnapr.nomotdnapr::text as N_OTD,' \
                '  DOCNAPR.PRDNSNAPR::text as PR_DS,' \
                '  SLSOTRPERSON.cnilssotr::text as IDDOKT,' \
                '  DOCNAPR.pldatgosp::date as D_PLAN,' \
                '  case when DOCNAPR.cdvdia = 2 '\
                '  then \'1\' ' \
                '  else \'0\' end as PERV_DIAGN ' \
                '  from public.DOCLPU ' \
                ' left join public.slterr on slterr.cdter = DOCLPU.cdter ' \
                '  LEFT JOIN SLSOTR on SLSOTR.CDSOTR = DOCLPU.CDSOTR '\
                '  LEFT JOIN SLOTDEL on SLOTDEL.CDOTDEL = SLSOTR.CDOTDEL '\
                '  INNER JOIN public.DOCZAG on DOCZAG.CDREG = DOCLPU.CDREG ' \
                '  INNER JOIN public.DOCNAPR on DOCNAPR.CDREG = DOCZAG.CDREG ' \
                '  LEFT JOIN public.SLLPU  as sllpunapr on sllpunapr.CDLPU = DOCNAPR.CDLPUNAPR ' \
                '  LEFT JOIN public.SLLPU  as sllpus on sllpus.cdlpu = SLOTDEL.cdlpu ' \
                '  LEFT JOIN public.slotdprof_reg on slotdprof_reg.cdotdprof_reg = DOCNAPR.cdotdprof_reg_napr ' \
                '  left join public.slstrah on slstrah.cdstr = doclpu.cdstr ' \
                '  LEFT JOIN public.PACIENT on PACIENT.CDPAC = DOCZAG.CDPAC ' \
                '  left join public.pacientdoc on pacientdoc.cdpac = pacient.cdpac ' \
                '  left join public.SLDOCUM on SLDOCUM.CDDOC = pacientdoc.cddocum ' \
                ' left join public.sltypedoc on (sltypedoc.cdtypedoc = SLDOCUM.cdtypedoc) ' \
                '  left join public.pacientsoc on pacientsoc.cdpac = PACIENT.CDPAC ' \
                '  left join public.slsocgr on slsocgr.cdsocgr = pacientsoc.cdsocgr ' \
                ' left join public.sltypesoc on (sltypesoc.cdtypesoc = slsocgr.cdtypesoc) ' \
                '  left join public.pacientfamily on pacientfamily.cdpac = PACIENT.cdpac ' \
                '  LEFT JOIN public.PACIENT pac_parent on pac_parent.CDPAC = pacientfamily.cdpacrel ' \
                '  LEFT JOIN slmedprof_v020 on slmedprof_v020.cdprof = DOCNAPR.cdprof_v020_napr ' \
                '  LEFT JOIN SLSOTRPERSON on SLSOTRPERSON.CDSOTRPERSON=SLSOTR.CDSOTRPERSON ' \
                '  WHERE (DOCLPU.ZADACH=140) and doclpu.isdone = 0 ' \
                ' and sltypedoc.cdtypedoc_u=\'1\' '\
                '  and DOCNAPR.cdnap = $1 ' \
                ' order by pacientfamily.today desc limit 1 ', ["uuid"])
  rec = plpy.execute(plan1, [v_cddoc])  
  rw = 0
  v_fname = ''
  v_kod_s = ''
  v_kod_r = ''
  xml_str = '<ZAP>'
  # ZL_LIST = ET.Element("ZL_LIST")
  # ZGL = ET.SubElement(ZL_LIST, "ZGL")
  # ZAP = ET.SubElement(ZL_LIST, "ZAP")

  # ET.SubElement(ZGL, "VERSION").text = "1.7"
  # ET.SubElement(ZGL, "DATA").text = datetime.datetime.now().strftime("%d-%m-%Y %H.%M.%S")
  # ET.SubElement(ZGL, "FILENAME").text = "HPiNiPpNp_YYMMDD_GUID"
  # ET.SubElement(ZGL, "PROG_NAME").text = "webmis"
  if len(rec) > 0:
    for key in rec[0]:
      if rec[0][key] != None and rec[0][key] != '' :
        t_str = '<' + key.upper() +'>' + rec[0][key] + '</' + key.upper() +'>'
      else:  
        t_str = '<' + key.upper() +'/>'   
      xml_str = xml_str + t_str   
      #ET.SubElement(ZAP, key.upper()).text = t_str
      #if key == 'KODLPU_S':
        #v_kod_s = rec[0][key]
      #if key == 'KODLPU_R':
        #v_kod_r = rec[0][key]
  # tree.write("filename.xml")
  #xml_str = ET.tostring(ZL_LIST, encoding='UTF-8')
  # xml_str = ET.tostring(ZAP, encoding='cp1251')
  # v_fname = 'INM'
  return xml_str + '</ZAP>'
$$
LANGUAGE 'plpython3u';

ALTER FUNCTION public.em_rir_make_xml(uuid, uuid)
  OWNER TO postgres;