from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from datetime import datetime

app = FastAPI()

AHREFS_API_TOKEN = os.getenv("AHREFS_API_TOKEN", "your_ahrefs_token")

class DomainRequest(BaseModel):
    domain: str

@app.post("/check-domain")
def check_domain(data: DomainRequest):
    domain = data.domain.strip()
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")

    try:
        ahrefs_url = f"https://apiv2.ahrefs.com?token={AHREFS_API_TOKEN}&target={domain}&from=domain_rating&mode=domain"
        ahrefs_response = requests.get(ahrefs_url)
        ahrefs_data = ahrefs_response.json()
        dr = ahrefs_data.get("domain_rating", 0)

        wb_url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&fl=timestamp,statuscode&filter=statuscode:200&collapse=timestamp:8"
        wb_response = requests.get(wb_url)
        timestamps = wb_response.json()[1:] if wb_response.ok else []

        if timestamps:
            first_seen = datetime.strptime(timestamps[0][0], "%Y%m%d")
            last_seen = datetime.strptime(timestamps[-1][0], "%Y%m%d")
            age_years = (datetime.now() - first_seen).days // 365
            recent_gap = (datetime.now() - last_seen).days
            recent_activity = f"{recent_gap} days ago"
        else:
            age_years = 0
            recent_activity = "No archive found"

        try:
            redirect_check = requests.get(f"http://{domain}", timeout=10, allow_redirects=False)
            is_redirected = redirect_check.status_code in [301, 302]
        except:
            is_redirected = None

        return {
            "domain": domain,
            "dr": dr,
            "age": age_years,
            "recent_activity": recent_activity,
            "redirect_301": is_redirected
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))