#!/usr/bin/env python3
"""Retrospective UK FM contract intelligence scan. Public notices only.
All counted releases preserve source, date, ocid, original release and award.
No employer hiring claim is made without independent external verification.
"""
import csv, json, os, re, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
START = "2026-11-05T00:00:00"
END = "2026-11-18T23:59:59"
os.makedirs("research/fm-output",exist_ok=True)
base = "research/fm-output"
headers={"User-Agent":"FM-opportunity-research/0.1 (public-data analysis)","Accept":"application/json"}
totals={}
errors=[]
def fetch(url):
    for attempt in range(5):
        try:
            req=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req,timeout=55) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body=e.read(300).decode("utf8","replace")
            if e.code in (429,500,502,503,504) and attempt<4:
                time.sleep(min(25,3*(attempt+1)));continue
            raise RuntimeError("HTTP "+str(e.code)+" "+body+" URL "+url[:180])
        except Exception:
            if attempt<4:
                time.sleep(2*(attempt+1));continue
            raise
def collect(source,endpoint,params):
    url=endpoint+"?"+urllib.parse.urlencode(params)
    seen=set(); out=[]; pages=0
    while url and pages<300:
        if url in seen: errors.append(source+" pagination cycle");break
        seen.add(url)
        try: data=fetch(url)
        except Exception as e:
            errors.append(source+" "+str(e)[:350]);break
        releases=data.get("releases",[])
        out.extend(releases);pages+=1
        nxt=data.get("links",{}).get("next")
        if pages%10==0: print("PROGRESS",source,"pages",pages,"releases",len(out),flush=True)
        url=nxt if releases else None
        if not nxt and len(releases)>=100: errors.append(source+" full page without continuation")
        if not nxt:break
        time.sleep(.12)
    if url and pages>=300:errors.append(source+" exceeded 300 pages")
    totals[source]={"pages":pages,"releases":len(out),"complete":not any(x.startswith(source) for x in errors)}
    print("TOTAL",source,totals[source],flush=True)
    return out
fts=collect("FTS","https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages",{
    "updatedFrom":START,"updatedTo":END,"limit":100})
cf=collect("CF","https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search",{
    "publishedFrom":START+"Z","publishedTo":END+"Z","size":100})
def cpvs(tender):
    codes=[]
    for i in tender.get("items",[]) or []:
        arr=[i.get("classification")]+(i.get("additionalClassifications") or [])
        for c in arr:
            if isinstance(c,dict) and c.get("id"): codes.append(str(c["id"]))
    return sorted(set(codes))
strong=re.compile(r"facilit(?:y|ies) management|hard fm|building (?:services|maintenance)|planned preventative maintenance|m\s*&\s*e(?:lectrical)?\b|mechanical and electrical|heating (?:maintenance|service|repair|system)|boiler (?:maintenance|service)|hvac|air conditioning|chiller|lift(?:s)? (?:maintenance|repair|refurbishment|servicing)|elevator|fire (?:alarm|safety|protection|systems)|water hygiene|legionella|electrical (?:maintenance|testing|installation|servicing)|gas (?:servicing|maintenance|engineering)|property maintenance|estate(?:s)? maintenance|plant maintenance|commercial maintenance",re.I)
adjacent=re.compile(r"maintenance|repair|refurbishment|mechanical|electrical|heating|boiler|ventilation|contract mobilisation|facilit(?:y|ies)",re.I)
soft=re.compile(r"cleaning|catering|pest control|waste collection|security guard|grounds maintenance|landscaping|window cleaning|laundry|food services",re.I)
strongcpv=("507","79993","713340","453310","453311","453312","453100")
def number(v):
    try:return float(v)
    except:return 0.
def extract(src,rels):
    out=[]
    for r in rels:
        if not ("award" in (r.get("tag") or []) or "contract" in (r.get("tag") or [])):continue
        date=(r.get("date") or "")[:10]
        if not ("2026-11-05"<=date<="2026-11-18"):continue
        t=r.get("tender") or {};title=t.get("title") or "";descr=re.sub(r"\s+"," ",t.get("description") or "")[:1200]
        buyer=(r.get("buyer") or {}).get("name") or ""
        codes=cpvs(t)
        alltext=(title+" "+descr)
        hard=bool(strong.search(alltext) or any(c.startswith(strongcpv) for c in codes))
        digital=bool(re.search(r"software|licen[cs]e|digital platform|information management system|data analytics",title+" "+descr[:300],re.I))
        maybe=bool(adjacent.search(alltext))
        issoft=bool(soft.search(title) and not strong.search(title))
        technique=t.get("techniques") or {}
        framework=bool(technique.get("hasFrameworkAgreement")) or "framework" in (t.get("procurementMethodDetails") or "").lower() or "framework" in title.lower()
        awards=r.get("awards") or []
        contracts=r.get("contracts") or []
        for a in awards:
            if a.get("status") in ("cancelled","unsuccessful"):continue
            v=a.get("value") or {};value=number(v.get("amount"));value_type="award"
            if not value: value=number((t.get("value") or {}).get("amount"));value_type="tender_estimate"
            suppliers=a.get("suppliers") or []
            if not suppliers: suppliers=[{"name":""}]
            for sup in suppliers:
                if isinstance(sup,str):sup={"name":sup}
                aid=str(a.get("id",""));noticeid=str(r.get("id") or "")
                docs=(r.get("awards") or [])
                official=""
                for doc in (r.get("documents") or [])+(a.get("documents") or [])+(t.get("documents") or []):
                    u=(doc or {}).get("url","")
                    if "find-tender.service.gov.uk/Notice/" in u or "contractsfinder.service.gov.uk/notice/" in u.lower():official=u;break
                if not official and src=="FTS":
                    match=re.search(r"\b(\d{6}-2026)\b",noticeid)
                    if match: official="https://www.find-tender.service.gov.uk/Notice/"+match.group(1)
                # For CF, source API link and OCID preserve auditability when notice URL unknown
                record={"source":src,"publication_date":date,"ocid":r.get("ocid",""),"release_id":noticeid,
                    "buyer":buyer,"supplier":sup.get("name",""),"supplier_id":(sup.get("id") or ""),
                    "award_id":aid,"title":title,"description":descr,
                    "value_gbp":value,"value_basis":value_type,"award_status":a.get("status",""),
                    "cpv":";".join(codes),"framework":framework,"contracts_in_release":len(contracts),
                    "hard_match":hard,"adjacent_match":maybe,"soft_match":issoft,
                    "official_notice_url":official,
                    "source_api_url":("https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/"+noticeid if src=="FTS" else
                    "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?publishedFrom="+START+"Z&publishedTo="+END+"Z")}
                record["candidate"]=bool(hard and not issoft and value>=250000 and sup.get("name") and not framework and not digital and value_type=="award")
                if hard and not issoft and value>=250000 and sup.get("name") and framework:record["reason"]="Framework: no confirmed allocation (manual check)"
                elif not sup.get("name"):record["reason"]="No named winning supplier"
                elif not hard:record["reason"]="Not hard FM / technical maintenance"
                elif issoft:record["reason"]="Soft services primarily"
                elif digital:record["reason"]="Digital/software purchase rather than operational workforce"
                elif value<250000:record["reason"]="Below proposed value threshold"
                elif value_type!="award":record["reason"]="Only tender estimate, award value not verified"
                else:record["reason"]="Relevant candidate; verify contract signed, timing, hiring, novelty"
                out.append(record)
    return out
rows=extract("FTS",fts)+extract("CF",cf)
unique={}
for r in rows:
    key=(r["source"],r["ocid"],r["award_id"],r["supplier"])
    if key not in unique or r["publication_date"]>unique[key]["publication_date"]:unique[key]=r
rows=list(unique.values())
candidates=[r for r in rows if r["candidate"]]
candidates.sort(key=lambda x:(-x["value_gbp"],x["publication_date"]))
def save_csv(name,records):
    if records:
        with open(os.path.join(base,name),"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(records[0].keys()));w.writeheader();w.writerows(records)
save_csv("all_awards.csv",rows)
save_csv("candidate_awards.csv",candidates)
summary={"window_start":START,"window_end":END,
   "official_feed":totals,"collection_errors":errors,"award_rows_deduplicated":len(rows),
   "potential_candidates":len(candidates),"linked_hiring_independently_verified":0,
   "method":"Official release API. Scores inferred only. No hiring corroboration. Framework without allocated contract excluded.",
   "completeness":all(x["complete"] for x in totals.values()) and len(totals)==2,
   "tested_at_utc":datetime.now(timezone.utc).isoformat()}
with open(os.path.join(base,"summary.json"),"w") as f:json.dump(summary,f,indent=2)
print("FINAL_SUMMARY",json.dumps(summary),flush=True)
for r in candidates[:50]:
    print("CANDIDATE",r["publication_date"],r["source"],round(r["value_gbp"]),"|",r["supplier"][:38],"|",r["title"][:92],"|",r["official_notice_url"],flush=True)
