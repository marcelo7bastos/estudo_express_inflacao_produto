"""Monta dados/processados/dados_pagina.json e o index.html autônomo (GitHub Pages).
Rodar a partir da pasta tomate/, depois de 02, 03 e 04."""
import json
AUTOR = "Marcelo Cabreira Bastos"   # assinatura exibida na página
P = 'dados/processados/'
R = json.load(open(P + 'analysis.json')); d = json.load(open(P + 'ibge_etc.json'))
X = {k: R[k] for k in R if k not in ('ptax', 'wb', 'deriva', 'deriva_geral')}
pam = d['pam']
X['uf'] = sorted([{'uf': u, 'p25': pam[u]['214'].get('2025'), 'p15': pam[u]['214'].get('2015'), 'a25': pam[u]['216'].get('2025'), 'r25': pam[u]['112'].get('2025')}
                  for u in pam if u != 'Brasil' and pam[u]['214'].get('2025')], key=lambda z: -z['p25'])
X['mun'] = d['pam_mun']
X['lspa'] = {'ref': d['lspa']['ref'], 'br': d['lspa']['br'], 'dez2025': d['lspa']['dez2025'], 'uf': {u: v for u, v in d['lspa']['uf'].items() if (v.get('35') or 0) > 100000}}
def cz(c, q, n):
    o = {}
    for u, e in c.items():
        try:
            t = e['Total']; f = e['Agricultura familiar - sim']
            if t.get(q): o[u] = {'q': t[q], 'af': f.get(q) or 0, 'n': t.get(n), 'naf': f.get(n) or 0}
        except KeyError: pass
    return o
X['censo'] = {'estaq': cz(d['censo']['estaq'], '10090', '2312'), 'rast': cz(d['censo']['rast'], '10085', '10084')}
X['pof'] = {a: d['pof'][a] for a in ['Brasil', 'Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']}; X['pof_renda'] = d['pof_renda']
X['fao_prod'] = d['fao_prod']; X['fao_world'] = d['fao_world']; X['fao_price'] = d['fao_price']
dados = json.dumps(X, ensure_ascii=False, separators=(',', ':')).replace('NaN', 'null')
open(P + 'dados_pagina.json', 'w').write(dados)
t = open('scripts/modelo_pagina.html').read().replace('/*DATA*/', dados.replace('</', '<\\/')).replace('{{AUTOR}}', AUTOR)
head = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="Relatório técnico sobre a evolução do preço do tomate no Brasil (2015–2026) e perspectivas para 2027–2028.">\n'
        '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
i = t.index('<div class="wrap">')
open('index.html', 'w').write(head + t[:i] + '</head>\n<body>\n' + t[i:] + '\n</body>\n</html>\n')
print('index.html', len(open('index.html').read()))
