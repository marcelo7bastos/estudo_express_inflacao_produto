#!/usr/bin/env bash
# Baixa os dados brutos das fontes oficiais. Rodar a partir da pasta tomate/.
# Os boletins da Conab (~840 MB) e os arquivos da FAO (~725 MB) não são versionados.
set -u
D=dados/brutos; mkdir -p "$D/conab/pdf" "$D/fao"
g(){ for i in 1 2 3; do curl -s -m 180 -L "$2" -o "$1"; [ "$(wc -c <"$1")" -gt 300 ] && break; sleep 5; done; echo "$1 $(wc -c <"$1")"; }
B=https://apisidra.ibge.gov.br/values
# IPCA: tomate (7212), índice geral (7169), alimentação e bebidas (7170); Brasil, regiões metropolitanas e municípios
for n in n1 n7 n6; do
  g $D/ipca7060_$n.json "$B/t/7060/$n/all/v/63,66/p/all/c315/7169,7170,7212/d/v63%202,v66%204"
  g $D/ipca1419_$n.json "$B/t/1419/$n/all/v/63,66/p/201201-201912/c315/7169,7170,7212/d/v63%202,v66%204"
done
# Produção Agrícola Municipal (tomate = 2715) e LSPA (tomate = 39470)
g $D/pam_n1.json "$B/t/1612/n1/all/v/216,214,112,215/p/2010-2025/c81/2715"
g $D/pam_n3.json "$B/t/1612/n3/all/v/216,214,112,215/p/2010-2025/c81/2715"
g $D/pam_n6_last.json "$B/t/1612/n6/all/v/214,216/p/last%201/c81/2715"
g $D/lspa_n1.json "$B/t/6588/n1/all/v/216,35,36/p/all/c48/39470"
g $D/lspa_n3.json "$B/t/6588/n3/all/v/216,35,36/p/last%201/c48/39470"
# Censo Agropecuário 2017: tomate estaqueado (horticultura) e rasteiro (lavoura temporária), por tipologia
for n in n1 n3; do
  g $D/censo_rasteiro_$n.json "$B/t/6957/$n/all/v/10084,10085,10086,10087,10089/p/2017/c829/46302,46303,46304/c226/111680/c218/46502/c12517/113601"
  g $D/censo_estaq_$n.json "$B/t/6953/$n/all/v/2312,10090,10091,10092/p/2017/c829/46302,46303,46304/c228/111604/c218/46502/c12517/113601"
done
# POF: aquisição alimentar domiciliar per capita
for n in n1 n2 n3; do g $D/pof2393_$n.json "$B/t/2393/$n/all/v/1207/p/all/c217/3953,4648,4651"; done
g $D/pof8157.json "$B/t/8157/n1/all/v/1207/p/all/c339/all/c217/3953,4648,4651"
# NOAA (ONI), Banco Central (câmbio), Banco Mundial (Pink Sheet; o endereço muda a cada edição), FAO
g $D/oni.txt https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
g $D/ptax.json "https://api.bcb.gov.br/dados/serie/bcdata.sgs.3698/dados?formato=json&dataInicial=01/01/2012&dataFinal=31/10/2026"
WB=$(curl -s -m 60 -L https://www.worldbank.org/en/research/commodity-markets | grep -oE 'https://thedocs[^"]+Monthly\.xlsx' | head -1)
g $D/wb_monthly.xlsx "$WB"
g $D/fao/prices.zip "https://bulks-faostat.fao.org/production/Prices_E_All_Data_(Normalized).zip"
g $D/fao/prod.zip "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
(cd $D/fao && unzip -o -q prices.zip && unzip -o -q prod.zip)
# Conab: boletins hortigranjeiros (PDF e planilhas) listados em conab_boletins_links.txt
xargs -P 6 -I{} sh -c 'f='"$D"'/conab/pdf/$(echo "{}" | sed "s#.*/boletim-hortigranjeiro/##; s#/#_#g"); [ -s "$f" ] || curl -s -m 300 --retry 2 -L "{}" -o "$f"' < $D/conab_boletins_links.txt
