from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Acil Durum AI API",
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MEMORY DATABASE
# =========================================================

emergencies = []


# =========================================================
# MODELS
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


# =========================================================
# AI KEYWORDS
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
# AI ANALYSIS
# =========================================================

def analyze_text(message: str):
    text = message.lower().strip()

    detected = []

    for word in FIRE_WORDS:
        if word in text:
            detected.append(word)

    for word in MEDICAL_WORDS:
        if word in text:
            detected.append(word)

    for word in POLICE_WORDS:
        if word in text:
            detected.append(word)

    for word in ACCIDENT_WORDS:
        if word in text:
            detected.append(word)

    for word in DISASTER_WORDS:
        if word in text:
            detected.append(word)

    # YANGIN
    if any(word in text for word in FIRE_WORDS):
        return {
            "type": "YANGIN",
            "priority": "KRİTİK",
            "confidence": 95,
            "detected_keywords": detected,
            "suggestion": (
                "Yangın belirtileri tespit edildi. "
                "İtfaiye müdahalesi öncelikli olmalıdır."
            ),
        }

    # SAĞLIK
    if any(word in text for word in MEDICAL_WORDS):
        return {
            "type": "SAĞLIK",
            "priority": "YÜKSEK",
            "confidence": 92,
            "detected_keywords": detected,
            "suggestion": (
                "Sağlıkla ilgili acil durum belirtileri "
                "tespit edildi. Ambulans desteği önceliklidir."
            ),
        }

    # GÜVENLİK
    if any(word in text for word in POLICE_WORDS):
        return {
            "type": "GÜVENLİK",
            "priority": "YÜKSEK",
            "confidence": 90,
            "detected_keywords": detected,
            "suggestion": (
                "Güvenlik riski tespit edildi. "
                "Polis desteği değerlendirilmelidir."
            ),
        }

    # KAZA
    if any(word in text for word in ACCIDENT_WORDS):
        return {
            "type": "KAZA",
            "priority": "YÜKSEK",
            "confidence": 88,
            "detected_keywords": detected,
            "suggestion": (
                "Kaza bildirimi tespit edildi. "
                "Gerekli acil ekiplerin yönlendirilmesi önerilir."
            ),
        }

    # DOĞAL AFET
    if any(word in text for word in DISASTER_WORDS):
        return {
            "type": "DOĞAL AFET",
            "priority": "YÜKSEK",
            "confidence": 87,
            "detected_keywords": detected,
            "suggestion": (
                "Doğal afet ile ilgili bildirim tespit edildi."
            ),
        }

    # GENEL
    return {
        "type": "GENEL",
        "priority": "DÜŞÜK",
        "confidence": 60,
        "detected_keywords": detected,
        "suggestion": (
            "Acil durum açıklaması analiz edildi."
        ),
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Acil Durum AI",
        "version": "1.0.0",
        "emergency_count": len(emergencies),
    }


# =========================================================
# AI ANALYZE
# =========================================================

@app.post("/analyze")
def analyze_emergency(request: AnalyzeRequest):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Mesaj boş olamaz.",
        )

    return analyze_text(request.message)


# =========================================================
# CREATE EMERGENCY
# =========================================================

@app.post("/events")
def create_emergency(data: EmergencyCreate):

    emergency_id = str(uuid4())[:8].upper()

    location = data.location

    analysis = data.analysis

    emergency = {
        "id": emergency_id,

        "service": data.service,

        "description": data.description,

        "category": analysis.type,

        "priority": analysis.priority,

        "confidence": analysis.confidence,

        "detected_keywords": (
            analysis.detected_keywords
        ),

        "suggestion": analysis.suggestion,

        "status": "Yeni",

        "team": None,

        "latitude": (
            location.latitude
            if location
            else None
        ),

        "longitude": (
            location.longitude
            if location
            else None
        ),

        "accuracy": (
            location.accuracy
            if location
            else None
        ),

        "created_at": datetime.now().isoformat(),

        "updated_at": datetime.now().isoformat(),
    }

    emergencies.insert(0, emergency)

    return {
        "success": True,
        "message": "Acil durum başarıyla oluşturuldu.",
        "event": emergency,
    }


# =========================================================
# GET ALL EMERGENCIES
# =========================================================

@app.get("/emergencies")
def get_emergencies():

    return {
        "success": True,
        "count": len(emergencies),
        "emergencies": emergencies,
    }


# =========================================================
# GET SINGLE EMERGENCY
# =========================================================

@app.get("/emergencies/{emergency_id}")
def get_emergency(emergency_id: str):

    for emergency in emergencies:
        if emergency["id"] == emergency_id:
            return {
                "success": True,
                "emergency": emergency,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# UPDATE STATUS
# =========================================================

@app.patch("/emergencies/{emergency_id}/status")
def update_status(
    emergency_id: str,
    data: StatusUpdate,
):

    allowed_statuses = [
        "Yeni",
        "Ekip Atandı",
        "Müdahale Ediliyor",
        "Çözüldü",
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz durum.",
        )

    for emergency in emergencies:

        if emergency["id"] == emergency_id:

            emergency["status"] = data.status

            emergency["updated_at"] = (
                datetime.now().isoformat()
            )

            return {
                "success": True,
                "message": "Durum güncellendi.",
                "emergency": emergency,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# ASSIGN TEAM
# =========================================================

@app.patch("/emergencies/{emergency_id}/assign")
def assign_team(emergency_id: str):

    for emergency in emergencies:

        if emergency["id"] == emergency_id:

            emergency["team"] = (
                emergency["service"]
            )

            if emergency["status"] == "Yeni":
                emergency["status"] = "Ekip Atandı"

            emergency["updated_at"] = (
                datetime.now().isoformat()
            )

            return {
                "success": True,
                "message": "Ekip başarıyla atandı.",
                "emergency": emergency,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# DELETE EMERGENCY
# =========================================================

@app.delete("/emergencies/{emergency_id}")
def delete_emergency(emergency_id: str):

    for index, emergency in enumerate(emergencies):

        if emergency["id"] == emergency_id:

            deleted = emergencies.pop(index)

            return {
                "success": True,
                "message": "Acil durum silindi.",
                "emergency": deleted,
            }

    raise HTTPException(
        status_code=404,
        detail="Acil durum bulunamadı.",
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "backend": True,
        "emergencies": len(emergencies),
        "time": datetime.now().isoformat(),
    }


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )