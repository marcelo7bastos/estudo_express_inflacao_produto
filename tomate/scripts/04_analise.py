import json,numpy as np,pandas as pd,warnings,collections
warnings.filterwarnings('ignore')
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
d=json.load(open('dados/processados/ibge_etc.json'));c=json.load(open('dados/processados/conab.json'))
M=d['months'];ix=pd.PeriodIndex([f"{m[:4]}-{m[4:]}" for m in M],freq='M')
def S(v): return pd.Series(v,index=ix,dtype=float)
br=d['ipca']['Brasil'];ig=S(br['ig']);it=S(br['it']);var=S(br['var']);peso=S(br['peso'])
R={}  # results
last=ix[-1]
defl=ig[last]/ig            # multiplica valor nominal -> R$ de out/2026
real=(it/ig); real=real/real['2015'].mean()*100
R['months']=[str(p) for p in ix]
R['ipca']={'var':var.round(2).tolist(),'v12':((it/it.shift(12)-1)*100).round(1).tolist(),'g12':((ig/ig.shift(12)-1)*100).round(2).tolist(),
 'real':real.round(1).tolist(),'peso':peso.round(3).tolist(),'contrib':(peso.shift(0)*var/100).round(3).tolist()}
ann=[]
for y in range(2013,2027):
    a=pd.Period(f'{y-1}-12','M');b=pd.Period(f'{y}-12','M') if y<2026 else last
    sub=slice(f'{y}-01',str(b))
    ann.append({'ano':y,'tom':round((it[b]/it[a]-1)*100,1),'geral':round((ig[b]/ig[a]-1)*100,2),'contrib':round(float((peso[sub]*var[sub]/100).sum()),2),'real_med':round(float(real[sub].mean()),1),'parcial':y==2026})
R['anual']=ann
print(pd.DataFrame(ann).to_string())
print('real: media 2015-2026',real['2015':].mean().round(1),'min',real['2015':].idxmin(),real['2015':].min().round(1),'max',real['2015':].idxmax(),real['2015':].max().round(1),'ultimo',real.iloc[-1].round(1))
lr=np.log(real['2015':]);t=np.arange(len(lr));b=np.polyfit(t,lr,1);print('tendencia real % a.a.',round((np.exp(b[0]*12)-1)*100,2))
R['trend_real_aa']=round((np.exp(b[0]*12)-1)*100,2)
mv=var['2015':];print('desvio mensal tomate',mv.std().round(1),'geral',S(br['geral'])['2015':].std().round(2),'alim',S(br['alim'])['2015':].std().round(2))
R['vol']={'tom':round(mv.std(),1),'geral':round(S(br['geral'])['2015':].std(),2),'alim':round(S(br['alim'])['2015':].std(),2),'meses_alta20':int((mv>=20).sum()),'meses_queda20':int((mv<=-20).sum()),'n':len(mv)}
# sazonalidade IPCA (razão à média móvel centrada 12m)
def seas(s):
    ma=s.rolling(12,center=True).mean();ma=(ma+ma.shift(-1))/2
    r=(s/ma).dropna();g=r.groupby(r.index.month).mean();return (g/g.mean()*100).round(1).tolist()
R['saz_ipca']=seas(real['2015':])
# regional
reg={}
for a,v in d['ipca'].items():
    if a=='Brasil': continue
    t_=S(v['it']);g_=S(v['ig']);r_=t_/g_;r_=r_/r_['2015'].mean()*100
    reg[a]={'real':r_.round(1).tolist(),'acum':round((t_[last]/t_['2014-12']-1)*100,0),'v12':round((t_[last]/t_[last-12]-1)*100,1),'ytd':round((t_[last]/t_['2025-12']-1)*100,1),'dp':round(S(v['var'])['2015':].std(),1),'peso':v['peso'][-1]}
R['reg']=reg
print(pd.DataFrame({a:{k:x for k,x in v.items() if k!='real'} for a,v in reg.items()}).T.sort_values('acum').to_string())
print('Brasil acum',round((it[last]/it['2014-12']-1)*100,0),'geral',round((ig[last]/ig['2014-12']-1)*100,0))
R['acum_br']={'tom':round((it[last]/it['2014-12']-1)*100,0),'geral':round((ig[last]/ig['2014-12']-1)*100,0),'alim':round((S(br['ia'])[last]/S(br['ia'])['2014-12']-1)*100,0)}
# ---------- atacado
core=['SP','BH','RJ','ES','PR','GO','PE','CE'];extra=['DF','Campinas','SC']
W=pd.DataFrame({k:pd.Series({pd.Period(f"{m[:4]}-{m[4:]}",'M'):v[k][0] for m,v in c['P'].items() if k in v}) for k in core+extra}).reindex(ix['2015-01'<=ix.astype(str)])
W=W[W.index>='2015-01']
Wr=W.mul(defl.reindex(W.index),axis=0)
comp=Wr[core].mean(axis=1).where(Wr[core].notna().sum(axis=1)>=5); compn=W[core].mean(axis=1).where(W[core].notna().sum(axis=1)>=5)
R['wmonths']=[str(p) for p in W.index]
R['w']={k:[None if pd.isna(x) else round(x,2) for x in W[k]] for k in W}
R['wr']={k:[None if pd.isna(x) else round(x,2) for x in Wr[k]] for k in Wr}
R['comp']=[None if pd.isna(x) else round(x,2) for x in comp];R['compn']=[None if pd.isna(x) else round(x,2) for x in compn]
st={}
for k in W:
    s=Wr[k].dropna();dl=np.log(W[k]).diff().dropna()
    st[k]={'n':len(s),'media':round(s.mean(),2),'cv':round(s.std()/s.mean()*100,0),'min':round(s.min(),2),'max':round(s.max(),2),'ult':round(s.iloc[-1],2),'ult_m':str(s.index[-1]),'dpm':round(dl.std()*100,0),'corr_sp':round(np.log(W[k]).diff().corr(np.log(W['SP']).diff()),2),'m2025':round(Wr[k]['2025'].mean(),2),'m2026':round(Wr[k]['2026'].mean(),2)}
R['wstat']=st;print(pd.DataFrame(st).T.to_string())
print('composto real: media',comp.mean().round(2),'ultimo',comp.dropna().iloc[-1].round(2),comp.dropna().index[-1],'max',comp.idxmax(),comp.max().round(2),'min',comp.idxmin(),comp.min().round(2))
R['compstat']={'media':round(comp.mean(),2),'ult':round(comp.dropna().iloc[-1],2),'max':round(comp.max(),2),'maxm':str(comp.idxmax()),'min':round(comp.min(),2),'minm':str(comp.idxmin())}
R['comp_ano']={int(y):round(v,2) for y,v in comp.groupby(comp.index.year).mean().items()}
print(R['comp_ano'])
R['saz_w']=seas(comp.interpolate());print('saz ipca',R['saz_ipca']);print('saz atac',R['saz_w'])
cm=np.log(W[core]).diff().corr().round(2);R['corr']={'labels':core,'m':cm.values.tolist()};print(cm.to_string())
# ---------- repasse atacado -> varejo
pairs={'SP':'São Paulo - SP','BH':'Belo Horizonte - MG','RJ':'Rio de Janeiro - RJ','ES':'Grande Vitória - ES','PR':'Curitiba - PR','GO':'Goiânia - GO','PE':'Recife - PE','CE':'Fortaleza - CE','DF':'Brasília - DF'}
pt={};pool=[]
for k,a in pairs.items():
    rt=np.log(S(d['ipca'][a]['it'])).diff();w=np.log(W[k]).diff()
    df=pd.DataFrame({'y':rt,'w0':w,'w1':w.shift(1),'w2':w.shift(2)}).dropna()
    m=sm.OLS(df.y,sm.add_constant(df[['w0','w1','w2']])).fit()
    # assimetria
    df['up']=df.w0.clip(lower=0);df['dn']=df.w0.clip(upper=0)
    m2=sm.OLS(df.y,sm.add_constant(df[['up','dn','w1']])).fit()
    pt[k]={'area':a,'n':len(df),'b0':round(m.params.w0,2),'b1':round(m.params.w1,2),'b2':round(m.params.w2,2),'soma':round(m.params[['w0','w1','w2']].sum(),2),'r2':round(m.rsquared,2),'up':round(m2.params.up,2),'dn':round(m2.params.dn,2),'p_asym':round(float(m2.t_test('up - dn = 0').pvalue),3)}
    df['k']=k;pool.append(df)
pl=pd.concat(pool);m=sm.OLS(pl.y,sm.add_constant(pl[['w0','w1','w2']])).fit();m2=sm.OLS(pl.y,sm.add_constant(pl[['up','dn','w1']])).fit()
pt['pool']={'n':len(pl),'b0':round(m.params.w0,2),'b1':round(m.params.w1,2),'b2':round(m.params.w2,2),'soma':round(m.params[['w0','w1','w2']].sum(),2),'r2':round(m.rsquared,2),'up':round(m2.params.up,2),'dn':round(m2.params.dn,2),'p_asym':round(float(m2.t_test('up - dn = 0').pvalue),3)}
R['pt']=pt;print(pd.DataFrame(pt).T.to_string())
# ---------- ENSO
oni=S([d['oni'].get(m) for m in M])
R['oni']=[None if pd.isna(x) else x for x in oni]
lr=np.log(real);sa=lr-lr.groupby(lr.index.month).transform('mean')   # desvio do padrão sazonal (2012-2026)
ph=pd.cut(oni,[-9,-0.5,0.5,9],labels=['La Niña','Neutro','El Niño'],right=False)
en={}
for lag in [0,3,6]:
    x=oni.shift(lag);p=ph.shift(lag);df=pd.DataFrame({'sa':sa,'p':p,'o':x}).dropna()
    g=df.groupby('p').sa.agg(['mean','count']);en[lag]={'media':{k:round((np.exp(v)-1)*100,1) for k,v in g['mean'].items()},'n':g['count'].to_dict(),'corr':round(df.sa.corr(df.o),2)}
    mm=sm.OLS(df.sa,sm.add_constant(df.o)).fit(cov_type='HAC',cov_kwds={'maxlags':12});en[lag]['beta']=round(mm.params.o*100,1);en[lag]['p']=round(mm.pvalues.o,3)
R['enso']=en;print(json.dumps(en,ensure_ascii=False))
strong=df=pd.DataFrame({'sa':sa,'o':oni});print('ONI>=1.5:',round((np.exp(df[df.o>=1.5].sa.mean())-1)*100,1),int((df.o>=1.5).sum()),' ONI<=-1:',round((np.exp(df[df.o<=-1].sa.mean())-1)*100,1),int((df.o<=-1).sum()))
R['enso_forte']={'el':round((np.exp(df[df.o>=1.5].sa.mean())-1)*100,1),'n_el':int((df.o>=1.5).sum()),'la':round((np.exp(df[df.o<=-1].sa.mean())-1)*100,1),'n_la':int((df.o<=-1).sum())}
# volatilidade por fase
dv=pd.DataFrame({'v':var.abs(),'p':ph}).dropna().groupby('p').v.mean().round(1);print('|var| por fase',dv.to_dict());R['enso_vol']=dv.to_dict()
# produtividade anual x ONI
pam=d['pam']['Brasil'];yl={int(y):v for y,v in pam['112'].items()};pr={int(y):v for y,v in pam['214'].items()};ar={int(y):v for y,v in pam['216'].items()}
R['pam_br']={'anos':sorted(yl),'rend':[yl[y] for y in sorted(yl)],'prod':[pr[y] for y in sorted(yl)],'area':[ar[y] for y in sorted(yl)],'valor':[pam['215'][str(y)] for y in sorted(yl)]}
R['oni_ano']={int(y):round(v,2) for y,v in oni.groupby(oni.index.year).mean().items()}
# ---------- custos
ptax=pd.Series({pd.Period(x['data'][6:]+'-'+x['data'][3:5],'M'):float(x['valor']) for x in json.load(open('dados/brutos/ptax.json'))}).reindex(ix)
R['ptax']=ptax.round(3).tolist()
wb={}
for k,v in d['wb'].items():
    s=S(v);wb[k]={'usd':s.round(1).tolist(),'brl_real':(s*ptax*defl).round(0).tolist()}
R['wb']=wb
u=S(d['wb']['Urea'])*ptax*defl;print('ureia R$ real: media 2015-19',u['2015':'2019'].mean().round(0),'pico',u.idxmax(),u.max().round(0),'ultimo',u.iloc[-1].round(0),'brent ult',d['wb']['Crude oil, Brent'][-3:],'ptax ult',ptax.iloc[-1])
fert=(S(d['wb']['Urea'])+S(d['wb']['DAP'])+S(d['wb']['Potassium chloride']))/3*ptax*defl
R['fert_idx']=(fert/fert['2015'].mean()*100).round(0).tolist()
for lag in [0,6,12]: print('corr ln real tomate (12m ma) x fert lag',lag,round(np.log(real.rolling(12).mean()).corr(np.log(fert.rolling(12).mean()).shift(lag)),2))
R['corr_fert']={lag:round(np.log(real.rolling(12).mean())['2015':].corr(np.log(fert.rolling(12).mean()).shift(lag)['2015':]),2) for lag in [0,6,12]}
# ---------- quantidade x preço (CEASAs)
Q=pd.DataFrame({pd.Period(f"{m[:4]}-{m[4:]}",'M'):v for m,v in c['Q'].items()}).T.sort_index()
qc=['SP','BH','RJ','ES','PE','CE'];Qt=Q[qc].dropna().sum(axis=1)
pm=np.log(Wr[qc].reindex(Qt.index).mean(axis=1));df=pd.DataFrame({'dp':pm.diff(),'dq':np.log(Qt).diff()}).dropna()
m=sm.OLS(df.dp,sm.add_constant(df.dq)).fit();print('flexibilidade preço-quantidade',round(m.params.dq,2),'r2',round(m.rsquared,2),'n',len(df),'p',round(m.pvalues.dq,4))
R['flex']={'b':round(m.params.dq,2),'r2':round(m.rsquared,2),'n':len(df),'ceasas':qc}
R['q']={'months':[str(p) for p in Qt.index],'t':(Qt/1e6).round(1).tolist(),'p':np.exp(pm).round(2).tolist()}
print('Q set/26 vs set/25',round((Qt['2026-09']/Qt['2025-09']-1)*100,1),'jan-set 26 vs 25',round((Qt['2026-01':'2026-09'].sum()/Qt['2025-01':'2025-09'].sum()-1)*100,1))
R['q_var']={'set':round((Qt['2026-09']/Qt['2025-09']-1)*100,1),'jan_set':round((Qt['2026-01':'2026-09'].sum()/Qt['2025-01':'2025-09'].sum()-1)*100,1)}
# deriva de encadeamento: atacado x IPCA regional, média 2016 -> média jan-set 2026
dr={}
for k,a in pairs.items():
    rt=S(d['ipca'][a]['it']);w=W[k]
    if w['2016'].notna().sum()>=10 and w['2026'].notna().sum()>=6:
        dr[k]={'area':a,'atacado':round((w['2026-01':'2026-09'].mean()/w['2016'].mean()-1)*100,0),'ipca':round((rt['2026-01':'2026-09'].mean()/rt['2016'].mean()-1)*100,0)}
R['deriva']=dr;print(pd.DataFrame(dr).T.to_string());print('geral 2016->2026',round((ig['2026-01':'2026-09'].mean()/ig['2016'].mean()-1)*100,0))
R['deriva_geral']=round((ig['2026-01':'2026-09'].mean()/ig['2016'].mean()-1)*100,0)
# origem
uf=[(r[8],r[9]) for r in c['UF']['202609'][5:] if r[8] and isinstance(r[9],(int,float))];R['origem']={'mes':'2026-09','uf':uf}
# ---------- projeção
y=np.log(real);H=26
best=None
for order in [(1,0,0),(1,0,1),(2,0,0),(2,0,1)]:
    for so in [(1,0,0,12),(0,1,1,12),(1,0,1,12)]:
        try:
            r=SARIMAX(y,order=order,seasonal_order=so,trend='c' if so[1]==0 else None).fit(disp=0)
            if best is None or r.aic<best[0]: best=(r.aic,order,so,r)
        except Exception as e: pass
print('modelo',best[1],best[2],'AIC',round(best[0],1));r=best[3];print(r.params.round(3).to_dict())
f=r.get_forecast(H);mu=f.predicted_mean;ci80=f.conf_int(alpha=0.2);ci50=f.conf_int(alpha=0.5)
# backtest: origem dez/2024, 22 passos
tr=y[:'2024-10'];rb=SARIMAX(tr,order=best[1],seasonal_order=best[2],trend='c' if best[2][1]==0 else None).fit(disp=0);fb=rb.get_forecast(24);e=(np.exp(fb.predicted_mean)/np.exp(y['2024-11':])-1).abs()*100
cib=fb.conf_int(alpha=0.2);cov=((y['2024-11':]>=cib.iloc[:,0])&(y['2024-11':]<=cib.iloc[:,1])).mean()
naive=(np.exp(y.shift(12)['2024-11':])/np.exp(y['2024-11':])-1).abs()*100
print('backtest 24m MAPE',e.mean().round(1),'cobertura 80%',round(cov*100),'ingenuo sazonal',naive.mean().round(1))
R['proj']={'modelo':f"SARIMA{best[1]}x{best[2]}",'months':[str(p) for p in mu.index],'base':np.exp(mu).round(1).tolist(),'lo80':np.exp(ci80.iloc[:,0]).round(1).tolist(),'hi80':np.exp(ci80.iloc[:,1]).round(1).tolist(),'lo50':np.exp(ci50.iloc[:,0]).round(1).tolist(),'hi50':np.exp(ci50.iloc[:,1]).round(1).tolist(),'bt_mape':round(e.mean(),1),'bt_cov':round(cov*100),'bt_naive':round(naive.mean(),1)}
pj=pd.DataFrame({'base':np.exp(mu),'lo':np.exp(ci80.iloc[:,0]),'hi':np.exp(ci80.iloc[:,1])})
for y_ in [2027,2028]:
    s=pj.loc[str(y_)].mean();print(y_,s.round(1).to_dict(),'vs media 2015-26',round(real['2015':].mean(),1),'vs 2026',round(real['2026'].mean(),1))
R['proj_ano']={y_:pj.loc[str(y_)].mean().round(1).to_dict() for y_ in [2027,2028]};R['real_med']=round(real['2015':].mean(),1);R['real_2026']=round(real['2026'].mean(),1);R['real_2025']=round(real['2025'].mean(),1)
print(pj.iloc[[1,2,5,8,11,14,20,25]].round(1).to_string())
# fator atacado: R$/kg composto por ponto do índice real
k=(comp/real.reindex(comp.index)).dropna()['2023':].mean();R['k_atacado']=round(k,4);print('R$/kg por ponto de indice',round(k,4))
json.dump(R,open('dados/processados/analysis.json','w'),ensure_ascii=False,default=lambda o: o.item() if hasattr(o,'item') else str(o))
