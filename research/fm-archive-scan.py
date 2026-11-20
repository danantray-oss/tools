#!/usr/bin/env python3
"""Offline-snapshot 14-day UK contract-award opportunity census (public notices).
Downloaded from Crown Commercial Service daily archives described in data.gov.uk.
Output is not a list of verified recruitment opportunities: independent hiring evidence
must be reviewed separately. All ambiguity and missing files are explicitly recorded.
"""
import csv,io,zipfile,xml.etree.ElementTree as ET,urllib.request,urllib.error,json,re,os,datetime,collections,time
START=datetime.date(2026,11,5); STOP=datetime.date(2026,11,18)
out='research/fm-archive-results';os.makedirs(out,exist_ok=True)
ckan='https://ckan.publishing.service.gov.uk/api/3/action/package_show?id='
sources={'FTS':'8570ac2d-9bb5-415c-83e8-d860b6e67c4d','CF':'d5038a31-8666-4d6f-8d4d-7de87ed650e7'}
heads={'User-Agent':'public-contracts-backtest/1.0','Accept':'*/*'}
def get(u):
  for i in range(3):
    try:
      with urllib.request.urlopen(urllib.request.Request(u,headers=heads),timeout=70) as r:return r.read()
    except Exception as e:
      if i==2:raise
      time.sleep(i+1)
def local(e):return e.tag.rsplit('}',1)[-1] if '}' in e.tag else e.tag
def flatten(e):return ' '.join(x.strip() for x in e.itertext() if x and x.strip())
def nl(x):return re.sub(r'\s+',' ',str(x or '')).strip()
money=lambda x:float(str(x).replace(',','')) if str(x or '').replace('.','',1).replace(',','').isdigit() else 0.
hard=re.compile(r'facilities management|facility management|hard fm|integrated fm|building (?:services|maintenance)|planned preventative maintenance|mechanical and electrical|hvac|air.conditioning|chiller|lift(?:s)? (?:maintenance|refurbishment|repair|servicing)|fire (?:alarm|safety|protection|systems)|gas (?:servicing|maintenance|engineering)|heating (?:maintenance|installation|servicing|repair)|electrical (?:maintenance|testing|installation)|property maintenance|estates maintenance|plant maintenance|commercial maintenance|legionella',re.I)
adj=re.compile(r'maintenance|mechanical|electrical|boiler|refurbish|heating|building services|facilities|lift|air.condition',re.I)
soft=re.compile(r'cleaning|catering|grounds maintenance|pest control|waste collection|security guarding|landscaping|laundry',re.I)
digital=re.compile(r'software|licen[cs](?:e|ing)|digital platform|information management system|saas|cloud hosted',re.I)
monthdates=[START+datetime.timedelta(days=i) for i in range((STOP-START).days+1)]
archivedays=[]; fts=[]; cf=[]; errors=[];types=collections.Counter()
meta={}
for source,id in sources.items():
  try:meta[source]=json.loads(get(ckan+id))['result']['resources']
  except Exception as e:meta[source]=[];errors.append(source+' manifest '+repr(e))
for day in monthdates:
  date=day.isoformat()
  d=day.day; suffix='th' if 11<=d%100<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10,'th')
  for source in ['FTS','CF']:
    target=f'{d}{suffix} November 2026' if source=='FTS' else date
    matches=[r for r in meta[source] if r.get('name','').rsplit(' - ',1)[-1]==target]
    if len(matches)!=1:
      archivedays.append({'source':source,'day':date,'status':'MISSING_FROM_MANIFEST','files':0,'records':0,'source_url':''})
      errors.append(f'{source} {date} missing manifest resource')
      continue
    r=matches[0]; u=r['url']
    try:
      b=get(u)
      if source=='FTS':
        z=zipfile.ZipFile(io.BytesIO(b))
        names=[n for n in z.namelist() if n.lower().endswith('.xml')];count=0;found=0
        for filename in names:
          count+=1
          try:root=ET.fromstring(z.read(filename))
          except Exception as e:errors.append(f'XML {filename} {repr(e)}');continue
          fs=[el for el in root.iter() if local(el)=='FORM_SECTION']
          form=local(list(fs[0])[0]) if fs and list(fs[0]) else 'UNKNOWN'
          types[form]+=1
          if not (form.startswith(('UK6','UK7','F03','F06','F13','F15')) or 'AWARD' in form):continue
          titles=[]
          # For TED legacy and modern forms, contract title usually first TITLE under OBJECT_CONTRACT.
          for e in root.iter():
            k=local(e)
            if k in ('TITLE','PROCUREMENT_TITLE','CONTRACT_TITLE','TITLE_CONTRACT','TITLE_OF_CONTRACT'):
              txt=nl(flatten(e))
              if 7<len(txt)<450:titles.append(txt)
          # Keep the first specific title. Later titles may be individual lots.
          title=titles[0] if titles else ''
          raw=nl(flatten(root))
          # Candidate flag permits full text fallback, but retains source for manual triage.
          match=bool(hard.search(' '.join(titles[:6])+' '+raw[:3000]))
          if not match:continue
          found+=1
          value_strings=[]
          for el in root.iter():
            k=local(el)
            if any(x in k for x in ('VALUE','VAL_TOTAL','AMOUNT','PRICE')):
              tx=nl(flatten(el))
              if tx and re.search(r'\d',tx) and len(tx)<30:value_strings.append(tx)
          code=filename.rsplit('/',1)[-1].replace('.xml','')
          candidate={'source':'FTS_ARCHIVE','day':date,'notice_id':code,'form':form,'title':title,
               'additional_titles':' | '.join(titles[1:4])[:400],
               'buyer':'','supplier':'UNVERIFIED_IN_XML','award_value':'','award_amount_basis':'UNPARSED_XML',
               'contract_start':'','evidence':'https://www.find-tender.service.gov.uk/Notice/'+code,
               'source_archive':u,'match_context':raw[:1100],
               'potential_technical_fm':bool(match),'weakness':'Supplier/value/contract stage and recruitment demand need verification',
               'value_fragments':' | '.join(value_strings[:4])}
          fts.append(candidate)
        archivedays.append({'source':source,'day':date,'status':'OK','files':len(names),'records':count,'suspects':found,'source_url':u})
        print('DAY',date,source,'files',len(names),'suspects',found,flush=True)
      else:
        text=b.decode('utf-8-sig','replace')
        reader=csv.DictReader(io.StringIO(text))
        count=0;found=0
        for x in reader:
          count+=1
          tag=x.get('releases/0/tag/0','')
          if tag not in ('award','contract'):continue
          title=nl(x.get('releases/0/tender/title') or x.get('releases/0/title'))
          desc=nl(x.get('releases/0/tender/description'))
          award_value=money(x.get('releases/0/awards/0/value/amount'))
          est=money(x.get('releases/0/tender/value/amount'))
          suppliers=[v for k,v in x.items() if re.search(r'releases/0/awards/0/suppliers/\d+/name$',k) and v]
          cpv=x.get('releases/0/tender/classification/id','')
          match=bool(hard.search(title+' '+desc[:1000]) or cpv.startswith(('507','79993')))
          if not match:continue
          found+=1
          docs=[v for k,v in x.items() if re.search(r'releases/0/awards/0/documents/\d+/url$',k) and v]
          rec={'source':'CF_ARCHIVE','day':date,'notice_id':x.get('releases/0/id',''),
              'form':tag,'title':title,'additional_titles':'','buyer':x.get('releases/0/parties/0/name',''),
              'supplier':' / '.join(suppliers) or 'UNVERIFIED','award_value':award_value,'award_amount_basis':'award' if award_value else 'NO_AWARD_VALUE',
              'contract_start':x.get('releases/0/awards/0/contractPeriod/startDate',''),
              'evidence':docs[0] if docs else x.get('uri',''),'source_archive':u,
              'match_context':desc[:1100],'potential_technical_fm':bool(match),'weakness':'Verify no framework-only, contract timing and hiring',
              'value_fragments':str(est) if est else ''}
          cf.append(rec)
        archivedays.append({'source':source,'day':date,'status':'OK','files':1,'records':count,'suspects':found,'source_url':u})
        print('DAY',date,source,'records',count,'suspects',found,flush=True)
    except Exception as e:
      archivedays.append({'source':source,'day':date,'status':'FETCH_OR_PARSE_FAILURE','files':0,'records':0,'source_url':u})
      errors.append(f'{source} {date}: '+repr(e))
      print('DAY_ERROR',source,date,repr(e),flush=True)
def writecsv(path,records):
  if not records:return
  fields=list(records[0])
  with open(out+'/'+path,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records)
writecsv('daily_coverage.csv',archivedays)
writecsv('fts_potential_awards.csv',fts)
writecsv('cf_potential_awards.csv',cf)
allrec=fts+cf
unique={}
for r in allrec:unique[(r['source'],r['notice_id'])]=r
allrec=list(unique.values())
for r in allrec:
  title=r['title']; descr=r.get('match_context','')
  r['screening_exclusion']=''
  if digital.search(title):r['screening_exclusion']='Software/digital service'
  elif (soft.search(title) or re.search(r'soft fm|waste|building materials|consultancy|engineering facility|management system|portfolio management',title,re.I)) and not re.search(r'(?:gas|lift|electrical|mechanical|building) maintenance',title,re.I):r['screening_exclusion']='Soft-FM, materials, software or consultancy rather than technical FM'
  elif r['source']=='CF_ARCHIVE' and (not isinstance(r['award_value'],(int,float)) or r['award_value']<250000):r['screening_exclusion']='Award value below threshold or unavailable'
  elif r['source']=='CF_ARCHIVE' and r['supplier']=='UNVERIFIED':r['screening_exclusion']='Supplier missing'
  elif r['source']=='FTS_ARCHIVE':r['screening_exclusion']='Needs structured manual value and supplier verification'
  elif 'framework' in title.lower():r['screening_exclusion']='Framework-only status needs investigation'
qualified=[r for r in allrec if not r['screening_exclusion']]
writecsv('all_potential_awards.csv',allrec)
writecsv('cf_automatically_screened.csv',qualified)
summary={'window':[str(START),str(STOP)],'source_coverage':archivedays,
    'files_downloaded':sum(r['files'] for r in archivedays if r['status']=='OK'),
    'notices_screened':sum(r['records'] for r in archivedays if r['status']=='OK'),
    'fts_potential_award_notices':len(fts),'cf_potential_award_notices':len(cf),
    'cf_screened_candidates':len(qualified),
    'fts_source_notice_types':types,'errors':errors,
    'all_sources_complete':not errors and all(r['status']=='OK' for r in archivedays),
    'hiring_linked_verified':0,'conclusion':'This is a supply scan; no verified recruitment need or buyer payment established.'}
with open(out+'/summary.json','w') as f:json.dump(summary,f,indent=2,default=str)
print('FINAL_ARCHIVE_SUMMARY',json.dumps({k:v for k,v in summary.items() if k not in ('source_coverage','fts_source_notice_types')})[:5000],flush=True)
print('FTS_FORMS',dict(types.most_common(15)),flush=True)
for r in sorted(qualified,key=lambda x:x['award_value'],reverse=True)[:45]:
  print('CF_CANDIDATE',r['day'],round(r['award_value']),'|',r['supplier'][:45],'|',r['title'][:75],'|',r['evidence'][:120],flush=True)
for r in fts[:45]:
  print('FTS_SUSPECT',r['day'],r['notice_id'],'|',r['title'][:75],flush=True)
