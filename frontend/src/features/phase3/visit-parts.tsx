"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { Row } from "@/features/phase2/screens";
import type { User } from "@/lib/api/types";
import { errorMessage } from "./contracts";

export function VisitParts({visit,items,user,refresh}:{visit:Row;items:Row[];user:User;refresh:()=>Promise<void>}) {
  const [editing,setEditing]=useState(false),[pending,setPending]=useState(false),[error,setError]=useState("");
  const stock=useQuery({queryKey:["visit-parts",user.id,user.company_id,visit.id],enabled:user.permissions.includes("inventory:read"),queryFn:async()=>({movements:await api<Row[]>("inventory-transactions"),balances:await api<Row[]>("technician-stock")})});
  const movements=stock.data?.movements.filter(r=>r.reference_id===visit.id&&["SERVICE_VISIT_INSTALL","SERVICE_VISIT_REVERSAL"].includes(String(r.reference_type)))||[];
  const outstanding=movements.reduce((n,r)=>n+Number(r.quantity)*(r.reference_type==="SERVICE_VISIT_INSTALL"?1:-1),0);
  async function change(event:React.FormEvent<HTMLFormElement>,reverse=false){event.preventDefault();setPending(true);setError("");const form=new FormData(event.currentTarget);try{await api(`service-visits/${visit.id}/parts${reverse?"/reverse":""}`,{method:"POST",body:JSON.stringify(reverse?{reason:form.get("reason")}:{inventory_item_id:form.get("inventory_item_id"),quantity:Number(form.get("quantity"))})});await stock.refetch();await refresh();}catch(e){setError(errorMessage(e));}finally{setPending(false);}}
  if(!user.permissions.includes("inventory:read"))return <p>Inventory access is unavailable.</p>;
  return <section aria-label="Visit inventory" className="service-related"><h3>Visit inventory</h3>{stock.error?<p role="alert">Inventory could not be loaded.</p>:stock.isPending?<p>Loading inventory…</p>:<>{movements.map(r=><p key={r.id}>{r.reference_type==="SERVICE_VISIT_REVERSAL"?"Reversal":"Installed"} · {items.find(i=>i.id===r.inventory_item_id)?.item_name||"Unavailable part"} · Quantity {r.quantity}</p>)}{!movements.length&&<p>No recorded installations or reversals.</p>}{user.permissions.includes("service:manage")&&visit.status==="In Progress"&&<><button type="button" onClick={()=>setEditing(!editing)}>{editing?"Close parts editing":"Edit parts"}</button>{editing&&<><form onSubmit={e=>{void change(e);}}><fieldset disabled={pending}><label>Inventory item<select aria-label="Inventory item" name="inventory_item_id" required><option value="">Select a part</option>{items.map(i=><option value={i.id} key={i.id}>{i.item_name} · Technician stock {stock.data?.balances.find(b=>b.technician_id===visit.technician_id&&b.inventory_item_id===i.id)?.quantity||0}</option>)}</select></label><label>Quantity<input name="quantity" type="number" min="1" step="1" defaultValue="1" required/></label><button className="primary">Install part</button></fieldset></form>{outstanding>0&&<form onSubmit={e=>{void change(e,true);}}><fieldset disabled={pending}><p>Reverse all outstanding installed parts before reinstalling the corrected quantities. Original movements remain in the audit trail.</p><label>Correction reason<input name="reason" required/></label><button>Reverse installed parts</button></fieldset></form>}</>}</>}</>}{error&&<p role="alert">{error}</p>}</section>;
}
