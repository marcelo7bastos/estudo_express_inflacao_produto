import json,collections,re,pandas as pd,numpy as np,openpyxl
D='dados/brutos/';out={}
def rows(f): return json.load(open(D+f))[1:]
def num(v):
    try: return float(v)
    except: return None
# ---------- IPCA
def ipca(files):
    s=collections.defaultdict(dict)
    for f in files:
        for x in rows(f): s[(x['D1N'],x['D2C'],x['D4C'])][x['D3C']]=num(x['V'])
    return s
s=ipca(['ipca1419_n1.json','ipca7060_n1.json','ipca1419_n7.json','ipca7060_n7.json','ipca1419_n6.json','ipca7060_n6.json'])
areas=sorted({k[0] for k in s})
months=sorted(s[('Brasil','63','7169')])
out['months']=months
def idx(series):
    v=1;o=[]
    for m in months:
        x=series.get(m)
        if x is None: o.append(None); continue
        v*=1+x/100;o.append(v)
    return o
ip={}
for a in areas:
    t=s[(a,'63','7212')];g=s[(a,'63','7169')];al=s[(a,'63','7170')];w=s[(a,'66','7212')]
    if sum(1 for m in months if t.get(m) is not None)<100: continue
    it=idx(t);ig=idx(g);ia=idx(al)
    ip[a]={'var':[t.get(m) for m in months],'geral':[g.get(m) for m in months],'alim':[al.get(m) for m in months],'peso':[w.get(m) for m in months],'it':it,'ig':ig,'ia':ia}
out['ipca']=ip
print(len(ip),list(ip))
# ---------- PAM
pam=collections.defaultdict(lambda: collections.defaultdict(dict))
for f in ['pam_n1.json','pam_n3.json']:
    for x in rows(f): pam[x['D1N']][x['D2C']][x['D3C']]=num(x['V'])
out['pam']={a:{v:d for v,d in vs.items()} for a,vs in pam.items()}
# LSPA latest per year for Brasil
l=collections.defaultdict(dict)
for x in rows('lspa_n1.json'): l[x['D2C']][x['D3C']]=num(x['V'])
print('LSPA last', sorted(l['35'])[-3:], [l['35'][k] for k in sorted(l['35'])[-3:]], l['216'][sorted(l['216'])[-1]], l['36'][sorted(l['36'])[-1]])
last=sorted(l['35'])[-1]
out['lspa']={'ref':last,'br':{v:l[v][last] for v in l},'dez2025':{v:l[v].get('202512') for v in l}}
lu=collections.defaultdict(dict)
for x in rows('lspa_n3.json'): lu[x['D1N']][x['D2C']]=num(x['V'])
out['lspa']['uf']=lu
# municipalities
mu=collections.defaultdict(dict)
for x in rows('pam_n6_last.json'): mu[x['D1N']][x['D2C']]=num(x['V']); yr=x['D3C']
top=sorted([(k,v.get('214') or 0,v.get('216') or 0) for k,v in mu.items()],key=lambda z:-z[1])[:20]
out['pam_mun']={'ano':yr,'top':top}
# ---------- Censo
def censo(f,vq):
    c=collections.defaultdict(lambda: collections.defaultdict(dict))
    for x in rows(f): c[x['D1N']][x['D4N']][x['D2C']]=num(x['V'])
    return c
out['censo']={'estaq':censo('censo_estaq_n1.json',0)|censo('censo_estaq_n3.json',0),'rast':censo('censo_rasteiro_n1.json',0)|censo('censo_rasteiro_n3.json',0)}
print(json.dumps(out['censo']['estaq']['Brasil'],ensure_ascii=False)); print(json.dumps(out['censo']['rast']['Brasil'],ensure_ascii=False))
# ---------- POF
pof=collections.defaultdict(lambda: collections.defaultdict(dict))
for f in ['pof2393_n1.json','pof2393_n2.json','pof2393_n3.json']:
    for x in rows(f): pof[x['D1N']][x['D4N']][x['D3C']]=num(x['V'])
out['pof']=pof; print(json.dumps(pof['Brasil'],ensure_ascii=False)); print({a:pof[a]['2.2.12 Tomate'] for a in ['Norte','Nordeste','Sudeste','Sul','Centro-Oeste']})
pr=collections.defaultdict(dict)
for x in rows('pof8157.json'): pr[x['D4N']][x['D5N']]=num(x['V'])
out['pof_renda']=pr; print(json.dumps(pr,ensure_ascii=False))
# ---------- ONI
seas=['DJF','JFM','FMA','MAM','AMJ','MJJ','JJA','JAS','ASO','SON','OND','NDJ']
oni={}
for ln in open(D+'oni.txt').read().split('\n')[1:]:
    p=ln.split()
    if len(p)==4: oni[f"{p[1]}{seas.index(p[0])+1:02d}"]=float(p[3])
out['oni']={m:oni.get(m) for m in months}; print('oni last',[(m,oni.get(m)) for m in months[-5:]])
# ---------- World Bank
ws=openpyxl.load_workbook(D+'wb_monthly.xlsx',read_only=True)['Monthly Prices']
R=list(ws.iter_rows(values_only=True))
hdr=R[4];cols={str(h).strip():i for i,h in enumerate(hdr) if h}
wb={}
for name in ['Urea','DAP','Potassium chloride **','Crude oil, Brent']:
    i=cols[name];d={}
    for r in R[6:]:
        if r[0] and re.match(r'\d{4}M\d\d',str(r[0])):
            d[str(r[0]).replace('M','')]=num(r[i])
    wb[name.replace(' **','')]=[d.get(m) for m in months]
out['wb']=wb; print({k:v[-3:] for k,v in wb.items()})
# ---------- FAO
p=pd.read_csv(D+'fao/Prices_E_All_Data_(Normalized).csv',encoding='latin-1',low_memory=False)
t=p[(p.Item=='Tomatoes')&(p.Element=='Producer Price (USD/tonne)')&(p.Year>=2015)&(p.Months=='Annual value')]
sel=['Brazil','Mexico','United States of America','Spain','Italy','Portugal','Chile']
out['fao_price']={a:{int(y):v for y,v in t[t.Area==a].set_index('Year').Value.items()} for a in sel}
q=pd.read_csv(D+'fao/Production_Crops_Livestock_E_All_Data_(Normalized).csv',encoding='latin-1',low_memory=False)
t=q[(q.Item=='Tomatoes')&(q.Year==2024)&(q['Area Code']<5000)&(q.Area!='China')]
pr_=t[t.Element=='Production'].sort_values('Value',ascending=False).head(12)
yl=t[t.Element=='Yield'].set_index('Area').Value
out['fao_prod']=[(a.replace('Ã¼','ü'),v,yl.get(a)) for a,v in zip(pr_.Area,pr_.Value)]
w=q[(q.Item=='Tomatoes')&(q.Year==2024)&(q.Area=='World')]
out['fao_world']={e:v for e,v in zip(w.Element,w.Value)}
print(out['fao_prod'],out['fao_world'],out['fao_price']['Brazil'])
json.dump(out,open('dados/processados/ibge_etc.json','w'),ensure_ascii=False)
