# config.py
from typing import Dict, Any

class HealthConfig:
    
    BMI_THRESHOLDS = {
        "under_weight": 18.5,
        "over_weight": 25.0,
        "obesity": 30.0
    }

    BMI_MESSAGES = {
        "under_weight": {
            "title": "کمبود وزن",
            "msg": "شاخص توده بدنی شما نشان‌دهنده «کمبود وزن» است. این وضعیت ممکن است ناشی از تغذیه ناکافی باشد.",
            "severity": "medium"
        },
        "healthy_weight": {
            "title": "وزن سالم",
            "msg": "تبریک! وزن شما در محدوده سالم و ایده‌آل قرار دارد.",
            "severity": "low"
        },
        "over_weight": {
            "title": "اضافه وزن",
            "msg": "شاخص توده بدنی شما در محدوده «اضافه وزن» قرار دارد. ۳۰ دقیقه پیاده‌روی روزانه توصیه می‌شود.",
            "severity": "high"
        },
        "obesity": {
            "title": "چاقی (خطر بالا)",
            "msg": "هشدار: شاخص توده بدنی در محدوده «چاقی» است. ریسک بیماری‌های متابولیک وجود دارد.",
            "severity": "critical"
        }
    }

    BP_THRESHOLDS = {
        "crisis":   {"sys": 180, "dia": 120},
        "stage2":   {"sys": 140, "dia": 90},
        "stage1":   {"sys": 130, "dia": 80},
        "elevated": {"sys": 120, "dia": 80}, 
        "low":      {"sys": 90,  "dia": 60}
    }

    BP_MESSAGES = {
        "crisis": {
            "title": "بحران فشار خون",
            "msg": "هشدار بسیار جدی: فشار خون در محدوده بحرانی است. نیاز به مداخله فوری پزشکی.",
            "severity": "critical"
        },
        "stage2": {
            "title": "فشار خون بالا (مرحله ۲)",
            "msg": "فشار خون بالا سطح ۲. خطر آسیب به عروق وجود دارد. مراجعه به پزشک ضروری است.",
            "severity": "high"
        },
        "stage1": {
            "title": "فشار خون بالا (مرحله ۱)",
            "msg": "هشدار اولیه فشار خون. تغییر رژیم غذایی (کاهش نمک) و ورزش توصیه می‌شود.",
            "severity": "medium"
        },
        "elevated": {
            "title": "فشار خون افزایش‌یافته",
            "msg": "پیش‌فشار خون. هنوز بیمار نیستید اما باید مراقب مصرف نمک و استرس باشید.",
            "severity": "medium"
        },
        "normal": {
            "title": "فشار خون نرمال",
            "msg": "عالی! فشار خون شما در محدوده کاملاً سالم قرار دارد.",
            "severity": "low"
        },
        "hypotension": {
            "title": "افت فشار خون",
            "msg": "فشار خون شما پایین‌تر از حد معمول است. اگر احساس سرگیجه دارید، مایعات بنوشید.",
            "severity": "medium"
        }
    }