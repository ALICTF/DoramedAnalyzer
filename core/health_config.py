from enum import Enum
from typing import Dict, TypedDict


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertMessage(TypedDict):
    title: str
    msg: str
    severity: AlertSeverity


class HealthConfig:
    BMI_THRESHOLDS: Dict[str, float] = {
        "under_weight": 18.5,
        "over_weight": 25.0,
        "obesity": 30.0
    }

    BMI_MESSAGES: Dict[str, AlertMessage] = {
        "under_weight": {
            "title": "کمبود وزن", 
            "msg": "شاخص توده بدنی شما نشان‌دهنده «کمبود وزن» است.", 
            "severity": AlertSeverity.MEDIUM
        },
        "healthy_weight": {
            "title": "وزن سالم", 
            "msg": "تبریک! وزن شما در محدوده سالم و ایده‌آل قرار دارد.", 
            "severity": AlertSeverity.LOW
        },
        "over_weight": {
            "title": "اضافه وزن", 
            "msg": "شاخص توده بدنی شما در محدوده «اضافه وزن» قرار دارد.", 
            "severity": AlertSeverity.HIGH
        },
        "obesity": {
            "title": "چاقی (خطر بالا)", 
            "msg": "هشدار: شاخص توده بدنی در محدوده «چاقی» است.", 
            "severity": AlertSeverity.CRITICAL
        }
    }


    BP_THRESHOLDS: Dict[str, Dict[str, int]] = {
        "crisis":   {"sys": 180, "dia": 120},
        "stage2":   {"sys": 140, "dia": 90},
        "stage1":   {"sys": 130, "dia": 80},
        "elevated": {"sys": 120, "dia": 80}, 
        "low":      {"sys": 90,  "dia": 60}
    }

    BP_MESSAGES: Dict[str, AlertMessage] = {
        "crisis": {
            "title": "بحران فشار خون", 
            "msg": "فشار خون در محدوده بحرانی است. نیاز به مداخله فوری.", 
            "severity": AlertSeverity.CRITICAL
        },
        "stage2": {
            "title": "فشار خون بالا (مرحله ۲)", 
            "msg": "خطر آسیب به عروق وجود دارد. مراجعه به پزشک ضروری است.", 
            "severity": AlertSeverity.HIGH
        },
        "stage1": {
            "title": "فشار خون بالا (مرحله ۱)", 
            "msg": "تغییر رژیم غذایی و ورزش توصیه می‌شود.", 
            "severity": AlertSeverity.MEDIUM
        },
        "elevated": {
            "title": "فشار خون افزایش‌یافته", 
            "msg": "پیش‌فشار خون. مراقب مصرف نمک و استرس باشید.", 
            "severity": AlertSeverity.MEDIUM
        },
        "normal": {
            "title": "فشار خون نرمال", 
            "msg": "عالی! فشار خون شما در محدوده کاملاً سالم قرار دارد.", 
            "severity": AlertSeverity.LOW
        },
        "hypotension": {
            "title": "افت فشار خون", 
            "msg": "فشار خون شما پایین‌تر از حد معمول است.", 
            "severity": AlertSeverity.MEDIUM
        }
    }


    O2_THRESHOLDS: Dict[str, int] = {
        "severe_hypoxia": 90,  
        "mild_hypoxia": 95    
    }

    O2_MESSAGES: Dict[str, AlertMessage] = {
        "normal": {
            "title": "اکسیژن خون نرمال", 
            "msg": "سطح اکسیژن خون شما در محدوده طبیعی است.", 
            "severity": AlertSeverity.LOW
        },
        "mild_hypoxia": {
            "title": "افت اکسیژن خفیف", 
            "msg": "افت خفیف اکسیژن مشاهده شد. در صورت تداوم بررسی شود.", 
            "severity": AlertSeverity.MEDIUM
        },
        "severe_hypoxia": {
            "title": "افت اکسیژن شدید", 
            "msg": "هشدار: افت شدید اکسیژن! بررسی‌های پزشکی الزامی است.", 
            "severity": AlertSeverity.CRITICAL
        }
    }


    ECG_THRESHOLDS: Dict[str, int] = {
        "tachycardia": 100,  
        "bradycardia": 60    
    }

    ECG_MESSAGES: Dict[str, AlertMessage] = {
        "normal": {
            "title": "نوار قلب نرمال", 
            "msg": "ریتم و ضربان قلب شما طبیعی ارزیابی شده است.", 
            "severity": AlertSeverity.LOW
        },
        "tachycardia": {
            "title": "تاکیکاردی (ضربان بالا)", 
            "msg": "ضربان قلب در حالت استراحت بالاتر از حد نرمال است.", 
            "severity": AlertSeverity.MEDIUM
        },
        "bradycardia": {
            "title": "برادیکاردی (ضربان پایین)", 
            "msg": "ضربان قلب پایین‌تر از حد معمول است. اگر ورزشکار نیستید بررسی شود.", 
            "severity": AlertSeverity.MEDIUM
        },
        "abnormal_rhythm": {
            "title": "ریتم غیرطبیعی", 
            "msg": "بی‌نظمی در نوار قلب مشاهده شد. مراجعه به متخصص قلب توصیه می‌شود.", 
            "severity": AlertSeverity.HIGH
        }
    }
