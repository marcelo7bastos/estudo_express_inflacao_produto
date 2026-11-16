# Tomate: preços de 2015 a 2026 e perspectivas para 2027–2028

Relatório técnico sobre a evolução do preço do tomate no Brasil: inflação (IPCA), preço no atacado por praça, repasse do atacado ao varejo, sazonalidade, produção por estado, agricultura familiar, consumo, clima (El Niño e mudança do clima), custos, contexto internacional e cenários para 2027–2028.

**Página:** https://marcelo7bastos.github.io/estudo_express_inflacao_produto/tomate/

**Autor:** Marcelo Cabreira Bastos · Dados até outubro de 2026 (IPCA) e setembro de 2026 (atacado) · Elaborado em novembro de 2026

## Aviso sobre uso de inteligência artificial

Este estudo foi elaborado com apoio de um assistente de inteligência artificial (Claude, da Anthropic), sob orientação e responsabilidade do autor. A IA coletou os dados nas fontes oficiais, escreveu os scripts, produziu os gráficos e redigiu o texto. O conteúdo não passou por revisão por pares. Podem existir erros de extração, de cálculo ou de interpretação. Confira os números nas fontes originais antes de usá-los em decisões ou citações.

Os estudos acadêmicos citados foram consultados por resumos e resultados de busca, sem leitura integral.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `index.html` | Página do relatório (autônoma, com os dados embutidos) |
| `scripts/01_baixar_dados.sh` | Baixa os dados brutos das fontes oficiais |
| `scripts/02_processar_ibge_noaa_bm_fao.py` | Organiza IPCA, PAM, LSPA, Censo, POF, ONI, Banco Mundial e FAO |
| `scripts/03_extrair_precos_conab.py` | Extrai o preço do tomate por CEASA dos boletins da Conab (PDF e planilhas) |
| `scripts/04_analise.py` | Preços reais, sazonalidade, repasse, clima, custos e projeção |
| `scripts/05_montar_pagina.py` | Gera `index.html` a partir de `scripts/modelo_pagina.html` |
| `dados/brutos/` | Arquivos baixados das fontes (exceto boletins da Conab e arquivos da FAO, por tamanho) |
| `dados/processados/` | Resultados intermediários e finais em JSON |

## Como reproduzir

Todos os comandos rodam a partir da pasta `tomate/`.

Requer Python 3.11+, `curl`, `unzip` e `pdftotext` (pacote poppler-utils).

```bash
pip install -r requirements.txt
```

```bash
bash scripts/01_baixar_dados.sh
```

```bash
python3 scripts/02_processar_ibge_noaa_bm_fao.py
```

```bash
python3 scripts/03_extrair_precos_conab.py
```

```bash
python3 scripts/04_analise.py
```

```bash
python3 scripts/05_montar_pagina.py
```

O passo 01 baixa cerca de 1,6 GB (boletins da Conab e bases da FAO). Para refazer só a análise e a página com os dados já versionados, rode apenas os passos 04 e 05.

## Fontes de dados

- IBGE, IPCA: [tabela 7060](https://sidra.ibge.gov.br/tabela/7060) e [tabela 1419](https://sidra.ibge.gov.br/tabela/1419)
- IBGE, Produção Agrícola Municipal: [tabela 1612](https://sidra.ibge.gov.br/tabela/1612); LSPA: [tabela 6588](https://sidra.ibge.gov.br/tabela/6588)
- IBGE, Censo Agropecuário 2017: [tabela 6953](https://sidra.ibge.gov.br/tabela/6953) e [tabela 6957](https://sidra.ibge.gov.br/tabela/6957)
- IBGE, POF: [tabela 2393](https://sidra.ibge.gov.br/tabela/2393) e [tabela 8157](https://sidra.ibge.gov.br/tabela/8157)
- Conab, [Boletim Hortigranjeiro (Prohort)](https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/hortigranjeiros-prohort/boletim-hortigranjeiro), edições de 2015 a outubro de 2026 (lista em `dados/brutos/conab_boletins_links.txt`)
- NOAA Climate Prediction Center, [Oceanic Niño Index](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt)
- Banco Mundial, [Commodity Price Data (Pink Sheet)](https://www.worldbank.org/en/research/commodity-markets)
- FAO, [FAOSTAT](https://www.fao.org/faostat/en/#data)
- Banco Central do Brasil, SGS série 3698 (câmbio médio mensal)

## Limitações

- A série de atacado foi montada a partir das tabelas dos boletins da Conab. Faltam janeiro a março de 2015, e alguns meses foram deduzidos da variação publicada no boletim seguinte.
- A Conab não publica o tomate da CEASA da Bahia nesses boletins.
- Não foram obtidas as séries do Cepea/Hortifruti Brasil nem preços de contrato do tomate industrial.
- O dado de agricultura familiar é do Censo Agropecuário de 2017.
- A projeção vem de um modelo estatístico simples (SARIMA) e tem erro grande: 15% em média no teste de 24 meses.
