"use client";
import { useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { errorMessage } from "@/features/phase3/contracts";
import { AssetImport } from "./import-assets";
import geography from "@/features/phase2/geography.json";
import { PhoneLabelEditor } from "@/features/phase2/customer-phones";

type Mode = "customers" | "assets" | "combined";
type Upload = { columns: string[]; rows: string[][]; mapping: string[]; fields: Record<string,string> };
type Data = Upload & { mode: Mode; skipped_rows: number[]; corrections: Record<string,Record<string,string>> };
type Summary = { new_customers: number; existing_customers: number; new_assets: number; overwritten_assets: number; attention_rows: number; skipped_rows: number };
type PreviewRow = {row:number;customer:string;customer_number:number|null;match:string;category:string;phone:string;asset_type:string;serial_number:string;warranty_end:string;values:Record<string,string>};
type Preview = { valid: boolean; message?:string; preview: PreviewRow[]; errors: {row:number;field:string;label:string;message:string}[]; summary:Summary; token?:string; replayed?:boolean; customer_numbers?:number[];asset_numbers?:number[] };
type Customer = {display_id:number|null;name:string};
const names:Record<Mode,string>={customers:"Customers only",assets:"Assets only",combined:"Customers + Assets"};
function Counts({summary}:{summary:Summary}) {return <ul className="smart-counts"><li>{summary.new_customers} new Customers</li><li>{summary.existing_customers} existing Customers matched</li><li>{summary.new_assets} new Assets</li><li>{summary.overwritten_assets} existing Assets overwritten</li><li>{summary.skipped_rows??0} rows skipped</li><li>{summary.attention_rows} rows need attention</li></ul>;}
function downloadTemplate(result:{content:string;filename:string;format:string}) {
  const bytes=Uint8Array.from(atob(result.content),c=>c.charCodeAt(0));
  const url=URL.createObjectURL(new Blob([bytes],{type:result.format==="xlsx"?"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":"text/csv;charset=utf-8"}));
  const link=document.createElement("a");link.href=url;link.download=result.filename;link.click();URL.revokeObjectURL(url);
}
function base64(bytes:Uint8Array){let result="";for(let i=0;i<bytes.length;i+=8192)result+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(result);}

export function SmartImport({done,allowCustomers,allowAssets}:{done:()=>Promise<void>;allowCustomers:boolean;allowAssets:boolean}) {
  const [open,setOpen]=useState(false),[mode,setMode]=useState<Mode>(allowCustomers&&allowAssets?"combined":allowCustomers?"customers":"assets"),[step,setStep]=useState(1);
  const [upload,setUpload]=useState<Upload>(),[corrections,setCorrections]=useState<Data["corrections"]>({}),[preview,setPreview]=useState<Preview>(),[reviewed,setReviewed]=useState<Data>(),[key,setKey]=useState("");
  const [pending,setPending]=useState(false),[error,setError]=useState(""),[confirmed,setConfirmed]=useState(false),[uncertain,setUncertain]=useState(false),[receipt,setReceipt]=useState<Preview>();
  const [skippedRows,setSkippedRows]=useState<number[]>([]);
  const [customers,setCustomers]=useState<Customer[]>([]),[customerSearch,setCustomerSearch]=useState("");
  const modes=(Object.keys(names) as Mode[]).filter(m=>m==="combined"?allowCustomers&&allowAssets:m==="customers"?allowCustomers:allowAssets);
  function reset(){setSkippedRows([]);setUpload(undefined);setCorrections({});setPreview(undefined);setReviewed(undefined);setReceipt(undefined);setError("");setConfirmed(false);setStep(1);}
  async function template(format:string){setError("");try{downloadTemplate(await api(`imports/template?mode=${mode}&format=${format}`));}catch(e){setError(errorMessage(e));}}
  async function load(file:File|undefined){if(!file)return;reset();setPending(true);try{
    const format=file.name.toLowerCase().split(".").pop();if(!["csv","xlsx"].includes(format||"")||file.size>1048576)throw new Error("Choose an XLSX or CSV file of 1 MB or smaller.");
    const result=await api<Upload>("imports/upload",{method:"POST",body:JSON.stringify({mode,format,content:base64(new Uint8Array(await file.arrayBuffer()))})});setUpload(result);setStep(2);
    setCustomers(await api<Customer[]>("customers"));
  }catch(e){setError(e instanceof ApiError?errorMessage(e):e instanceof Error?e.message:"Unable to read file.");}finally{setPending(false);}}
  async function review(nextSkipped=skippedRows){if(!upload)return;setPending(true);setError("");setConfirmed(false);try{
    const data={...upload,mode,corrections,skipped_rows:nextSkipped};const result=await api<Preview>("imports/preview",{method:"POST",body:JSON.stringify(data)});
    setPreview(result);setReviewed(data);setKey(crypto.randomUUID());setStep(3);
  }catch(e){setError(errorMessage(e));}finally{setPending(false);}}
  function toggleSkip(row:number){
    if(pending||uncertain)return;
    const next=skippedRows.includes(row)?skippedRows.filter(number=>number!==row):[...skippedRows,row].sort((a,b)=>a-b);
    setSkippedRows(next);setPreview(old=>old?{...old,valid:false,token:undefined}:old);setReviewed(undefined);setConfirmed(false);
    void review(next);
  }
  function correct(row:number,field:string,value:string){setCorrections(old=>({...old,[row]:{...old[row],[field]:value}}));setPreview(old=>old?{...old,valid:false,token:undefined}:old);setConfirmed(false);}
  async function commit(){if(!preview?.token||!reviewed)return;setPending(true);setError("");setUncertain(true);try{
    const result=await api<Preview>("imports/commit",{method:"POST",body:JSON.stringify({data:reviewed,token:preview.token,idempotency_key:key})});
    if(result.valid){setUncertain(false);try{await done();}catch{setError("Import completed. Refresh this page to reload your records.");}setReceipt(result);}
    else{setPreview(result);setUncertain(false);setConfirmed(false);setStep(3);}
  }catch(e){if(e instanceof ApiError&&[400,413].includes(e.status)){setUncertain(false);setStep(3);setPreview(old=>old?{...old,valid:false,token:undefined}:old);setConfirmed(false);}setError(errorMessage(e));}finally{setPending(false);}}
  const countryOptions=geography.countries;
  return <section className="panel smart-import" aria-label="Smart Import"><button aria-expanded={open} disabled={pending||uncertain} onClick={()=>setOpen(!open)}>Import Data</button>{open&&<>
    <h2>Import Data</h2><ol className="smart-steps" aria-label="Import steps">{["Upload","Match Columns","Review","Import"].map((name,i)=><li key={name} aria-current={step===i+1?"step":undefined}>{i+1}. {name}</li>)}</ol>
    {error&&<p role="alert">{error}</p>}
    {step===1&&<><label>Import type<select aria-label="Import type" value={mode} disabled={pending} onChange={e=>{reset();setMode(e.target.value as Mode);}}>{modes.map(m=><option key={m} value={m}>{names[m]}</option>)}</select></label><p>XLSX or UTF-8 CSV · 1 MB · 1000 data rows · 40 columns · 1000 characters per cell. Use one worksheet with plain values; formulas, macros and external links are rejected.</p><p>Use country and governorate names, for example Egypt and Cairo. Blank country and phone country use Egypt; you can correct them in Review. Preserve phone leading zeroes. Installation dates: YYYY-MM-DD or Excel date cells.</p><div className="smart-actions"><button className="primary" onClick={()=>void template("xlsx")}>Download Excel Template</button><button onClick={()=>void template("csv")}>Download CSV Template</button></div><label>Spreadsheet file<input aria-label="Spreadsheet file" type="file" accept=".xlsx,.csv" disabled={pending} onChange={e=>void load(e.target.files?.[0])}/></label></>}
    {step===2&&upload&&<><h3>Match Columns</h3><p>{upload.rows.length} rows loaded. Match each column once, or ignore it.</p><div className="smart-mapping">{upload.columns.map((column,i)=><label key={i}>{column}<select aria-label={`Map ${column}`} value={upload.mapping[i]} disabled={pending} onChange={e=>{const mapping=[...upload.mapping];mapping[i]=e.target.value;setUpload({...upload,mapping});}}><option value="">Ignore this column</option>{Object.entries(upload.fields).map(([key,label])=><option key={key} value={key} disabled={upload.mapping.some((value,index)=>index!==i&&value===key)}>{label}</option>)}</select><small>Example: {upload.rows[0]?.[i]||"Empty"}</small></label>)}</div><div className="smart-actions"><button disabled={pending} onClick={reset}>Choose another file</button><button className="primary" disabled={pending} onClick={()=>void review()}>Review import</button></div></>}
    {step===3&&preview&&<><h3>{preview.valid?"Ready to import":"Review and correct your rows"}</h3><Counts summary={preview.summary}/>{preview.message&&<p role="status">{preview.message}</p>}{pending&&<p role="status">Rechecking rows...</p>}<p>Skipped rows create nothing. Existing customers will not be duplicated or changed. Conflicting names on repeated new-customer phones require correction. Assets are created only.</p>
      <label>Find an existing customer<input value={customerSearch} onChange={e=>setCustomerSearch(e.target.value)} placeholder="Search customer name or number"/></label>
      <div className="smart-review">{["Ready","Existing matched","Needs attention","Skipped"].map(category=><section key={category}><h3>{category} ({preview.preview.filter(r=>r.category===category).length})</h3>{preview.preview.filter(r=>r.category===category).map(row=>{
        const values={...row.values,...corrections[row.row]};const country=countryOptions.find(c=>c.code===values.country||c.name.toLowerCase()===(values.country||"Egypt").toLowerCase())?.code||"";
        const states=geography.states[country as keyof typeof geography.states]||[];
        const selectedState=states.find(s=>s.code===values.state||s.name.toLowerCase()===(values.state||"").toLowerCase());
        const errors=preview.errors.filter(e=>e.row===row.row);
        return <article className={`smart-row${row.category==="Skipped"?" is-skipped":""}`} aria-label={`Source row ${row.row}`} key={row.row}><h4>Row {row.row}: {row.customer||"Customer needs attention"}{row.customer_number?` · Customer No. #${row.customer_number}`:""}</h4><p>{row.match}{row.match==="Existing customer found"?" · Customer will NOT be duplicated":""}</p><p>{row.phone} {row.asset_type&&` · ${row.asset_type}`} {row.serial_number&&` · ${row.serial_number}`}{row.warranty_end&&` · Warranty end ${row.warranty_end}`}</p>
          {mode!=="customers"&&row.customer_number&&<p>{preview.preview.filter(r=>r.customer_number===row.customer_number).length} new Assets will be added for this customer.</p>}
          {!!errors.length&&<section aria-label={`Row ${row.row} errors`}><h4>Errors</h4><ul>{errors.map((e,i)=><li key={i}><strong>{e.label}:</strong> {e.message}</li>)}</ul></section>}
          <button disabled={pending||uncertain} aria-label={`${row.category==="Skipped"?"Restore row":"Skip this row"} ${row.row}`} onClick={()=>toggleSkip(row.row)}>{row.category==="Skipped"?"Restore row":"Skip this row"}</button>
          {row.category!=="Skipped"&&<details><summary>Correct row {row.row}</summary><div className="smart-mapping">
            <label>Country<select aria-label={`Row ${row.row} Country`} value={country} disabled={pending} onChange={e=>{correct(row.row,"country",e.target.value);correct(row.row,"state","");}}><option value="">Choose country</option>{countryOptions.map(c=><option key={c.code} value={c.code}>{c.name}</option>)}</select></label>
            <label>Governorate / State<select aria-label={`Row ${row.row} Governorate / State`} value={selectedState?.code||""} disabled={pending} onChange={e=>correct(row.row,"state",e.target.value)}><option value="">Not specified</option>{states.map(s=><option key={s.code} value={s.code}>{s.name}</option>)}</select></label>
            <label>Phone country<select aria-label={`Row ${row.row} Phone country`} value={countryOptions.find(c=>c.code===values.phone_country||c.name.toLowerCase()===(values.phone_country||values.country||"Egypt").toLowerCase())?.code||""} disabled={pending} onChange={e=>correct(row.row,"phone_country",e.target.value)}><option value="">Choose phone country</option>{countryOptions.filter(c=>c.callingCode).map(c=><option key={c.code} value={c.code}>{c.name} (+{c.callingCode})</option>)}</select></label>
            <label>Status<select aria-label={`Row ${row.row} Status`} value={values.status||"Active"} disabled={pending} onChange={e=>correct(row.row,"status",e.target.value)}><option>Active</option><option>Inactive</option>{values.status&&!['Active','Inactive'].includes(values.status)&&<option value={values.status}>{values.status} (choose a valid status)</option>}</select></label>
            <PhoneLabelEditor disabled={pending} index={row.row} value={values.phone_label||"Primary"} onChange={value=>correct(row.row,"phone_label",value)}/>
            <label>Existing customer<select aria-label={`Row ${row.row} Existing customer`} value={values.customer_selection||""} disabled={pending} onChange={e=>correct(row.row,"customer_selection",e.target.value)}><option value="">Use safe phone matching</option>{customers.filter(c=>c.display_id!==null&&(String(c.display_id).includes(customerSearch)||c.name.toLowerCase().includes(customerSearch.toLowerCase())||String(c.display_id)===values.customer_selection)).map(c=><option key={c.display_id} value={String(c.display_id)}>{c.name} · Customer No. #{c.display_id}</option>)}</select></label>
            {Object.entries(upload?.fields||{}).filter(([key])=>!['country','state','phone_country','status','phone_label'].includes(key)).map(([field,label])=><label key={field}>{label}<input aria-label={`Row ${row.row} ${label}`} value={values[field]||""} maxLength={field==='customer_name'?200:1000} disabled={pending} onChange={e=>correct(row.row,field,e.target.value)}/></label>)}
          </div></details>}</article>;
      })}</section>)}</div><div className="smart-actions"><button disabled={pending} onClick={()=>{setStep(2);setPreview(undefined);}}>Back to columns</button><button disabled={pending} onClick={()=>void review()}>Recheck corrections</button><button className="primary" disabled={!preview.valid||pending} onClick={()=>{setStep(4);setConfirmed(false);}}>Continue to Import</button></div></>}
    {step===4&&preview&&!receipt&&<><h3>Confirm import</h3><Counts summary={preview.summary}/><p>Skipped rows create nothing. Existing customers and assets will remain unchanged.</p><label className="check-label"><input type="checkbox" checked={confirmed} disabled={pending||uncertain} onChange={e=>setConfirmed(e.target.checked)}/>I confirm these new Customers and Assets will be created.</label><div className="smart-actions"><button disabled={pending||uncertain} onClick={()=>setStep(3)}>Back to review</button><button className="primary" disabled={!confirmed||pending} onClick={()=>void commit()}>{pending?"Importing…":uncertain?"Retry same import safely":"Confirm import"}</button></div>{uncertain&&<p>Keep this review unchanged. Retry uses the same key and cannot create this batch twice.</p>}</>}
    {receipt&&<section role="status"><h3>Import completed</h3><Counts summary={receipt.summary}/><p>Customer numbers: {receipt.customer_numbers?.map(n=>`#${n}`).join(", ")||"No new customers"}</p><p>Asset numbers: {receipt.asset_numbers?.map(n=>`#${n}`).join(", ")||"No new assets"}</p>{receipt.replayed&&<p>Existing receipt retrieved; no duplicate records created.</p>}<button onClick={reset}>Start another import</button></section>}
  </>}{allowAssets&&<details className="smart-legacy"><summary>Advanced / legacy Asset CSV import</summary><AssetImport done={done}/></details>}</section>;
}
