from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="Acil Durum AI Backend",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://192.168.31.8:5173",
        "http://192.168.31.8:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# VERİLER
# =========================================================

emergencies = []


# =========================================================
# MODELLER
# =========================================================

class AnalyzeRequest(BaseModel):
    message: str


class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None


class AnalysisData(BaseModel):
    type: str = "GENEL"
    priority: str = "DÜŞÜK"
    confidence: float = 0
    detected_keywords: list[str] = []
    suggestion: str = ""


class EmergencyCreate(BaseModel):
    service: str
    description: str
    location: Optional[LocationData] = None
    analysis: AnalysisData


class StatusUpdate(BaseModel):
    status: str


class AssignTeamRequest(BaseModel):
    team: Optional[str] = None


# =========================================================
# AI ANAHTAR KELİMELER
# =========================================================

FIRE_WORDS = [
    "yangın",
    "yanıyor",
    "alev",
    "duman",
    "patlama",
    "yanmak",
]

MEDICAL_WORDS = [
    "bayıldı",
    "bayılma",
    "kanama",
    "yaralı",
    "yaralandı",
    "nefes",
    "nefes alamıyor",
    "kalp",
    "kalp krizi",
    "bilinci kapalı",
    "ambulans",
    "zehirlenme",
]

POLICE_WORDS = [
    "kavga",
    "saldırı",
    "tehdit",
    "hırsızlık",
    "silah",
    "bıçak",
    "polis",
    "şiddet",
]

ACCIDENT_WORDS = [
    "kaza",
    "çarpışma",
    "çarpıştı",
    "araç",
    "otomobil",
    "trafik kazası",
]

DISASTER_WORDS = [
    "deprem",
    "sel",
    "fırtına",
    "heyelan",
    "tsunami",
]


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

def analyze_text(text: str):
    text_lower = text.lower()

    detected = []

    for word in FIRE_WORDS:
        if word in text_lower:
            detected.append(word)

    if detected:
        return {
            "type": "YANGIN",
            "priority": "KRİTİK",
            "confidence": 95,
            "detected_keywords": detected,
            "suggestion": "İtfaiye ekibi yönlendirilmesi önerilir.",
        }

    detected = []

    for word in MEDICAL_WORDS:
        if word in text_lower:
            detected.append(word)

    if detected:
        return {
            "type": "SAĞLIK",
            "priority": "YÜKSEK",
            "confidence": 92,
            "detected_keywords": detected,
            "suggestion": "Sağlık/ambulans ekibi yönlendirilmesi önerilir.",
        }

    detected = []

    for word in POLICE_WORDS:
        if word in text_lower:
            detected.append(word)

    if detected:
        return {
            "type": "GÜVENLİK",
            "priority": "YÜKSEK",
            "confidence": 90,
            "detected_keywords": detected,
            "suggestion": "Polis ekibi yönlendirilmesi önerilir.",
        }

    detected = []

    for word in ACCIDENT_WORDS:
        if word in text_lower:
            detected.append(word)

    if detected:
        return {
            "type": "KAZA",
            "priority": "YÜKSEK",
            "confidence": 88,
            "detected_keywords": detected,
            "suggestion": "Trafik/kaza müdahale ekibi yönlendirilmesi önerilir.",
        }

    detected = []

    for word in DISASTER_WORDS:
        if word in text_lower:
            detected.append(word)

    if detected:
        return {
            "type": "DOĞAL AFET",
            "priority": "YÜKSEK",
            "confidence": 87,
            "detected_keywords": detected,
            "suggestion": "Acil müdahale ve koordinasyon ekibi yönlendirilmesi önerilir.",
        }

    return {
        "type": "GENEL",
        "priority": "DÜŞÜK",
        "confidence": 60,
        "detected_keywords": [],
        "suggestion": "Olayın detaylı olarak değerlendirilmesi önerilir.",
    }


def create_event_id():
    return f"event-{int(datetime.now().timestamp() * 1000)}"


# =========================================================
# ANA SAYFA / SAĞLIK KONTROLÜ
# =========================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "Acil Durum AI backend çalışıyor.",
        "status": "online",
        "port": 8000,
        "time": datetime.now().isoformat(),
    }

@app.get("/health")
def health():
    return {
        "success": True,
        "status": "online",
    }

# =========================================================
# AI ANALİZ
# =========================================================

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = analyze_text(request.message)

    return {
        "success": True,
        "analysis": result,
    }


# =========================================================
# ACİL DURUM OLUŞTUR
# =========================================================

@app.post("/events")
def create_event(data: EmergencyCreate):
    event_id = create_event_id()

    event = {
        "id": event_id,
        "service": data.service,
        "description": data.description,
        "location": (
            data.location.model_dump()
            if data.location
            else None
        ),
        "analysis": data.analysis.model_dump(),
        "status": "Yeni",
        "team": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    emergencies.append(event)

    return {
        "success": True,
        "message": "Acil durum başarıyla oluşturuldu.",
        "event": event,
    }


# =========================================================
# TÜM ACİL DURUMLAR
# =========================================================

@app.get("/events")
def get_events():
    return {
        "success": True,
        "events": emergencies,
        "count": len(emergencies),
    }


# =========================================================
# TEK ACİL DURUM
# =========================================================

@app.get("/events/{event_id}")
def get_event(event_id: str):
    for emergency in emergencies:
        if emergency["id"] == event_id:
            return {
                "success": True,
                "event": emergency,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# DURUM GÜNCELLE
# =========================================================

@app.patch("/events/{event_id}")
def update_event_status(
    event_id: str,
    data: StatusUpdate,
):
    for emergency in emergencies:
        if emergency["id"] == event_id:
            emergency["status"] = data.status
            emergency["updated_at"] = datetime.now().isoformat()

            return {
                "success": True,
                "message": "Durum güncellendi.",
                "event": emergency,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# EKİP ATA
# =========================================================

@app.patch("/events/{event_id}/assign")
def assign_event_team(
    event_id: str,
    data: AssignTeamRequest,
):
    for emergency in emergencies:
        if emergency["id"] == event_id:

            team_name = (
                data.team
                or emergency["service"]
                or "Operasyon Ekibi"
            )

            emergency["team"] = team_name

            if emergency["status"] == "Yeni":
                emergency["status"] = "Ekip Atandı"

            emergency["updated_at"] = datetime.now().isoformat()

            return {
                "success": True,
                "message": "Ekip başarıyla atandı.",
                "event": emergency,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# ACİL DURUM SİL
# =========================================================

@app.delete("/events/{event_id}")
def delete_event(event_id: str):
    for index, emergency in enumerate(emergencies):
        if emergency["id"] == event_id:
            deleted = emergencies.pop(index)

            return {
                "success": True,
                "message": "Acil durum silindi.",
                "event": deleted,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# ESKİ / LEGACY ENDPOINTLER
# =========================================================

@app.get("/emergencies")
def get_emergencies():
    return {
        "success": True,
        "emergencies": emergencies,
        "count": len(emergencies),
    }


@app.post("/emergencies")
def create_emergency(data: EmergencyCreate):
    return create_event(data)


@app.get("/emergencies/{emergency_id}")
def get_emergency(emergency_id: str):
    return get_event(emergency_id)


@app.patch("/emergencies/{emergency_id}")
def update_emergency(
    emergency_id: str,
    data: StatusUpdate,
):
    return update_event_status(emergency_id, data)


@app.delete("/emergencies/{emergency_id}")
def delete_emergency(emergency_id: str):
    return delete_event(emergency_id)