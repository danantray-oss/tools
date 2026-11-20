#!/usr/bin/env python3
"""Enrich all Find a Tender technical FM candidates from original XML.
No recruitment need inferred. Value field distinguishes award and signed contract.
"""
import csv,io,urllib.request,xml.etree.ElementTree as ET,zipfile,datetime,os,re,json,collections,time
ROOT='research/fm-archive-results'
def readcsv(name):
 with open(ROOT+'/'+name,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
base=readcsv('fts_potential_awards.csv')
byday=collections.defaultdict(list)
for r in base:byday[r['day']].append(r)
def loc(x):return x.tag.rsplit('}',1)[-1]
def child(root,tag):
 return next((x for x in root if loc(x)==tag),None) if root is not None else None
def children(root,tag):
 return [x for x in root if loc(x)==tag] if root is not None else []
def get(root,*tags):
 p=root
 for tag in tags:p=child(p,tag)
 return (p.text or '').strip() if p is not None else ''
def fl(x):
 return re.sub(r'\s+',' ',' '.join((a.text or '').strip() for a in x.iter() if a.text and a.text.strip())) if x is not None else ''
def amount(x):
 try:return float(x)
 except:return 0
def download(url):
 for i in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'UK public procurement audit'})
   with urllib.request.urlopen(req,timeout=75) as f:return f.read()
  except Exception as e:
   if i==2:raise
   time.sleep(i+1)
results=[]
for day, records in sorted(byday.items()):
 url=records[0]['source_archive'];z=zipfile.ZipFile(io.BytesIO(download(url)));errors=0
 for raw in records:
  id=raw['notice_id']
  try:
   root=ET.fromstring(z.read(id+'.xml'))
   sec=child(root,'FORM_SECTION')
   form=next(iter(sec)) if sec is not None and len(sec) else None
   label=loc(form) if form is not None else ''
   tender=child(form,'tender')
   buyer=child(form,'buyer')
   parties=children(form,'parties')
   supplierparties=[p for p in parties if 'supplier' in [x.text for x in children(p,'roles')]]
   awards=children(form,'awards')
   contracts=children(form,'contracts')
   award=awards[0] if awards else None
   contract=contracts[0] if contracts else None
   ids=[get(x,'id') for x in children(award,'suppliers')]
   winners=[get(p,'name') for p in supplierparties if get(p,'id') in ids] if ids else [get(p,'name') for p in supplierparties]
   awvalue=amount(get(award,'value','amount'))
   covalue=amount(get(contract,'value','amount'))
   mainvalue=covalue or awvalue
   valuebasis='signed_contract' if covalue and get(contract,'dateSigned') else 'contract' if covalue else 'award' if awvalue else 'unknown'
   title=get(tender,'title') or get(contract,'title') or raw['title']
   description=get(tender,'description') or get(award,'description') or ''
   awarddesc=get(award,'description')
   procurement=get(tender,'procurementMethodDetails')
   sign=get(contract,'dateSigned')
   cstatus=get(contract,'status')
   astatus=get(award,'status')
   supplier='; '.join(filter(None,winners))
   # Legacy F03 uses nested format, no modern awards; original full text retained, not counted as verified winner
   ex=[]
   if not supplier:ex.append('no structured winning supplier (legacy XML may need manual parsing)')
   if mainvalue<250000:ex.append('value missing or below £250k')
   if not title:ex.append('no specific title')
   if re.search(r'cleaning|catering|landscap|pest control|waste|software|digitis|consultancy|consulting|building materials',title,re.I):ex.append('outside initial technical FM niche')
   if re.search(r'one.off|single refurbishment|minor works|new build|installation only',title,re.I):ex.append('one-off project, staffing trigger uncertain')
   if astatus=='pending' and cstatus!='active':ex.append('award pending signed contract')
   if cstatus and cstatus not in ('active','complete'):ex.append('contract not active')
   # Score stage 1 technical/service. A named award is a contract signal, not direct verified staffing demand.
   relevant=bool(re.search(r'facilit(?:y|ies) management|building maintenance|planned preventative|reactive maintenance|lift.*mainten|lift.*refurbish|fire system|fire safety|boiler|gas servicing|electrical maintenance|mechanical maintenance|water hygiene|engineering maintenance|air conditioning|hvac|heating maintenance',title+' '+description[:400],re.I))
   if not relevant:ex.append('no clear hard-FM delivery title')
   rec={
    'day':day,'notice_id':id,'notice_form':label,'buyer':get(buyer,'name'),
    'supplier':supplier,'title':title,'description':description[:330],
    'award_status':astatus,'contract_status':cstatus,'date_signed':sign,
    'amount_gbp':mainvalue,'amount_basis':valuebasis,
    'procurement_method':procurement,'award_value_gbp':awvalue,'contract_value_gbp':covalue,
    'contract_start':get(contract,'period','startDate') or get(award,'contractPeriod','startDate'),
    'notice_url':raw['evidence'],'source_archive':url,'operational_relevance':relevant,
    'screening_result':'REVIEW' if not ex else 'EXCLUDE_OR_VERIFY',
    'reasons':'; '.join(ex),'hiring_linked_verified':False
   }
   results.append(rec)
  except Exception as e:
   results.append({'day':day,'notice_id':id,'notice_url':raw['evidence'],
    'screening_result':'PARSE_ERROR','reasons':repr(e),'hiring_linked_verified':False})
   errors+=1
 print('ENRICHED_DAY',day,'records',len(records),'errors',errors,flush=True)
fields=['day','notice_id','notice_form','buyer','supplier','title','description','award_status','contract_status','date_signed','amount_gbp','amount_basis','procurement_method','award_value_gbp','contract_value_gbp','contract_start','notice_url','source_archive','operational_relevance','screening_result','reasons','hiring_linked_verified']
with open(ROOT+'/fts_enriched.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(results)
review=[r for r in results if r.get('screening_result')=='REVIEW']
with open(ROOT+'/fts_review_priority.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(review)
summary={'source_candidates':len(base),'enriched':len(results),'review_priority':len(review),
  'verified_hiring_linked':0,'parse_errors':[x['notice_id'] for x in results if x.get('screening_result')=='PARSE_ERROR'],
  'stage_counts':dict(collections.Counter((x.get('award_status'),x.get('contract_status')) for x in results))}
with open(ROOT+'/enrichment_summary.json','w') as f:json.dump(summary,f,indent=2,default=str)
print('ENRICHMENT_SUMMARY',json.dumps(summary),flush=True)
for x in sorted(review,key=lambda r:-r['amount_gbp']):
 print('REVIEW',x['day'],x['notice_id'],int(x['amount_gbp']),x['buyer'][:35],'|',x['supplier'][:44],'|',x['title'][:85],'|',x['award_status'],x['contract_status'],x['date_signed'],flush=True)
