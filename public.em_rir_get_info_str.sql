CREATE OR REPLACE FUNCTION public.em_rir_get_info_str(IN  v_cduser  uuid,IN  v_cdpac   uuid)
RETURNS text AS
$$
  import os
  import datetime
  from datetime import datetime as dt
  # Sinelnikov 04102021.   
  # Функция определения страховой принадлежности пациента.
  plan1 = plpy.prepare('select pc.famip as FAM,pc.namep as IM, \
  pc.otchp as OT, em_decode_pol(pc.polpa) as W,pc.drogd as DR, \
  docm.cddoc_u as DOCTYPE,pcd.seria as DOCSER, \
  pcd.nomer as DOCNUM,tpp.cdtypepoli_u as VPOLIS, \
  pols.npoli as NPOLIS,slstrah.reestr_nom as SMOCOD,slstrah.okato as SMO_OK \
  from public.PACIENT pc \
  LEFT JOIN public.pacientpoli pols on pols.cdpac = pc.CDPAC \
  left join public.pacientdoc  pcd on pcd.cdpac = pc.CDPAC \
  left join public.slstrah on slstrah.cdstr = pols.cdstr \
  left join public.SLDOCUM docm on docm.CDDOC = pcd.cddocum \
  left join public.sltypepoli tpp on tpp.cdtypepoli = pols.cdtypepoli \
  where pcd.seria != \'\' and  pc.cdpac = $1', ["uuid"])
  rec = plpy.execute(plan1, [v_cdpac])  
  rw = 0
  v_fname = ''
  v_kod_s = ''
  v_kod_r = ''
  xml_str = '<ZL>'
  if len(rec) > 0:
    for key in rec[0]:
      if rec[0][key] != None and rec[0][key] != '' :
        t_str = '<' + key.upper() +'>' + str(rec[0][key]) + '</' + key.upper() +'>'
      else:  
        t_str = '<' + key.upper() +'/>'   
      xml_str = xml_str + t_str   

  return xml_str + '</ZL>'
$$
LANGUAGE 'plpython3u';
