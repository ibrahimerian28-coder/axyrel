"use client";
import { useEffect, useState } from "react";

export function ProfileImage({ resource, id, name, canManage }: { resource: "customers" | "assets"; id: string; name: string; canManage: boolean }) {
  const [image, setImage] = useState<string>(); const [preview, setPreview] = useState<string>();
  const [file, setFile] = useState<File>(); const [error, setError] = useState("");
  const [notice, setNotice] = useState(""); const [pending, setPending] = useState(false); const [revision, setRevision] = useState(0);
  const path = `/api/backend/${resource}/${id}/image`;
  const title = resource === "customers" ? "Customer" : "Asset";
  useEffect(() => {
    const controller = new AbortController(); let url: string | undefined;
    fetch(path, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (response.status === 404) { setImage(undefined); return; }
      if (!response.ok) throw new Error("Image could not be loaded.");
      const blob = await response.blob();
      if (controller.signal.aborted) return;
      url = URL.createObjectURL(blob); setImage(url);
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => { controller.abort(); if (url) URL.revokeObjectURL(url); };
  }, [path, revision]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  function selectFile(candidate?: File) { setFile(candidate); setPreview(candidate ? URL.createObjectURL(candidate) : undefined); }
  async function mutate(method: "PUT" | "DELETE") {
    setPending(true); setError(""); setNotice("");
    try {
      const response = await fetch(path, { method, body: method === "PUT" ? file : undefined, headers: method === "PUT" ? { "Content-Type": file?.type || "application/octet-stream" } : undefined });
      if (!response.ok) { const data = await response.json(); throw new Error(typeof data.detail === "string" ? data.detail : "Image could not be saved."); }
      selectFile(undefined); if (method === "DELETE") setImage(undefined); setRevision(r => r + 1); setNotice(method === "DELETE" ? "Image removed." : "Image saved.");
    } catch (e) { setError(e instanceof Error ? e.message : "Image could not be saved."); }
    finally { setPending(false); }
  }
  return <section className="profile-image-section" aria-label={`${title} profile image`}><div className="profile-avatar">{preview || image ? <img src={preview || image} alt={`${name} ${preview ? "image preview" : "profile image"}`} /> : <span role="img" aria-label={`${title} image fallback`}>{resource === "customers" ? name.trim().split(/\s+/).slice(0, 2).map(n => n[0]).join("").toUpperCase() || "?" : "◇"}</span>}</div>{canManage && <div className="image-controls"><label className="image-picker">{image ? "Replace image" : "Choose image"}<input type="file" aria-label={`${title} image file`} accept="image/jpeg,image/png,image/webp" disabled={pending} onChange={e => { const candidate = e.target.files?.[0]; e.target.value = ""; setError(""); setNotice(""); if (candidate && (candidate.size > 5 * 1024 * 1024 || !["image/jpeg", "image/png", "image/webp"].includes(candidate.type))) { selectFile(undefined); setError("Choose a JPEG, PNG or WebP image of 5 MB or smaller."); return; } selectFile(candidate); }} /></label><small>JPEG, PNG or WebP · up to 5 MB</small>{file && <div className="actions"><button className="primary" disabled={pending} onClick={() => { void mutate("PUT"); }}>{pending ? "Saving…" : "Save image"}</button><button disabled={pending} onClick={() => selectFile(undefined)}>Cancel preview</button></div>}{image && <button disabled={pending} onClick={() => { void mutate("DELETE"); }}>Remove image</button>}</div>}{error && <p role="alert">{error}</p>}<span role="status">{notice}</span></section>;
}
