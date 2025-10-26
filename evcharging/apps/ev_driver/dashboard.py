"""Driver dashboard FastAPI app bound to an ``EVDriver`` instance."""

from datetime import datetime
from typing import List, Literal, Optional, TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

if TYPE_CHECKING:  # pragma: no cover
    from evcharging.apps.ev_driver.main import EVDriver


class Location(BaseModel):
    address: str
    city: str
    latitude: float
    longitude: float
    distance_km: Optional[float] = Field(default=None, description="Distance from driver in km")


class ChargingPointStatus(BaseModel):
    cp_id: str
    name: str
    status: Literal["FREE", "OCCUPIED", "OFFLINE"]
    power_kw: float
    connector_type: str
    location: Location
    queue_length: int = Field(default=0, ge=0)
    estimated_wait_minutes: int = Field(default=0, ge=0)
    favorite: bool = False


class ChargingPointDetail(ChargingPointStatus):
    amenities: List[str] = Field(default_factory=list)
    price_eur_per_kwh: float = 0.0
    last_updated: datetime


class SessionSummary(BaseModel):
    session_id: str
    request_id: str
    cp_id: str
    status: Literal[
        "PENDING",
        "APPROVED",
        "CHARGING",
        "COMPLETED",
        "DENIED",
        "FAILED",
        "STOPPED",
        "CANCELLED",
    ]
    queue_position: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    energy_kwh: Optional[float] = None
    cost_eur: Optional[float] = None


class SessionHistoryEntry(SessionSummary):
    receipt_url: Optional[str] = None


class RequestPayload(BaseModel):
    cp_id: str
    vehicle_id: str
    preferred_start: Optional[datetime] = None


class FavoritePayload(BaseModel):
    cp_id: str


class Notification(BaseModel):
    notification_id: str
    created_at: datetime
    message: str
    type: Literal["SESSION", "QUEUE", "ALERT"]
    read: bool = False


class BroadcastAlert(BaseModel):
    alert_id: str
    title: str
    message: str
    severity: Literal["INFO", "WARN", "CRITICAL"]
    effective_at: datetime
    expires_at: Optional[datetime] = None


def create_driver_dashboard_app(driver: "EVDriver") -> FastAPI:
    """Bind the REST API to a running ``EVDriver`` instance."""

    app = FastAPI(
        title="Driver Dashboard API",
        version="1.0.0",
        description="Driver self-service endpoints for live session management.",
    )

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "driver-dashboard"}

    # ------------------------------------------------------------------
    # Charging point discovery
    # ------------------------------------------------------------------

    @app.get("/charging-points", response_model=List[ChargingPointDetail])
    async def list_charging_points(
        city: Optional[str] = Query(None, description="Filter by city"),
        connector_type: Optional[str] = Query(None, description="Filter by connector type"),
        min_power_kw: Optional[float] = Query(None, ge=0, description="Filter by minimum power"),
        only_available: bool = Query(False, description="Return only FREE points"),
    ):
        points = await driver.dashboard_charging_points(
            city=city,
            connector_type=connector_type,
            min_power_kw=min_power_kw,
            only_available=only_available,
        )
        return points

    @app.get("/charging-points/{cp_id}", response_model=ChargingPointDetail)
    async def get_charging_point(cp_id: str):
        try:
            return await driver.dashboard_charging_point(cp_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Charging point not found")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    @app.post("/drivers/{driver_id}/requests", response_model=SessionSummary, status_code=202)
    async def request_session(driver_id: str, payload: RequestPayload):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        driver_request = await driver.send_request(payload.cp_id)
        summary = await driver.dashboard_request_summary(driver_request.request_id)
        return summary

    @app.delete("/drivers/{driver_id}/requests/{request_id}", status_code=204)
    async def cancel_request(driver_id: str, request_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        cancelled = await driver.dashboard_cancel_request(request_id)
        if not cancelled:
            raise HTTPException(status_code=404, detail="Request not found or already active")

    @app.get("/drivers/{driver_id}/sessions/current", response_model=Optional[SessionSummary])
    async def current_session(driver_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        return await driver.dashboard_current_session()

    @app.post("/drivers/{driver_id}/sessions/{session_id}/stop", response_model=SessionSummary)
    async def stop_session(driver_id: str, session_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        summary = await driver.dashboard_stop_session(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Session not found")
        return summary

    @app.get("/drivers/{driver_id}/sessions/history", response_model=List[SessionHistoryEntry])
    async def session_history(driver_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        return await driver.dashboard_session_history()

    # ------------------------------------------------------------------
    # Favorites & personalization
    # ------------------------------------------------------------------

    @app.get("/drivers/{driver_id}/favorites", response_model=List[ChargingPointStatus])
    async def list_favorites(driver_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        return await driver.dashboard_favorites()

    @app.post("/drivers/{driver_id}/favorites", status_code=204)
    async def add_favorite(driver_id: str, payload: FavoritePayload):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        await driver.dashboard_add_favorite(payload.cp_id)

    @app.delete("/drivers/{driver_id}/favorites/{cp_id}", status_code=204)
    async def remove_favorite(driver_id: str, cp_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        await driver.dashboard_remove_favorite(cp_id)

    # ------------------------------------------------------------------
    # Notifications and alerts
    # ------------------------------------------------------------------

    @app.get("/drivers/{driver_id}/notifications", response_model=List[Notification])
    async def list_notifications(driver_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        return await driver.dashboard_notifications()

    @app.get("/drivers/{driver_id}/alerts", response_model=List[BroadcastAlert])
    async def list_alerts(driver_id: str):
        if driver_id != driver.driver_id:
            raise HTTPException(status_code=404, detail="Driver not found")
        return await driver.dashboard_alerts()

    # ------------------------------------------------------------------
    # HTML Dashboard
    # ------------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    async def driver_dashboard_home(request: Request):
        """Interactive HTML dashboard for drivers."""
        driver_id = driver.driver_id
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🚗 Driver Dashboard - {driver_id}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                
                h1 {{
                    color: #667eea;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .driver-badge {{
                    background: #764ba2;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.9em;
                }}
                
                .status-bar {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #667eea;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .last-update {{
                    font-size: 0.9em;
                    color: #999;
                }}
                
                .active-session {{
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                    padding: 25px;
                    border-radius: 12px;
                    border-left: 6px solid #2196f3;
                    margin-bottom: 25px;
                    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
                }}
                
                .active-session h3 {{
                    color: #1976d2;
                    margin-bottom: 15px;
                    font-size: 1.3em;
                }}
                
                .session-info {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                    gap: 15px;
                    margin-bottom: 15px;
                }}
                
                .info-item {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .info-label {{
                    color: #666;
                    font-size: 0.85em;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                    font-weight: 600;
                }}
                
                .info-value {{
                    color: #333;
                    font-size: 1.4em;
                    font-weight: bold;
                }}
                
                .filters {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 25px;
                }}
                
                .filters h2 {{
                    color: #764ba2;
                    margin-bottom: 15px;
                    font-size: 1.3em;
                }}
                
                .filter-row {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 15px;
                }}
                
                .filter-group {{
                    display: flex;
                    flex-direction: column;
                }}
                
                .filter-group label {{
                    color: #666;
                    font-size: 0.9em;
                    margin-bottom: 5px;
                    font-weight: 600;
                }}
                
                .filter-group select,
                .filter-group input {{
                    padding: 10px;
                    border: 2px solid #ddd;
                    border-radius: 6px;
                    font-size: 1em;
                    transition: border-color 0.3s;
                }}
                
                .filter-group select:focus,
                .filter-group input:focus {{
                    outline: none;
                    border-color: #667eea;
                }}
                
                .cp-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                
                .cp-card {{
                    background: #fff;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 20px;
                    transition: all 0.3s;
                    cursor: pointer;
                    position: relative;
                }}
                
                .cp-card:hover {{
                    border-color: #667eea;
                    box-shadow: 0 8px 20px rgba(102,126,234,0.3);
                    transform: translateY(-3px);
                }}
                
                .cp-card.favorite {{
                    border-color: #ffd700;
                    background: #fffef0;
                }}
                
                .cp-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 15px;
                }}
                
                .cp-id {{
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #333;
                }}
                
                .cp-name {{
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 2px;
                }}
                
                .favorite-btn {{
                    background: none;
                    border: none;
                    font-size: 1.8em;
                    cursor: pointer;
                    color: #ccc;
                    transition: all 0.3s;
                }}
                
                .favorite-btn.active {{
                    color: #ffd700;
                    transform: scale(1.2);
                }}
                
                .favorite-btn:hover {{
                    transform: scale(1.3);
                }}
                
                .status-badge {{
                    display: inline-block;
                    padding: 6px 14px;
                    border-radius: 20px;
                    font-size: 0.85em;
                    font-weight: bold;
                    text-transform: uppercase;
                    margin-bottom: 12px;
                }}
                
                .status-FREE {{ background: #4caf50; color: white; }}
                .status-OCCUPIED {{ background: #ff9800; color: white; }}
                .status-OFFLINE {{ background: #f44336; color: white; }}
                
                .cp-location {{
                    color: #667eea;
                    font-weight: 600;
                    margin-bottom: 12px;
                    font-size: 0.95em;
                }}
                
                .cp-details {{
                    color: #666;
                    line-height: 1.8;
                    font-size: 0.95em;
                }}
                
                .cp-detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 8px 0;
                    padding: 5px 0;
                    border-bottom: 1px solid #f0f0f0;
                }}
                
                .cp-detail-row:last-child {{
                    border-bottom: none;
                }}
                
                .request-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 1em;
                    font-weight: 600;
                    margin-top: 15px;
                    width: 100%;
                    transition: all 0.3s;
                }}
                
                .request-btn:hover {{
                    background: #5568d3;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(102,126,234,0.4);
                }}
                
                .request-btn:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }}
                
                .stop-btn {{
                    background: #f44336;
                }}
                
                .stop-btn:hover {{
                    background: #da190b;
                }}
                
                .cancel-btn {{
                    background: #ff9800;
                }}
                
                .cancel-btn:hover {{
                    background: #f57c00;
                }}
                
                .section-header {{
                    color: #764ba2;
                    margin: 30px 0 15px 0;
                    font-size: 1.5em;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .count-badge {{
                    background: #e0e0e0;
                    color: #666;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 0.7em;
                }}
                
                .notifications {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    max-width: 400px;
                    z-index: 1000;
                }}
                
                .notification {{
                    background: white;
                    padding: 18px;
                    border-radius: 8px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
                    margin-bottom: 12px;
                    border-left: 5px solid #667eea;
                    animation: slideIn 0.4s ease-out;
                }}
                
                @keyframes slideIn {{
                    from {{
                        transform: translateX(450px);
                        opacity: 0;
                    }}
                    to {{
                        transform: translateX(0);
                        opacity: 1;
                    }}
                }}
                
                .notification.success {{ border-left-color: #4caf50; }}
                .notification.error {{ border-left-color: #f44336; }}
                .notification.warning {{ border-left-color: #ff9800; }}
                
                .notification-title {{
                    font-weight: bold;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                    font-size: 0.85em;
                }}
                
                .empty-state {{
                    text-align: center;
                    padding: 60px 20px;
                    color: #999;
                }}
                
                .empty-state-icon {{
                    font-size: 4em;
                    margin-bottom: 15px;
                }}
                
                .btn-group {{
                    display: flex;
                    gap: 10px;
                }}
                
                .btn-secondary {{
                    background: #9e9e9e;
                }}
                
                .btn-secondary:hover {{
                    background: #757575;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.6; }}
                }}
                
                .charging-indicator {{
                    animation: pulse 2s infinite;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>
                    <span>🚗 Driver Dashboard</span>
                    <span class="driver-badge">{driver_id}</span>
                </h1>
                
                <div class="status-bar">
                    <span>📡 Real-time updates enabled</span>
                    <span class="last-update">Last update: <span id="last-update">--:--:--</span></span>
                </div>
                
                <!-- Active Session -->
                <div id="active-session-container"></div>
                
                <!-- Filters -->
                <div class="filters">
                    <h2>🔍 Find Charging Points</h2>
                    <div class="filter-row">
                        <div class="filter-group">
                            <label>📍 City</label>
                            <input type="text" id="filter-city" placeholder="Enter city">
                        </div>
                        <div class="filter-group">
                            <label>🔌 Connector Type</label>
                            <select id="filter-connector">
                                <option value="">All Connectors</option>
                                <option value="Type 2">Type 2</option>
                                <option value="CCS">CCS</option>
                                <option value="CHAdeMO">CHAdeMO</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label>⚡ Min Power (kW)</label>
                            <input type="number" id="filter-min-power" placeholder="0" min="0">
                        </div>
                        <div class="filter-group">
                            <label>📊 Status</label>
                            <select id="filter-status">
                                <option value="">All Status</option>
                                <option value="FREE">Available</option>
                                <option value="OCCUPIED">Occupied</option>
                                <option value="OFFLINE">Offline</option>
                            </select>
                        </div>
                    </div>
                    <div class="btn-group">
                        <button class="request-btn" onclick="applyFilters()" style="width: auto;">Apply Filters</button>
                        <button class="request-btn btn-secondary" onclick="clearFilters()" style="width: auto;">Clear</button>
                    </div>
                </div>
                
                <!-- Favorites Section -->
                <div id="favorites-section" style="display: none;">
                    <h2 class="section-header">
                        <span>⭐ Favorite Charging Points</span>
                        <span class="count-badge" id="favorites-count">0</span>
                    </h2>
                    <div class="cp-grid" id="favorites-grid"></div>
                </div>
                
                <!-- All Charging Points -->
                <h2 class="section-header">
                    <span>⚡ All Charging Points</span>
                    <span class="count-badge" id="cp-count">0</span>
                </h2>
                <div class="cp-grid" id="cp-grid"></div>
            </div>
            
            <!-- Notifications Container -->
            <div class="notifications" id="notifications"></div>
            
            <script>
                const driverId = '{driver_id}';
                let chargingPoints = [];
                let favorites = new Set();
                let activeSession = null;
                
                function showNotification(message, type = 'info') {{
                    const container = document.getElementById('notifications');
                    const notification = document.createElement('div');
                    notification.className = `notification ${{type}}`;
                    notification.innerHTML = `
                        <div class="notification-title">${{type}}</div>
                        ${{message}}
                    `;
                    container.appendChild(notification);
                    
                    setTimeout(() => {{
                        notification.remove();
                    }}, 5000);
                }}
                
                async function loadChargingPoints() {{
                    try {{
                        const response = await fetch('/charging-points');
                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}
                        const data = await response.json();
                        console.log('Loaded charging points:', data);
                        if (!Array.isArray(data)) {{
                            throw new Error('Expected array of charging points');
                        }}
                        chargingPoints = data;
                        renderChargingPoints();
                    }} catch (error) {{
                        console.error('Error loading charging points:', error);
                        showNotification('Failed to load charging points', 'error');
                    }}
                }}
                
                async function loadFavorites() {{
                    try {{
                        const response = await fetch(`/drivers/${{driverId}}/favorites`);
                        const data = await response.json();
                        favorites = new Set(data.map(cp => cp.cp_id));
                        renderFavorites(data);
                    }} catch (error) {{
                        console.error('Error loading favorites:', error);
                    }}
                }}
                
                function renderFavorites(favCps) {{
                    const container = document.getElementById('favorites-section');
                    const grid = document.getElementById('favorites-grid');
                    const count = document.getElementById('favorites-count');
                    
                    if (favCps.length === 0) {{
                        container.style.display = 'none';
                        return;
                    }}
                    
                    container.style.display = 'block';
                    count.textContent = favCps.length;
                    grid.innerHTML = favCps.map(cp => renderCpCard(cp)).join('');
                }}
                
                function renderChargingPoints() {{
                    const grid = document.getElementById('cp-grid');
                    const count = document.getElementById('cp-count');
                    
                    count.textContent = chargingPoints.length;
                    
                    if (chargingPoints.length === 0) {{
                        grid.innerHTML = `
                            <div class="empty-state" style="grid-column: 1 / -1;">
                                <div class="empty-state-icon">🔍</div>
                                <div>No charging points found</div>
                            </div>
                        `;
                        return;
                    }}
                    
                    grid.innerHTML = chargingPoints.map(cp => renderCpCard(cp)).join('');
                }}
                
                function renderCpCard(cp) {{
                    const isFavorite = favorites.has(cp.cp_id);
                    const isDisabled = cp.status !== 'FREE' || activeSession;
                    
                    return `
                        <div class="cp-card ${{isFavorite ? 'favorite' : ''}}">
                            <div class="cp-header">
                                <div>
                                    <div class="cp-id">${{cp.cp_id}}</div>
                                    <div class="cp-name">${{cp.name}}</div>
                                </div>
                                <button 
                                    class="favorite-btn ${{isFavorite ? 'active' : ''}}" 
                                    onclick="toggleFavorite('${{cp.cp_id}}')"
                                    title="${{isFavorite ? 'Remove from favorites' : 'Add to favorites'}}"
                                >★</button>
                            </div>
                            
                            <div class="cp-location">📍 ${{cp.location.address}}, ${{cp.location.city}}</div>
                            <span class="status-badge status-${{cp.status}}">${{cp.status}}</span>
                            
                            <div class="cp-details">
                                <div class="cp-detail-row">
                                    <span>🔌 Connector:</span>
                                    <strong>${{cp.connector_type}}</strong>
                                </div>
                                <div class="cp-detail-row">
                                    <span>⚡ Power:</span>
                                    <strong>${{cp.power_kw}} kW</strong>
                                </div>
                                ${{cp.price_eur_per_kwh ? `
                                <div class="cp-detail-row">
                                    <span>💰 Price:</span>
                                    <strong>€${{cp.price_eur_per_kwh.toFixed(2)}}/kWh</strong>
                                </div>
                                ` : ''}}
                                ${{cp.distance_km ? `
                                <div class="cp-detail-row">
                                    <span>📏 Distance:</span>
                                    <strong>${{cp.distance_km.toFixed(1)}} km</strong>
                                </div>
                                ` : ''}}
                                ${{cp.queue_length > 0 ? `
                                <div class="cp-detail-row">
                                    <span>⏳ Queue:</span>
                                    <strong>${{cp.queue_length}} waiting</strong>
                                </div>
                                <div class="cp-detail-row">
                                    <span>⏱️ Wait Time:</span>
                                    <strong>~${{cp.estimated_wait_minutes}} min</strong>
                                </div>
                                ` : ''}}
                            </div>
                            
                            <button 
                                class="request-btn" 
                                onclick="requestSession('${{cp.cp_id}}')"
                                ${{isDisabled ? 'disabled' : ''}}
                            >
                                ${{cp.status === 'FREE' ? '🔌 Request Charging' : '⏳ ' + cp.status}}
                            </button>
                        </div>
                    `;
                }}
                
                async function loadActiveSession() {{
                    try {{
                        const response = await fetch(`/drivers/${{driverId}}/sessions/current`);
                        const data = await response.json();
                        activeSession = data;
                        renderActiveSession();
                        loadChargingPoints(); // Refresh to update button states
                    }} catch (error) {{
                        console.error('Error loading active session:', error);
                    }}
                }}
                
                function renderActiveSession() {{
                    const container = document.getElementById('active-session-container');
                    
                    if (!activeSession) {{
                        container.innerHTML = '';
                        return;
                    }}
                    
                    const statusDisplay = {{
                        'PENDING': '⏳ Pending Approval',
                        'APPROVED': '✅ Approved - Starting',
                        'CHARGING': '🔋 Charging',
                        'COMPLETED': '✔️ Completed',
                        'DENIED': '❌ Denied',
                        'FAILED': '⚠️ Failed'
                    }}[activeSession.status] || activeSession.status;
                    
                    const actionBtn = activeSession.status === 'PENDING' 
                        ? `<button class="request-btn cancel-btn" onclick="cancelSession('${{activeSession.request_id}}')">❌ Cancel Request</button>`
                        : activeSession.status === 'CHARGING'
                        ? `<button class="request-btn stop-btn" onclick="stopSession('${{activeSession.session_id}}')">⏹️ Stop Charging</button>`
                        : '';
                    
                    const isCharging = activeSession.status === 'CHARGING';
                    
                    container.innerHTML = `
                        <div class="active-session ${{isCharging ? 'charging-indicator' : ''}}">
                            <h3>🔋 Active Session: ${{activeSession.session_id}}</h3>
                            <div class="session-info">
                                <div class="info-item">
                                    <div class="info-label">Status</div>
                                    <div class="info-value">${{statusDisplay}}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Charging Point</div>
                                    <div class="info-value">${{activeSession.cp_id}}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Energy</div>
                                    <div class="info-value">${{(activeSession.energy_kwh || 0).toFixed(2)}} kWh</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Cost</div>
                                    <div class="info-value">€${{(activeSession.cost_eur || 0).toFixed(4)}}</div>
                                </div>
                                ${{activeSession.started_at ? `
                                <div class="info-item">
                                    <div class="info-label">Started</div>
                                    <div class="info-value" style="font-size: 0.9em;">${{new Date(activeSession.started_at).toLocaleTimeString()}}</div>
                                </div>
                                ` : ''}}
                            </div>
                            ${{actionBtn}}
                        </div>
                    `;
                }}
                
                async function requestSession(cpId) {{
                    try {{
                        const response = await fetch(`/drivers/${{driverId}}/requests`, {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                cp_id: cpId,
                                vehicle_id: 'vehicle-1'
                            }})
                        }});
                        
                        if (response.ok) {{
                            const data = await response.json();
                            showNotification(`Charging requested at ${{cpId}}`, 'success');
                            loadActiveSession();
                        }} else {{
                            showNotification('Failed to request session', 'error');
                        }}
                    }} catch (error) {{
                        console.error('Error requesting session:', error);
                        showNotification('Error requesting session', 'error');
                    }}
                }}
                
                async function cancelSession(requestId) {{
                    try {{
                        const response = await fetch(`/drivers/${{driverId}}/requests/${{requestId}}`, {{
                            method: 'DELETE'
                        }});
                        
                        if (response.ok) {{
                            showNotification('Session request cancelled', 'success');
                            loadActiveSession();
                        }} else {{
                            showNotification('Failed to cancel request', 'error');
                        }}
                    }} catch (error) {{
                        console.error('Error cancelling session:', error);
                        showNotification('Error cancelling session', 'error');
                    }}
                }}
                
                async function stopSession(sessionId) {{
                    try {{
                        const response = await fetch(`/drivers/${{driverId}}/sessions/${{sessionId}}/stop`, {{
                            method: 'POST'
                        }});
                        
                        if (response.ok) {{
                            showNotification('Charging session stopped', 'success');
                            loadActiveSession();
                        }} else {{
                            showNotification('Failed to stop session', 'error');
                        }}
                    }} catch (error) {{
                        console.error('Error stopping session:', error);
                        showNotification('Error stopping session', 'error');
                    }}
                }}
                
                async function toggleFavorite(cpId) {{
                    const isFavorite = favorites.has(cpId);
                    const method = isFavorite ? 'DELETE' : 'POST';
                    const url = isFavorite 
                        ? `/drivers/${{driverId}}/favorites/${{cpId}}`
                        : `/drivers/${{driverId}}/favorites`;
                    
                    try {{
                        const response = await fetch(url, {{
                            method: method,
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: method === 'POST' ? JSON.stringify({{ cp_id: cpId }}) : undefined
                        }});
                        
                        if (response.ok) {{
                            if (isFavorite) {{
                                favorites.delete(cpId);
                                showNotification(`${{cpId}} removed from favorites`, 'info');
                            }} else {{
                                favorites.add(cpId);
                                showNotification(`${{cpId}} added to favorites`, 'success');
                            }}
                            loadFavorites();
                            renderChargingPoints();
                        }}
                    }} catch (error) {{
                        console.error('Error toggling favorite:', error);
                        showNotification('Error updating favorites', 'error');
                    }}
                }}
                
                async function applyFilters() {{
                    const city = document.getElementById('filter-city').value;
                    const connector = document.getElementById('filter-connector').value;
                    const minPower = document.getElementById('filter-min-power').value;
                    const status = document.getElementById('filter-status').value;
                    
                    const params = new URLSearchParams();
                    if (city) params.append('city', city);
                    if (connector) params.append('connector_type', connector);
                    if (minPower) params.append('min_power_kw', minPower);
                    if (status === 'FREE') params.append('only_available', 'true');
                    
                    try {{
                        const response = await fetch(`/charging-points?${{params}}`);
                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}
                        const data = await response.json();
                        console.log('Filtered charging points:', data);
                        if (!Array.isArray(data)) {{
                            throw new Error('Expected array of charging points');
                        }}
                        chargingPoints = data;
                        renderChargingPoints();
                        showNotification(`Found ${{data.length}} charging points`, 'info');
                    }} catch (error) {{
                        console.error('Error applying filters:', error);
                        showNotification('Error applying filters: ' + error.message, 'error');
                    }}
                }}
                
                function clearFilters() {{
                    document.getElementById('filter-city').value = '';
                    document.getElementById('filter-connector').value = '';
                    document.getElementById('filter-min-power').value = '';
                    document.getElementById('filter-status').value = '';
                    loadChargingPoints();
                }}
                
                function updateTimestamp() {{
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                }}
                
                // Initialize
                loadChargingPoints();
                loadActiveSession();
                loadFavorites();
                updateTimestamp();
                
                // Auto-refresh every 2 seconds
                setInterval(() => {{
                    loadChargingPoints();
                    loadActiveSession();
                    updateTimestamp();
                }}, 2000);
                
                // Refresh favorites every 10 seconds
                setInterval(loadFavorites, 10000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)

    return app
