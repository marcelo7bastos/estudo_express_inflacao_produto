import re,subprocess,glob,json,os,unicodedata,warnings,datetime,collections
warnings.filterwarnings('ignore')
import openpyxl
MES={'janeiro':1,'fevereiro':2,'marco':3,'maro':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
AB=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
def na(s): return unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
def canon(n):
    n=na(n)
    for k,pats in {'SP':['ceagesp','grande sp'],'Campinas':['campinas'],'BH':['ceasaminas','grande bh'],'RJ':['/rj','grande rio'],'ES':['/es','vitoria'],'PR':['/pr','curitiba'],'SC':['/sc','sao jose'],'RS':['/rs','porto alegre'],'GO':['/go','goiania'],'DF':['/df','brasilia'],'PE':['/pe','recife'],'CE':['/ce','fortaleza'],'AC':['/ac','rio branco']}.items():
        if any(p in n for p in pats): return k
    return None
def fl(t):
    t=str(t).replace('%','').replace('.','').replace(',','.')
    try: return float(t)
    except: return None
def txt(f):
    c=f+'.txt'
    if not os.path.exists(c) or os.path.getsize(c)==0: subprocess.run(['pdftotext','-layout',f,c],stderr=subprocess.DEVNULL)
    return open(c,errors='ignore').read() if os.path.exists(c) else ''
P=collections.defaultdict(dict)   # month -> ceasa -> (price, source-rank)
def put(m,c,p,rank,src):
    if p is None or c is None or not (0.2<p<40): return
    if c not in P[m] or P[m][c][1]<rank: P[m][c]=(round(p,3),rank,src)
log=[]
def bmy(b):
    m=re.search(r'(janeiro|fevereiro|marco|maro|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)',b); y=re.match(r'(\d{4})_',b)
    return (MES[m.group(1)],int(y.group(1))) if m and y else (None,None)
def prev(y,m,k=1):
    i=y*12+m-1-k; return i//12,i%12+1
for f in sorted(glob.glob('dados/brutos/conab/pdf/*.pdf')):
    b=na(os.path.basename(f)); bm,by=bmy(b)
    if not bm or 'pescado' in b: log.append(('skip',b)); continue
    ry,rm=prev(by,bm); key=f"{ry}{rm:02d}"; pk="%d%02d"%prev(by,bm,2)
    L=txt(f).split('\n');found=False
    for i,l in enumerate(L):
        n=na(l)
        if 'alface' in n and 'tomate' in n and 'batata' in n and len(n.split())<=8:
            prods=[w for w in n.split() if w in('alface','tomate','batata','cebola','cenoura')]
            if len(prods)<4: continue
            k=prods.index('tomate')
            for l2 in L[i+1:i+30]:
                n2=na(l2).strip()
                if n2.startswith('fonte'): break
                mt=re.match(r'^(cea.*?)\s+((?:\*|-?\d+,\d+)(?:\s.*)?)$',n2)
                if not mt or not canon(mt.group(1)): continue
                toks=mt.group(2).split(); vals=[];j=0
                while j<len(toks) and len(vals)<len(prods):
                    if toks[j] in('*','-','s/c','n/d'): vals.append((None,None)); j+=1; 
                    else:
                        vals.append((fl(toks[j]),fl(toks[j+1]) if j+1<len(toks) else None)); j+=2
                if len(vals)<=k: continue
                p,pc=vals[k]; c=canon(mt.group(1))
                put(key,c,p,2,b); found=True
                if p and pc is not None and pc>-95: put(pk,c,p/(1+pc/100),1,b+' (derivado da variação)')
            if found: break
        # formato transposto de 2015
        if n.strip().startswith('produtos') and ('grande' in n or 'ceasa' in n or 'goiania' in n):
            names=[('grande vitoria','ES'),('grande bh','BH'),('grande rio','RJ'),('grande sp','SP'),('campinas','Campinas'),('curitiba','PR'),('goiania','GO'),('brasilia','DF'),('fortaleza','CE'),('recife','PE')]
            cols=[c for pos,c in sorted((n.find(a),c) for a,c in names if a in n)]
            for l2 in L[i+1:i+10]:
                if na(l2).strip().startswith('tomate'):
                    toks=l2.split()[1:]
                    if len(toks)!=2*len(cols): break
                    for j,cc in enumerate(cols):
                        p=fl(toks[2*j]);pc=fl(toks[2*j+1])
                        put(key,cc,p,2,b); found=True
                        if p and pc is not None and pc>-95: put(pk,cc,p/(1+pc/100),1,b+' (derivado da variação)')
    if not found: log.append(('semtabela',b))
# planilhas
Q=collections.defaultdict(dict); MP={}; UF={}
for f in sorted(glob.glob('dados/brutos/conab/pdf/*.xlsx'),key=lambda f:(bmy(na(os.path.basename(f)))[1] or 0,bmy(na(os.path.basename(f)))[0] or 0)):
    b=na(os.path.basename(f)); bm,by=bmy(b)
    if not bm:
        mm=re.search(r'(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)z?(\d{4})',b.replace('-','').replace('z',''))
        if mm: bm,by=MES[mm.group(1)],int(mm.group(2))
        else: log.append(('xlsx?',b)); continue
    ry,rm=prev(by,bm); key=f"{ry}{rm:02d}"
    try: wb=openpyxl.load_workbook(f,data_only=True)
    except Exception as e: log.append(('xlsxerr',b,str(e)[:40])); continue
    for ws in wb.worksheets:
        t=na(ws.title); R=list(ws.iter_rows(values_only=True))
        if t=='precos-tomate':
            for i,r in enumerate(R):
                if r and na(r[0]).strip()=='ceasa':
                    dates=[(j,c) for j,c in enumerate(r) if isinstance(c,datetime.datetime)]
                    for r2 in R[i+1:i+20]:
                        if r2[0] and canon(r2[0]):
                            for j,d in dates:
                                v=r2[j]
                                if isinstance(v,(int,float)): put(f"{d.year}{d.month:02d}",canon(r2[0]),float(v),3+ (by*12+bm)/1e5,b)
                    break
        elif t=='precos-hortalicas':
            hdr=None
            for i,r in enumerate(R):
                if r and na(r[0]).strip()=='produto': hdr=[na(c).strip() if c else None for c in r]; k=hdr.index('tomate')
                elif hdr and r and r[0]:
                    v=r[k] if isinstance(r[k],(int,float)) else None
                    if 'media ponderada' in na(r[0]): MP[key]=(round(v,3) if v else None, r[k+1] if isinstance(r[k+1],(int,float)) else None)
                    elif canon(r[0]) and v: put(key,canon(r[0]),float(v),2.5,b)
        elif t=='quantidade-tomate':
            for i,r in enumerate(R):
                if r and na(r[0]).strip()=='ceasa':
                    heads=[na(c) for c in r[1:4]]
                    for r2 in R[i+1:i+20]:
                        if r2[0] and canon(r2[0]):
                            for h,v in zip(heads,r2[1:4]):
                                mm=re.match(r'([a-z]+) de (\d{4})',h)
                                if mm and isinstance(v,(int,float)) and mm.group(1) in MES: Q[f"{mm.group(2)}{MES[mm.group(1)]:02d}"][canon(r2[0])]=v
                    break
        elif t=='uf-hortalicas':
            UF[key]=[[ (round(c,4) if isinstance(c,float) else (str(c) if c is not None and not isinstance(c,(int,str)) else c)) for c in r[:14]] for r in R[:45]]
months=sorted(P)
print(len(months),months[0],months[-1]); miss=[f"{y}{m:02d}" for y in range(2015,2027) for m in range(1,13) if f"{y}{m:02d}" not in P and f"{y}{m:02d}"<='202609']; print('faltam',miss)
cnt=collections.Counter(c for m in P for c in P[m]); print(cnt)
for x in log: print(x)
print('MP',len(MP),sorted(MP.items())[-4:]); print('Q',len(Q),sorted(Q)[:2],sorted(Q)[-2:]); print('UF',sorted(UF)[-3:])
json.dump({'P':P,'MP':MP,'Q':Q,'UF':UF},open('dados/processados/conab.json','w'),ensure_ascii=False)
