from typing import Dict, Any, Optional
from config import HealthConfig
import logging

logger = logging.getLogger("dstand.ai.analyzer")

class HealthAnalyzer:

    def _build_response(self, kind: str, title: str, msg: str, severity: str, value: float, unit: str, metrics: Dict) -> Dict[str, Any]:
        return {
            "kind": kind,
            "title": title,
            "message": msg,
            "severity": severity,
            "value": value,
            "unit": unit,
            "metric": metrics
        }

    def analyze_body_composition(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        bmi = data.get("bmi")
        if bmi is None:
            return None

        kind = ""
        if bmi < 18.5: kind = "under_weight"
        elif bmi < 25: kind = "healthy_weight"
        elif bmi < 30: kind = "over_weight"
        else: kind = "obesity"
        
        conf = HealthConfig.BMI_MESSAGES.get(kind, {})
        
        return self._build_response(
            kind, 
            conf.get("title", kind), 
            conf.get("msg", ""), 
            conf.get("severity", "low"), 
            bmi, "kg/m²", {'bmi': bmi}
        )

    
    def analyze_blood_pressure(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sys = data.get("systolic_mmhg")
        dia = data.get("diastolic_mmhg")

        if not (sys and dia):
            return None

        th = HealthConfig.BP_THRESHOLDS
        
        kind = ""
        
        if sys >= th["crisis"]["sys"] or dia >= th["crisis"]["dia"]:
            kind = "crisis"
        elif sys >= th["stage2"]["sys"] or dia >= th["stage2"]["dia"]:
            kind = "stage2"
        elif sys >= th["stage1"]["sys"] or dia >= th["stage1"]["dia"]:
            kind = "stage1"
        elif sys >= th["elevated"]["sys"] and dia < th["elevated"]["dia"]:
            kind = "elevated"
        elif sys < th["low"]["sys"] or dia < th["low"]["dia"]:
            kind = "hypotension"
        else:
            kind = "normal"

        conf = HealthConfig.BP_MESSAGES.get(kind, HealthConfig.BP_MESSAGES["normal"])
        
        display_val = float(f"{int(sys)}.{int(dia)}")
        
        return self._build_response(
            kind, 
            conf["title"], 
            conf["msg"], 
            conf["severity"], 
            display_val, 
            "mmHg", 
            {"systolic_mmhg": sys, "diastolic_mmhg": dia}
        )

    def analyze(self, report_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if report_type == "body_composition":
            return self.analyze_body_composition(data)
        elif report_type == "blood_pressure":
            return self.analyze_blood_pressure(data)
        return None