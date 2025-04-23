from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)
AHREFS_API_TOKEN = "your_ahrefs_api_key_here"

def get_ahrefs_metrics(domain):
    url = f"https://apiv2.ahrefs.com?token={AHREFS_API_TOKEN}&target={domain}&from=domain_rating&mode=domain"
    response = requests.get(url)
    return response.json()

def get_wayback_snapshots(domain):
    url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&fl=timestamp,statuscode&filter=statuscode:200&collapse=timestamp:8"
    response = requests.get(url)
    if response.ok:
        data = response.json()[1:]
        timestamps = [entry[0] for entry in data]
        return timestamps
    return []

def check_redirect(domain):
    try:
        response = requests.get(f"http://{domain}", timeout=10, allow_redirects=False)
        return response.status_code in [301, 302]
    except:
        return False

@app.route("/api/check-domain", methods=["POST"])
def check_domain():
    data = request.get_json()
    domain = data.get("domain")
    if not domain:
        return jsonify({"error": "Domain is required."}), 400

    try:
        ahrefs_data = get_ahrefs_metrics(domain)
        wayback_timestamps = get_wayback_snapshots(domain)
        redirected = check_redirect(domain)

        dr = ahrefs_data.get("domain_rating", 0)
        if wayback_timestamps:
            first_seen = datetime.strptime(wayback_timestamps[0], "%Y%m%d")
            age_years = int((datetime.now() - first_seen).days / 365)
            last_seen = datetime.strptime(wayback_timestamps[-1], "%Y%m%d")
            gap_days = (datetime.now() - last_seen).days
            recent_activity = f"{gap_days} days ago"
        else:
            age_years = 0
            recent_activity = "No data"

        return jsonify({
            "domain": domain,
            "dr": dr,
            "age": age_years,
            "backlinks70plus": "Check via Ahrefs backlinks endpoint",
            "recentActivity": recent_activity,
            "redirect301": redirected
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)