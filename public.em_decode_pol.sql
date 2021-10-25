--Function: public.em_decode_pol(text)

--DROP FUNCTION public.em_decode_pol(text);

CREATE OR REPLACE FUNCTION public.em_decode_pol
(
  IN  _varrec  text
)
RETURNS integer AS
$$
DECLARE   _res	  text:= 1;


    /*Sinelnikov 22092021*/
   /*функция перевода м/ж в 1/2*/
BEGIN
  
 if _varrec is null
    then _res = 1 ; 
    else 
      if upper(_varrec) = 'М' then _res = 1 ; 
      else _res = 2;
      end if;  
 end if; 
  
 RETURN _res;
   
END;
$$
LANGUAGE 'plpgsql';

ALTER FUNCTION public.em_decode_pol(text)
  OWNER TO postgres;