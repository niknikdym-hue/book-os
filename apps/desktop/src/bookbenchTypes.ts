export type Finding = { finding_id:string; dimension:string; category:string; location:string; evidence:Record<string,unknown>; severity:"INFO"|"ATTENTION"|"BLOCKING"; confidence:number; recommended_action:string };
export type Dimension = { dimension:string; state:"PASS"|"ATTENTION"|"BLOCKING"; findings:Finding[]; run_ids:string[]; metrics:Record<string,unknown> };
export type Report = { snapshot_id:string; snapshot_hash:string; current:boolean; dimensions:Dimension[]; blocking_dimensions:string[] };
export type Scorecard = { scorecard_id:string; config_id:string; role:string; dimensions:Record<string,Record<string,unknown>>; severe_failure_count:number; pass_count:number; attention_count:number; blocking_count:number; latency_ms:number; cost_usd:number; usage:Record<string,unknown> };
