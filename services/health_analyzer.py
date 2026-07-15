from typing import Dict, Any, Optional, TypedDict
from core.health_config import HealthConfig
from core.logging_utils import compact_warning, compact_error, get_logger, setup_logging

setup_logging()
logger = get_logger("analyzer")

try:
    from apps.analyzer.models import TestFile, AlertKind, HealthAlert
    from django.db import transaction
    
    DANGEROUS_SMS_SEVERITIES = {
        HealthAlert.Severity.HIGH,
        HealthAlert.Severity.CRITICAL,
    }
    DJANGO_ENV = True
except ImportError:
    logger.warning("Django integration disabled. reason=models_not_available")
    TestFile = None
    AlertKind = None
    HealthAlert = None
    DANGEROUS_SMS_SEVERITIES = set()
    DJANGO_ENV = False


ALERT_KIND_KEY_ALIASES = {
    "normal": ("healthy_bp", "bp_normal"),
    "elevated": ("bp_elevated", "elevated_bp"),
    "stage1": ("bp_stage1", "hypertension_stage1"),
    "stage2": ("bp_stage2", "hypertension_stage2"),
    "crisis": ("bp_crisis", "hypertensive_crisis"),
    "hypotension": ("bp_hypotension", "low_bp"),
    "under_weight": ("bmi_under_weight",),
    "healthy_weight": ("bmi_healthy_weight",),
    "over_weight": ("bmi_over_weight",),
    "obesity": ("bmi_obesity",),
}

def _get_active_alert_kind(analysis_kind: str) -> Optional[Any]:
    if not DJANGO_ENV:
        return None
        
    candidate_keys = (analysis_kind, *ALERT_KIND_KEY_ALIASES.get(analysis_kind, ()))
    for key in candidate_keys:
        alert_kind = AlertKind.objects.filter(key=key, is_active=True).first()
        if alert_kind is not None:
            return alert_kind
    return None

def _queue_dangerous_alert_sms(alert: Any) -> None:
    if not DJANGO_ENV or alert.severity not in DANGEROUS_SMS_SEVERITIES:
        return

    def _enqueue():
        from apps.analyzer.tasks import send_dangerous_health_alert_sms
        send_dangerous_health_alert_sms.delay(alert.pk)

    try:
        transaction.on_commit(_enqueue)
    except NameError as e:
        compact_warning(logger, "SMS queue registration", e)


class AnalysisResult(TypedDict):
    kind: str
    title: str
    message: str
    severity: str
    value: float
    unit: str
    metric: Dict[str, Any]


class HealthAnalyzer:

    def _build_response(
        self, 
        kind: str, 
        title: str, 
        msg: str, 
        severity: str, 
        value: float, 
        unit: str, 
        metrics: Dict[str, Any]
    ) -> AnalysisResult:
        return {
            "kind": kind,
            "title": title,
            "message": msg,
            "severity": severity,
            "value": value,
            "unit": unit,
            "metric": metrics
        }

    def analyze_body_composition(self, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        bmi = data.get("bmi")
        if bmi is None:
            return None

        if bmi < 18.5:
            kind = "under_weight"
        elif bmi < 25:
            kind = "healthy_weight"
        elif bmi < 30:
            kind = "over_weight"
        else:
            kind = "obesity"
        
        conf = HealthConfig.BMI_MESSAGES.get(kind, {})
        
        return self._build_response(
            kind=kind, 
            title=conf.get("title", kind), 
            msg=conf.get("msg", ""), 
            severity=conf.get("severity", "low"), 
            value=float(bmi), 
            unit="kg/m²", 
            metrics=data
        )

    def analyze_blood_pressure(self, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        sys = data.get("systolic_mmhg")
        dia = data.get("diastolic_mmhg")

        if not (sys and dia):
            return None

        th = HealthConfig.BP_THRESHOLDS
        
        if sys >= th["crisis"]["sys"] or dia >= th["crisis"]["dia"]:
            kind = "crisis"
        elif sys >= th["stage2"]["sys"] or dia >= th["stage2"]["dia"]:
            kind = "stage2"
        elif sys >= th["stage1"]["sys"] or dia >= th["stage1"]["dia"]:
            kind = "stage1"
        elif sys < th["low"]["sys"] or dia < th["low"]["dia"]:
            kind = "hypotension"
        elif sys >= th["elevated"]["sys"] and dia < th["elevated"]["dia"]:
            kind = "elevated"
        else:
            kind = "normal"

        conf = HealthConfig.BP_MESSAGES.get(kind, HealthConfig.BP_MESSAGES["normal"])
        data["formatted_bp"] = f"{int(sys)}/{int(dia)}"
        
        return self._build_response(
            kind=kind, 
            title=conf["title"], 
            msg=conf["msg"], 
            severity=conf["severity"], 
            value=float(sys), 
            unit="mmHg", 
            metrics=data
        )

    def analyze_oxygen_level(self, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        o2_min = data.get("oxygen_summary", {}).get("min")
        if o2_min is None:
            return None

        th = HealthConfig.O2_THRESHOLDS
        
        if o2_min < th["severe_hypoxia"]:
            kind = "severe_hypoxia"
        elif o2_min < th["mild_hypoxia"]:
            kind = "mild_hypoxia"
        else:
            kind = "normal"

        conf = HealthConfig.O2_MESSAGES.get(kind, HealthConfig.O2_MESSAGES["normal"])
        
        return self._build_response(
            kind=kind,
            title=conf["title"],
            msg=conf["msg"],
            severity=conf["severity"],
            value=float(o2_min),
            unit="%",
            metrics=data
        )

    def analyze_ecg(self, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        hr = data.get("heart_rate_bpm")
        if hr is None:
            return None

        rhythm_desc = data.get("waveform_analysis", {}).get("rhythm_regularity", "").lower()
        th = HealthConfig.ECG_THRESHOLDS
        
        if "irregular" in rhythm_desc or "نامنظم" in rhythm_desc:
            kind = "abnormal_rhythm"
        elif hr > th["tachycardia"]:
            kind = "tachycardia"
        elif hr < th["bradycardia"]:
            kind = "bradycardia"
        else:
            kind = "normal"

        conf = HealthConfig.ECG_MESSAGES.get(kind, HealthConfig.ECG_MESSAGES["normal"])

        return self._build_response(
            kind=kind,
            title=conf["title"],
            msg=conf["msg"],
            severity=conf["severity"],
            value=float(hr),
            unit="bpm",
            metrics=data
        )

    def analyze(self, report_type: str, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        analyzers_map = {
            "body_composition": self.analyze_body_composition,
            "blood_pressure": self.analyze_blood_pressure,
            "oxygen_level": self.analyze_oxygen_level,
            "ecg": self.analyze_ecg
        }
        
        analyzer_func = analyzers_map.get(report_type)
        if analyzer_func:
            try:
                return analyzer_func(data)
            except Exception as e:
                compact_error(logger, "Health analysis", e, report_type=report_type)
                return None
        return None


def analyze_summary_result_helper(test_file: Any, data: Dict[str, Any], key: str) -> Optional[Any]:
    try:
        if not data or not DJANGO_ENV:
            return None

        analyzer = HealthAnalyzer()
        
        key_mapping = {
            "bodyComposition": "body_composition",
            "bloodPressure": "blood_pressure",
            "oxygenLevel": "oxygen_level",
            "oxygen_level": "oxygen_level",
            "ecg": "ecg"
        }
        
        mapped_key = key_mapping.get(key, key)
        analysis = analyzer.analyze(mapped_key, data)

        if not analysis:
            return None

        analysis_kind = analysis.get("kind")
        if not analysis_kind:
            return None

        alert_kind = _get_active_alert_kind(analysis_kind)
        if alert_kind is None:
            logger.warning(
                "Alert skipped. reason=alert_kind_missing test_file_id=%s analysis_kind=%s",
                test_file.pk,
                analysis_kind,
            )
            return None

        severity = (analysis.get("severity") or alert_kind.default_severity or "medium").lower()
        value = analysis.get("value")
        unit = analysis.get("unit") or alert_kind.unit or ""
        metrics = analysis.get("metric") or {}

        dedup_key = f"tf:{test_file.pk}:kind:{alert_kind.key}"

        title = analysis.get("title") or alert_kind.title_template.format(
            name=alert_kind.name, value=value, unit=unit
        )
        message = analysis.get("message") or alert_kind.message_template.format(
            name=alert_kind.name, value=value, unit=unit
        )

        is_critical = severity == HealthAlert.Severity.CRITICAL

        defaults = {
            "master": test_file.master,
            "subuser": test_file.subuser,
            "test_file": test_file,
            "kind": alert_kind,
            "severity": severity,
            "is_critical": is_critical,
            "status": HealthAlert.Status.NEW,
            "measured_at": test_file.created_on_device,
            "value": value,
            "unit": unit,
            "metrics": metrics,
            "operator": alert_kind.default_operator,
            "threshold_low": alert_kind.default_threshold_low,
            "threshold_high": alert_kind.default_threshold_high,
            "detected_by": "ai.health_summary.v2",
            "title": title,
            "message": message,
        }

        alert, created = HealthAlert.objects.update_or_create(
            dedup_key=dedup_key,
            defaults=defaults,
        )

        logger.info(
            "Alert saved. action=%s test_file_id=%s alert_id=%s kind=%s severity=%s",
            "created" if created else "updated",
            test_file.pk, alert.pk, alert_kind.key, severity
        )

        _queue_dangerous_alert_sms(alert)

        return alert
    except Exception as e:
        compact_error(logger, "Alert analysis helper", e, key=key)
        return None
