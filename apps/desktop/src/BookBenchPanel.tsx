import { useState } from "react";
import { coreApi } from "./api";
import type { Report, Scorecard } from "./bookbenchTypes";
import type { ProjectView } from "./types";

export function BookBenchPanel({ project }: { project: ProjectView }) {
  const [scope,setScope]=useState("BOOK"); const [snapshot,setSnapshot]=useState<string>();
  const [report,setReport]=useState<Report>(); const [scorecards,setScorecards]=useState<Scorecard[]>([]);
  const [message,setMessage]=useState("");
  async function build(){const x=await coreApi<{snapshot_id:string}>("POST",`/api/projects/${project.book_id}/bookbench/snapshots`,{scope});setSnapshot(x.snapshot_id);setMessage("Exact snapshot ready");}
  async function run(path="deterministic",body?:unknown){if(!snapshot)return;await coreApi("POST",`/api/projects/${project.book_id}/bookbench/snapshots/${snapshot}/${path}`,body);setReport(await coreApi<Report>("GET",`/api/projects/${project.book_id}/bookbench/snapshots/${snapshot}/report`));}
  async function send(id:string){await coreApi("POST",`/api/projects/${project.book_id}/bookbench/findings/${id}/handoff`,{actor:"OWNER"});setMessage("Sent to Editorial Inbox for human review");}
  async function compare(){const ds=await coreApi<{dataset_snapshot_id:string}>("POST",`/api/projects/${project.book_id}/bookbench/datasets`,{name:"Editorial decisions"});setScorecards(await coreApi<Scorecard[]>("POST",`/api/projects/${project.book_id}/bookbench/datasets/${ds.dataset_snapshot_id}/compare`,{configs:[{config_id:"fake-a",provider:"fake",model:"fake-a",role:"WRITER"},{config_id:"fake-b",provider:"fake",model:"fake-b",role:"WRITER"}]}));}
  return <section className="panel bookbench"><div className="panel-heading"><div><p className="eyebrow">M7 · DIAGNOSTIC DERIVED STATE</p><h3>BookBench</h3></div><strong>No overall score</strong></div>
    <p>Exact revision evidence only. Results never rewrite, approve, accept, or waive authority.</p>
    <div className="toolbar"><select aria-label="Evaluation scope" value={scope} onChange={e=>setScope(e.target.value)}><option>BOOK</option><option>CHAPTER</option><option>MANUSCRIPT_UNIT</option></select><button onClick={()=>void build()}>Build exact snapshot</button><button disabled={!snapshot} onClick={()=>void run()}>Run deterministic</button><button disabled={!snapshot} onClick={()=>void run("semantic",{provider:"fake",model:"fake-embedding"})}>Run semantic</button><button disabled={!snapshot} onClick={()=>void run("judge",{dimension:"AUTHOR_VOICE",provider:"fake",model:"fake-judge",config_id:"judge-v1"})}>Run judge</button><button onClick={()=>void compare()}>Compare fake configs</button></div>
    {message&&<p role="status">{message}</p>}{report&&<p><strong>{report.current?"CURRENT":"NON-CURRENT / STALE"}</strong> · snapshot {report.snapshot_hash.slice(0,12)}</p>}
    {report?.dimensions.map(d=><article key={d.dimension} className="finding-card"><h4>{d.dimension} <span className="badge">{d.state}</span></h4>{d.findings.map(f=><div key={f.finding_id}><strong>{f.category}</strong><p>{f.location} · confidence {f.confidence}</p><pre>{JSON.stringify(f.evidence,null,2)}</pre><p>{f.recommended_action}</p><button onClick={()=>void send(f.finding_id)}>Send to Editorial Inbox</button></div>)}</article>)}
    <section><h4>Voice Fingerprint & AI-prose pathology</h4><p>Versioned exact references, measurable deltas, and concrete pattern examples are diagnostic only.</p></section>
    {scorecards.length>0&&<section aria-label="Configuration scorecards"><h4>Dataset/config scorecards — no overall score</h4>{scorecards.map(s=><article key={s.scorecard_id}><strong>{s.role} · {s.config_id}</strong><p>PASS {s.pass_count} · ATTENTION {s.attention_count} · BLOCKING {s.blocking_count} · severe {s.severe_failure_count}</p><pre>{JSON.stringify(s.dimensions,null,2)}</pre><small>latency {s.latency_ms}ms · cost ${s.cost_usd} · usage {JSON.stringify(s.usage)}</small></article>)}</section>}
  </section>;
}
