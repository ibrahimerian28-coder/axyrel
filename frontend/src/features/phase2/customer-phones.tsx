"use client";
import geography from "./geography.json";
import { useState } from "react";
export type Phone = {country: string | null; number: string; label: string; normalized?: string | null};
export const phoneLabels = ["Primary", "Mobile", "Work", "Home", "Office", "Emergency"];
export function PhoneLabelEditor({value,onChange,index,disabled=false}:{value:string;onChange:(value:string)=>void;index:number;disabled?:boolean}) {
  const [other,setOther]=useState(false);
  const custom=other||!phoneLabels.includes(value);
  return <><label>Label / description {index}<select aria-label={`Label / description ${index}`} disabled={disabled} value={custom?"__other__":value} onChange={e=>{setOther(e.target.value==="__other__");if(e.target.value!=="__other__")onChange(e.target.value);}}>{phoneLabels.map(label=><option key={label}>{label}</option>)}<option value="__other__">Other</option></select></label>{custom&&<label>Custom phone label {index}<input aria-label={`Custom phone label ${index}`} disabled={disabled} value={value} maxLength={100} onChange={e=>onChange(e.target.value)} /></label>}</>;
}
export function PhonesEditor({phones,setPhones}: {phones:Phone[];setPhones:(phones:Phone[])=>void}) {
  function change(index:number,field:keyof Phone,value:string) {setPhones(phones.map((p,i)=>i===index?{...p,[field]:value}:p));}
  return <section className="phone-editor"><h3>Phone numbers</h3><p>Choose a country; national numbers are normalized securely by the server. Unresolved legacy numbers are retained until you choose their country.</p>{phones.map((phone,index)=><fieldset key={index}><legend>Phone {index+1}</legend><div className="form-grid"><label>Country / calling code {index+1}<select aria-label={`Country / calling code ${index+1}`} value={phone.country||""} onChange={e=>change(index,"country",e.target.value)}><option value="">Unresolved legacy country</option>{geography.countries.filter(c=>c.callingCode).map(c=><option key={c.code} value={c.code}>{c.name} (+{c.callingCode})</option>)}</select></label><label>Phone<input aria-label={index===0?"Phone":`Phone ${index+1}`} value={phone.number} onChange={e=>change(index,"number",e.target.value)} type="tel" maxLength={100} /></label><PhoneLabelEditor index={index+1} value={phone.label} onChange={value=>change(index,"label",value)}/></div><button type="button" onClick={()=>setPhones(phones.filter((_,i)=>i!==index))} aria-label={`Remove phone ${index+1}`}>Remove phone</button></fieldset>)}<button type="button" disabled={phones.length>=100} onClick={()=>setPhones([...phones,{country:"EG",number:"",label:"Other"}])}>+ Add Phone Number</button><p>Up to 100 contact numbers per Customer.</p></section>;
}
