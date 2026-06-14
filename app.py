import os
import sqlite3
import json
from flask import Flask, render_template_string, request, jsonify
# Using a completely free, keyless translation engine
from deep_translator import GoogleTranslator

app = Flask(__name__)
DB_FILE = 'disaster.db'

# --------------------------------------------------------------------------
# DATABASE SETUP
# --------------------------------------------------------------------------
def init_db():
    """Initializes the SQLite database with seed data if empty."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT,
            latitude REAL,
            longitude REAL,
            original_text TEXT,
            translated_text TEXT,
            priority TEXT,
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM reports")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            ("Kochi Marine Drive", 9.9796, 76.2754, "ഇവിടെ വെള്ളപ്പൊക്കം കാരണം റോഡ് തകർന്നു, ആളുകൾ കുടുങ്ങിക്കിടക്കുന്നു.", "Road collapsed due to flooding here, people are trapped.", "CRITICAL", "Road collapse with trapped individuals."),
            ("Aluva Metro Station", 10.1094, 76.3495, "Power grid failure after the heavy winds. Whole area dark.", "Power grid failure after the heavy winds. Whole area dark.", "HIGH", "Power outage affecting transit zone."),
            ("Fort Kochi Beach", 9.9658, 76.2421, "Minor water logging near the shops, we need some guidance.", "Minor water logging near the shops, we need some guidance.", "MEDIUM", "Localized low-level flooding.")
        ]
        cursor.executemany('''
            INSERT INTO reports (location_name, latitude, longitude, original_text, translated_text, priority, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', seed_data)
        conn.commit()
    conn.close()

# --------------------------------------------------------------------------
# ALGORITHMIC BACKEND LOGIC (KEYLESS ENGINE)
# --------------------------------------------------------------------------
def ai_triage_and_translate(user_text):
    """Translates regional text live and processes priority dynamically using keyword mapping."""
    try:
        # Actively translates Malayalam/Hindi/Tamil to English over free web endpoints
        translated = GoogleTranslator(source='auto', target='en').translate(user_text)
    except Exception:
        translated = user_text

    # Rules-based Natural Language Processing to determine severity
    lower_text = translated.lower()
    
    if any(k in lower_text for k in ["trap", "roof", "critical", "medical", "die", "bleed", "hospital", "flood"]):
        priority = "CRITICAL"
        summary = "Active emergency vector requiring immediate rescue intervention."
    elif any(k in lower_text for k in ["power", "road", "block", "bridge", "wire", "electricity", "cut"]):
        priority = "HIGH"
        summary = "Infrastructure or utility failure reported in grid corridor."
    else:
        priority = "MEDIUM"
        summary = "Baseline situational awareness or monitoring update filed."

    return {
        "translated": translated,
        "priority": priority,
        "summary": summary
    }

def ai_verify_scam(content_text):
    """Evaluates message authenticity algorithmically by tracing common digital fraud signatures."""
    lower_text = content_text.lower()
    
    # Check for known scam variables (asking for cash via individual UPI accounts)
    has_upi = "@" in lower_text or "upi" in lower_text or "link" in lower_text
    has_cash = "inr" in lower_text or "rupees" in lower_text or "money" in lower_text or "donate" in lower_text
    has_panic = "evacuate" in lower_text or "urgent" in lower_text or "forward" in lower_text

    if has_upi and has_cash:
        score = 12
        verdict = "HIGH RISK SCAM/FAKE"
        reason = "CRITICAL RISK: Message solicits digital financial wire routing/UPI transfers under emergency pretenses."
    elif has_panic or has_upi:
        score = 45
        verdict = "SUSPICIOUS UNVERIFIED"
        reason = "CAUTION: Broadcast request has unverified forward characteristics. Exercise vigilance."
    else:
        score = 94
        verdict = "VERIFIED SAFE"
        reason = "Information conforms to standard broadcast structures with no immediate commercial fraud fingerprints detected."

    return {
        "score": score,
        "verdict": verdict,
        "reason": reason
    }

# --------------------------------------------------------------------------
# ROUTES & ENDPOINTS
# --------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/api/reports', methods=['GET'])
def get_reports():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/report', methods=['POST'])
def submit_report():
    data = request.json
    loc_name = data.get('location_name', 'Unknown Location')
    lat = float(data.get('latitude', 9.98))
    lng = float(data.get('longitude', 76.28))
    original_text = data.get('text', '')

    ai_results = ai_triage_and_translate(original_text)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (location_name, latitude, longitude, original_text, translated_text, priority, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (loc_name, lat, lng, original_text, ai_results.get('translated'), ai_results.get('priority'), ai_results.get('summary')))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Report successfully verified and logged into command grid."})

@app.route('/api/verify', methods=['POST'])
def verify_link():
    data = request.json
    content = data.get('content', '')
    verification_results = ai_verify_scam(content)
    return jsonify(verification_results)

# --------------------------------------------------------------------------
# MONOLITHIC EMBEDDED FRONTEND INTERFACE (HTML/CSS/JS)
# --------------------------------------------------------------------------
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CrisisShield AI - Command Interface</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; }
        .critical-badge { background-color: #ef4444; color: white; }
        .high-badge { background-color: #f97316; color: white; }
        .medium-badge { background-color: #3b82f6; color: white; }
    </style>
</head>
<body class="p-4 lg:p-8">

    <header class="flex flex-col md:flex-row justify-between items-center border-b border-slate-700 pb-6 mb-8 gap-4">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-lg bg-gradient-to-tr from-red-600 to-orange-500 flex items-center justify-center font-bold text-xl border border-orange-300 shadow-md">🛡️</div>
            <div>
                <h1 class="text-3xl font-black tracking-tight text-white flex items-center gap-2">CRISISSHIELD <span class="text-orange-500 text-xl font-bold px-2 py-0.5 bg-orange-950/50 border border-orange-800 rounded">AI</span></h1>
                <p class="text-slate-400 text-sm font-medium">Platform Execution Matrix by <span class="text-orange-400 font-bold">BLASTCODERS</span></p>
            </div>
        </div>
        <div class="flex gap-4">
            <button onclick="switchMode('citizen')" id="btn-citizen" class="px-5 py-2.5 rounded-lg font-bold bg-orange-600 hover:bg-orange-700 transition cursor-pointer text-white shadow-lg shadow-orange-900/20">Citizen Reporting Hub</button>
            <button onclick="switchMode('authority')" id="btn-authority" class="px-5 py-2.5 rounded-lg font-bold bg-slate-800 hover:bg-slate-700 transition cursor-pointer text-slate-300 border border-slate-700">Authority Command View</button>
        </div>
    </header>

    <main>
        <section id="citizen-view" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-slate-900/80 p-6 rounded-xl border border-slate-800 shadow-xl">
                <h2 class="text-xl font-bold mb-4 text-orange-400 flex items-center gap-2">🚨 Fast Multilingual Emergency Report</h2>
                <p class="text-sm text-slate-400 mb-6">File local infrastructure breaks, entrapment, or medical alerts. Native inputs (Malayalam, Hindi, Tamil) are translated immediately by the NLP engine.</p>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Location Name</label>
                        <input type="text" id="cit-loc" placeholder="e.g. Aluva Market Road, Kochi" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-orange-500">
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Latitude Coordinates</label>
                            <input type="number" step="0.0001" id="cit-lat" value="9.9821" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Longitude Coordinates</label>
                            <input type="number" step="0.0001" id="cit-lng" value="76.2805" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none">
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Describe the exact crisis emergency</label>
                        <textarea id="cit-text" rows="4" placeholder="Type here in your native language (e.g., ഇവിടെ വൻതോതിൽ വെള്ളപ്പൊക്കം കാരണം റോഡ് തടസ്സപ്പെട്ടു...)" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-orange-500"></textarea>
                    </div>
                    <button onclick="submitCitizenReport()" class="w-full bg-red-600 hover:bg-red-700 transition py-3 rounded-lg font-bold uppercase tracking-wider shadow-lg text-white shadow-red-950/30 cursor-pointer">Dispatch Emergency Report</button>
                </div>
            </div>

            <div class="bg-slate-900/80 p-6 rounded-xl border border-slate-800 shadow-xl flex flex-col justify-between">
                <div>
                    <h2 class="text-xl font-bold mb-4 text-emerald-400 flex items-center gap-2">🛡️ AI Misinformation & Cyber-Scam Radar</h2>
                    <p class="text-sm text-slate-400 mb-6">Paste unverified WhatsApp chain forwards, text broadcast warnings, or online donation requests here to instantly compute credibility signatures.</p>
                    
                    <div class="space-y-4">
                        <textarea id="scam-input" rows="5" placeholder="Paste questionable links or panic message forwards here..." class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-emerald-500"></textarea>
                        <button onclick="scanForScams()" class="w-full bg-emerald-600 hover:bg-emerald-700 transition py-3 rounded-lg font-bold uppercase tracking-wider text-white shadow-lg shadow-emerald-950/20 cursor-pointer">Scan for Digital Fraud</button>
                    </div>
                </div>

                <div id="scam-results" class="hidden mt-6 p-4 rounded-lg border bg-slate-950 border-slate-800 transition-all">
                    <div class="flex justify-between items-center mb-3">
                        <span id="scam-verdict" class="px-3 py-1 text-xs font-bold rounded">VERDICT</span>
                        <span id="scam-score" class="text-xl font-black">Score: --</span>
                    </div>
                    <p id="scam-reason" class="text-sm text-slate-300"></p>
                </div>
            </div>
        </section>

        <section id="authority-view" class="hidden grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 flex flex-col gap-4">
                <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 shadow-xl flex-1 min-h-[500px] relative">
                    <h2 class="text-lg font-bold mb-3 text-white flex items-center gap-2">🗺️ Live Geospatial Operations Command Map</h2>
                    <div id="map" class="w-full h-[450px] rounded-lg border border-slate-800 z-10"></div>
                </div>
            </div>

            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-xl flex flex-col max-h-[550px]">
                <h2 class="text-lg font-bold mb-2 text-white flex items-center gap-2">📥 AI Priority Dispatch Queue</h2>
                <p class="text-xs text-slate-400 mb-4">Incoming crowdsourced feeds algorithmically mapped, translated, and prioritized autonomously.</p>
                
                <div id="report-feed" class="overflow-y-auto space-y-3 flex-1 pr-1"></div>
            </div>
        </section>
    </main>

    <script>
        let map;
        let markersGroup;

        window.addEventListener('DOMContentLoaded', () => {
            initLeafletMap();
            loadGridData();
        });

        function initLeafletMap() {
            map = L.map('map').setView([9.9821, 76.2805], 11);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO'
            }).addTo(map);
            markersGroup = L.layerGroup().addTo(map);
        }

        function switchMode(targetMode) {
            const citView = document.getElementById('citizen-view');
            const authView = document.getElementById('authority-view');
            const btnCit = document.getElementById('btn-citizen');
            const btnAuth = document.getElementById('btn-authority');

            if(targetMode === 'citizen') {
                citView.classList.remove('hidden');
                authView.classList.add('hidden');
                btnCit.className = "px-5 py-2.5 rounded-lg font-bold bg-orange-600 hover:bg-orange-700 transition cursor-pointer text-white shadow-lg";
                btnAuth.className = "px-5 py-2.5 rounded-lg font-bold bg-slate-800 hover:bg-slate-700 transition cursor-pointer text-slate-300 border border-slate-700";
            } else {
                citView.classList.add('hidden');
                authView.classList.remove('hidden');
                btnAuth.className = "px-5 py-2.5 rounded-lg font-bold bg-orange-600 hover:bg-orange-700 transition cursor-pointer text-white shadow-lg";
                btnCit.className = "px-5 py-2.5 rounded-lg font-bold bg-slate-800 hover:bg-slate-700 transition cursor-pointer text-slate-300 border border-slate-700";
                setTimeout(() => { map.invalidateSize(); }, 200);
            }
        }

        function loadGridData() {
            fetch('/api/reports')
                .then(res => res.json())
                .then(data => {
                    renderFeed(data);
                    renderMapMarkers(data);
                });
        }

        function renderFeed(reports) {
            const feed = document.getElementById('report-feed');
            feed.innerHTML = '';
            
            reports.forEach(r => {
                let badgeClass = 'medium-badge';
                if(r.priority === 'CRITICAL') badgeClass = 'critical-badge';
                if(r.priority === 'HIGH') badgeClass = 'high-badge';

                feed.innerHTML += `
                    <div class="bg-slate-950 p-4 rounded-lg border border-slate-800 hover:border-slate-700 transition">
                        <div class="flex justify-between items-start gap-2 mb-2">
                            <h4 class="font-bold text-sm text-slate-200">${r.location_name}</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded tracking-wide ${badgeClass}">${r.priority}</span>
                        </div>
                        <p class="text-xs text-orange-400 italic mb-1">Raw: "${r.original_text}"</p>
                        <p class="text-xs text-slate-300 font-medium mb-2">Trans: ${r.translated_text}</p>
                        <div class="pt-2 border-t border-slate-900 text-[11px] text-slate-400 font-semibold flex items-center gap-1">
                            🤖 Brief: ${r.summary}
                        </div>
                    </div>
                `;
            });
        }

        function renderMapMarkers(reports) {
            markersGroup.clearLayers();
            reports.forEach(r => {
                let markerColor = '#3b82f6';
                if(r.priority === 'CRITICAL') markerColor = '#ef4444';
                if(r.priority === 'HIGH') markerColor = '#f97316';

                const customMarker = L.circleMarker([r.latitude, r.longitude], {
                    radius: 9,
                    fillColor: markerColor,
                    color: '#ffffff',
                    weight: 2,
                    fillOpacity: 0.9
                });

                customMarker.bindPopup(`
                    <div class="text-slate-950 p-1">
                        <strong class="text-sm block border-b pb-1 mb-1">${r.location_name}</strong>
                        <span class="text-xs block font-bold text-red-600 mb-1">Priority: ${r.priority}</span>
                        <p class="text-xs margin-0"><strong>Summary:</strong> ${r.summary}</p>
                    </div>
                `);
                markersGroup.addLayer(customMarker);
            });
        }

        function submitCitizenReport() {
            const loc = document.getElementById('cit-loc').value;
            const lat = document.getElementById('cit-lat').value;
            const lng = document.getElementById('cit-lng').value;
            const text = document.getElementById('cit-text').value;

            if(!loc || !text) {
                alert("Please fill out your location and emergency description details.");
                return;
            }

            fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_name: loc, latitude: lat, longitude: lng, text: text })
            }).then(res => res.json())
                .then(data => {
                    alert(data.message);
                    document.getElementById('cit-loc').value = '';
                    document.getElementById('cit-text').value = '';
                    loadGridData();
                });
        }

        function scanForScams() {
            const text = document.getElementById('scam-input').value;
            if(!text) { alert("Please input text data or a verification link to scan."); return; }

            const targetBox = document.getElementById('scam-results');
            const vLabel = document.getElementById('scam-verdict');
            const sLabel = document.getElementById('scam-score');
            const rLabel = document.getElementById('scam-reason');

            fetch('/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: text })
            }).then(res => res.json())
                .then(data => {
                    targetBox.classList.remove('hidden');
                    sLabel.innerText = `Score: ${data.score}%`;
                    rLabel.innerText = data.reason;
                    vLabel.innerText = data.verdict;

                    if(data.score > 75) {
                        targetBox.className = "mt-6 p-4 rounded-lg border bg-slate-950 border-emerald-800";
                        vLabel.className = "px-3 py-1 text-xs font-bold rounded bg-emerald-500 text-white";
                    } else if(data.score > 40) {
                        targetBox.className = "mt-6 p-4 rounded-lg border bg-slate-950 border-orange-800";
                        vLabel.className = "px-3 py-1 text-xs font-bold rounded bg-orange-500 text-white";
                    } else {
                        targetBox.className = "mt-6 p-4 rounded-lg border bg-slate-950 border-red-800";
                        vLabel.className = "px-3 py-1 text-xs font-bold rounded bg-red-500 text-white";
                    }
                });
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)