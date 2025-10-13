"""
Dashboard for EV Central - FastAPI web interface.
Provides real-time view of charging points and telemetry.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import TYPE_CHECKING
from loguru import logger

from evcharging.common.messages import CPRegistration

if TYPE_CHECKING:
    from evcharging.apps.ev_central.main import EVCentralController


def create_dashboard_app(controller: "EVCentralController") -> FastAPI:
    """Create FastAPI application for dashboard."""
    
    app = FastAPI(title="EV Central Dashboard", version="0.1.0")
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": "ev-central"}
    
    @app.post("/cp/register")
    async def register_cp(registration: CPRegistration):
        """Register or update a charging point."""
        success = controller.register_cp(registration)
        return {
            "success": success,
            "cp_id": registration.cp_id,
            "message": "Charging point registered successfully" if success else "Registration failed"
        }
    
    @app.get("/cp")
    async def list_charging_points():
        """List all charging points and their current state."""
        data = controller.get_dashboard_data()
        return {
            "charging_points": data["charging_points"],
            "active_requests": data["active_requests"]
        }
    
    @app.get("/cp/{cp_id}")
    async def get_charging_point(cp_id: str):
        """Get detailed information about a specific charging point."""
        if cp_id not in controller.charging_points:
            return {"error": "Charging point not found"}, 404
        
        cp = controller.charging_points[cp_id]
        return {
            "cp_id": cp.cp_id,
            "state": cp.state.value,
            "current_driver": cp.current_driver,
            "current_session": cp.current_session,
            "last_update": cp.last_update.isoformat(),
            "telemetry": (
                {
                    "kw": cp.last_telemetry.kw,
                    "euros": cp.last_telemetry.euros,
                    "driver_id": cp.last_telemetry.driver_id,
                    "session_id": cp.last_telemetry.session_id,
                    "ts": cp.last_telemetry.ts.isoformat(),
                }
                if cp.last_telemetry
                else None
            ),
        }
    
    @app.get("/telemetry")
    async def get_telemetry():
        """Get current telemetry from all active charging sessions."""
        telemetry_list = []
        for cp in controller.charging_points.values():
            if cp.last_telemetry:
                telemetry_list.append({
                    "cp_id": cp.cp_id,
                    "kw": cp.last_telemetry.kw,
                    "euros": cp.last_telemetry.euros,
                    "driver_id": cp.last_telemetry.driver_id,
                    "session_id": cp.last_telemetry.session_id,
                    "ts": cp.last_telemetry.ts.isoformat(),
                })
        return {"telemetry": telemetry_list}
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home(request: Request):
        """Main dashboard HTML page."""
        data = controller.get_dashboard_data()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EV Central Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                h1 {{
                    color: #667eea;
                    margin-top: 0;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 15px;
                }}
                .stats {{
                    display: flex;
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    flex: 1;
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                .stat-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .cp-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }}
                .cp-card {{
                    background: #fff;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 20px;
                    transition: all 0.3s;
                }}
                .cp-card:hover {{
                    border-color: #667eea;
                    box-shadow: 0 5px 15px rgba(102,126,234,0.3);
                    transform: translateY(-2px);
                }}
                .cp-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }}
                .cp-id {{
                    font-size: 1.2em;
                    font-weight: bold;
                    color: #333;
                }}
                .state-badge {{
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 0.85em;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .state-ACTIVATED {{ background: #4caf50; color: white; }}
                .state-SUPPLYING {{ background: #2196f3; color: white; animation: pulse 2s infinite; }}
                .state-STOPPED {{ background: #ff9800; color: white; }}
                .state-FAULT {{ background: #f44336; color: white; }}
                .state-DISCONNECTED {{ background: #9e9e9e; color: white; }}
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                }}
                .telemetry {{
                    background: #f0f4ff;
                    padding: 12px;
                    border-radius: 6px;
                    margin-top: 10px;
                }}
                .telemetry-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 5px 0;
                }}
                .telemetry-label {{
                    color: #666;
                    font-weight: 500;
                }}
                .telemetry-value {{
                    color: #333;
                    font-weight: bold;
                }}
                .driver-info {{
                    color: #667eea;
                    font-style: italic;
                    margin-top: 10px;
                }}
                .refresh-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 1em;
                    margin-top: 20px;
                }}
                .refresh-btn:hover {{
                    background: #5568d3;
                }}
            </style>
            <script>
                function refresh() {{
                    location.reload();
                }}
                // Auto-refresh every 2 seconds
                setTimeout(() => {{ location.reload(); }}, 2000);
            </script>
        </head>
        <body>
            <div class="container">
                <h1>⚡ EV Central Dashboard</h1>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">{len(data['charging_points'])}</div>
                        <div class="stat-label">Total Charging Points</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{data['active_requests']}</div>
                        <div class="stat-label">Active Requests</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{sum(1 for cp in data['charging_points'] if cp['state'] == 'SUPPLYING')}</div>
                        <div class="stat-label">Currently Charging</div>
                    </div>
                </div>
                
                <h2>Charging Points</h2>
                <div class="cp-grid">
        """
        
        for cp in data['charging_points']:
            telemetry_html = ""
            if cp.get('telemetry'):
                t = cp['telemetry']
                telemetry_html = f"""
                    <div class="telemetry">
                        <div class="telemetry-row">
                            <span class="telemetry-label">Power:</span>
                            <span class="telemetry-value">{t['kw']:.2f} kW</span>
                        </div>
                        <div class="telemetry-row">
                            <span class="telemetry-label">Cost:</span>
                            <span class="telemetry-value">€{t['euros']:.2f}</span>
                        </div>
                        <div class="telemetry-row">
                            <span class="telemetry-label">Session:</span>
                            <span class="telemetry-value">{t.get('session_id', 'N/A')}</span>
                        </div>
                    </div>
                """
            
            driver_html = f'<div class="driver-info">👤 Driver: {cp["current_driver"]}</div>' if cp.get('current_driver') else ''
            
            html_content += f"""
                    <div class="cp-card">
                        <div class="cp-header">
                            <div class="cp-id">{cp['cp_id']}</div>
                            <span class="state-badge state-{cp['state']}">{cp['state']}</span>
                        </div>
                        {driver_html}
                        {telemetry_html}
                    </div>
            """
        
        html_content += """
                </div>
                
                <button class="refresh-btn" onclick="refresh()">🔄 Refresh Now</button>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    return app
