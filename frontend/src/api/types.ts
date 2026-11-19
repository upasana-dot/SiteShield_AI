export type Detection={class_name:string;confidence_score:number;bbox:number[];is_violation:boolean;color:'red'|'green'};
export type Violation={_id:string;timestamp:string;camera_id:string;site_location:string;violation_type:string;class_name:string;severity:string;confidence_score:number;bbox:number[];track_id:string;image_url:string;status:'Unresolved'|'Resolved';resolved_at:string|null;model_version:string};
export type ViolationPage={items:Violation[];total:number;limit:number;skip:number};
export type Prediction={detections:Detection[];new_violations:Violation[];total_workers:number;violation_count:number;compliance_score:number|null;inference_ms:number;frame_size:{width:number;height:number}};
export type HourlyCount={hour:string;count:number}; export type TypeCount={violation_type:string;count:number;severity:string};
export type Summary={total_violations:number;unresolved_count:number;today_count:number;average_compliance_score:number|null;top_violation_type:string|null};
export type Health={api:string;model_loaded:boolean;db_connected:boolean};
export type ModelInfo={model_name:string|null;dataset:string|null;epochs:number|null;metrics:Record<string,number|null>;per_class_ap50:Record<string,number>;violation_classes:Record<string,{label:string;severity:string;enabled:boolean;min_conf:number}>;loaded:boolean};
