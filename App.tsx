import AddLocationAltIcon from "@mui/icons-material/AddLocationAlt";
import ArticleIcon from "@mui/icons-material/Article";
import DevicesIcon from "@mui/icons-material/Devices";
import ExploreIcon from "@mui/icons-material/Explore";
import FenceIcon from "@mui/icons-material/Fence";
import HistoryIcon from "@mui/icons-material/History";
import LoginIcon from "@mui/icons-material/Login";
import LogoutIcon from "@mui/icons-material/Logout";
import MapIcon from "@mui/icons-material/Map";
import RadarIcon from "@mui/icons-material/Radar";
import RefreshIcon from "@mui/icons-material/Refresh";
import TimelineIcon from "@mui/icons-material/Timeline";
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Switch,
  TextField,
  Typography
} from "@mui/material";
import type { FormEvent, ReactElement, ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { GeofenceMap } from "./components/GeofenceMap";
import { createGeofence, fetchEvents, fetchGeofences, fetchLocationHistory, ingestLocation, login, profile, signup, type AuthUser } from "./services/api";
import type { BoundaryType, Geofence, GeofenceEvent, LocationEvent } from "./types/api";

const samplePolygon = "12.965,77.585\n12.965,77.605\n12.981,77.605\n12.981,77.585";
type Section = "overview" | "map" | "boundaries" | "devices" | "locations" | "events" | "audit";

const navItems: { id: Section; label: string; icon: ReactElement }[] = [
  { id: "overview", label: "Dashboard", icon: <RadarIcon fontSize="small" /> },
  { id: "map", label: "Live Map", icon: <MapIcon fontSize="small" /> },
  { id: "boundaries", label: "Geofences", icon: <FenceIcon fontSize="small" /> },
  { id: "devices", label: "Devices", icon: <DevicesIcon fontSize="small" /> },
  { id: "locations", label: "Location History", icon: <HistoryIcon fontSize="small" /> },
  { id: "events", label: "Events", icon: <TimelineIcon fontSize="small" /> },
  { id: "audit", label: "Audit Logs", icon: <ArticleIcon fontSize="small" /> }
];

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [authError, setAuthError] = useState("");
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  const [events, setEvents] = useState<GeofenceEvent[]>([]);
  const [locations, setLocations] = useState<LocationEvent[]>([]);
  const [message, setMessage] = useState<string>("");
  const [boundaryType, setBoundaryType] = useState<BoundaryType>("circle");
  const [section, setSection] = useState<Section>("overview");

  async function refresh() {
    const [fences, eventRows, history] = await Promise.all([fetchGeofences(), fetchEvents(), fetchLocationHistory()]);
    setGeofences(fences);
    setEvents(eventRows);
    setLocations(history);
  }

  useEffect(() => {
    const token = localStorage.getItem("geo_token");
    if (!token) return;
    profile()
      .then((account) => {
        setUser(account);
        return refresh();
      })
      .catch(() => localStorage.removeItem("geo_token"));
  }, []);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthError("");
    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email"));
    const password = String(formData.get("password"));
    const name = String(formData.get("name") || "Geo Admin");
    try {
      const response = authMode === "signup" ? await signup(name, email, password) : await login(email, password);
      localStorage.setItem("geo_token", response.access_token);
      setUser(response.user);
      await refresh();
    } catch {
      setAuthError(authMode === "signup" ? "Could not create account. Try another email." : "Login failed. Check email and password.");
    }
  }

  async function demoLogin() {
    setAuthError("");
    try {
      let response;
      try {
        response = await login("admin@example.com", "secret123");
      } catch {
        response = await signup("Admin", "admin@example.com", "secret123");
      }
      localStorage.setItem("geo_token", response.access_token);
      setUser(response.user);
      await refresh();
    } catch {
      setAuthError("Demo login is not available. Check that the backend is running.");
    }
  }

  function logout() {
    localStorage.removeItem("geo_token");
    setUser(null);
    setGeofences([]);
    setEvents([]);
    setLocations([]);
  }

  const eventCounts = useMemo(
    () =>
      events.reduce<Record<string, number>>((acc, event) => {
        acc[event.event_type] = (acc[event.event_type] ?? 0) + 1;
        return acc;
      }, {}),
    [events]
  );

  async function submitGeofence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload =
      boundaryType === "circle"
        ? {
            name: String(formData.get("name")),
            boundary_type: "circle",
            center_lat: Number(formData.get("center_lat")),
            center_lng: Number(formData.get("center_lng")),
            radius_meters: Number(formData.get("radius_meters")),
            accuracy_buffer_meters: Number(formData.get("accuracy_buffer_meters") || 15),
            emit_inside_events: true,
            emit_outside_events: false
          }
        : {
            name: String(formData.get("name")),
            boundary_type: "polygon",
            accuracy_buffer_meters: Number(formData.get("accuracy_buffer_meters") || 15),
            emit_inside_events: true,
            emit_outside_events: false,
            points: String(formData.get("points"))
              .split("\n")
              .map((row) => row.split(",").map(Number))
              .map(([latitude, longitude]) => ({ latitude, longitude }))
          };
    await createGeofence(payload);
    setMessage("Geofence saved.");
    await refresh();
  }

  async function submitLocation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    await ingestLocation({
      device_identifier: String(formData.get("device_identifier")),
      latitude: Number(formData.get("latitude")),
      longitude: Number(formData.get("longitude")),
      accuracy_meters: Number(formData.get("accuracy_meters") || 0),
      timestamp: new Date().toISOString()
    });
    setMessage("Location processed.");
    await refresh();
  }

  const latestLocations = useMemo(() => {
    const unique = new Map<number, LocationEvent>();
    locations.forEach((location) => {
      if (!unique.has(location.device_id)) unique.set(location.device_id, location);
    });
    return [...unique.values()];
  }, [locations]);

  const activeFences = geofences.filter((fence) => fence.is_enabled).length;

  function StatTile({ label, value, helper, tone }: { label: string; value: string | number; helper: string; tone: string }) {
    return (
      <Paper variant="outlined" sx={{ p: 2, bgcolor: "#ffffff", borderColor: "#d8e1ea", borderRadius: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h4" fontWeight={800} color="#172033">
              {value}
            </Typography>
          </Box>
          <Box sx={{ width: 10, height: 42, borderRadius: 2, bgcolor: tone }} />
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {helper}
        </Typography>
      </Paper>
    );
  }

  function BoundaryForm() {
    return (
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, borderColor: "#d8e1ea" }}>
        <Stack component="form" onSubmit={submitGeofence} spacing={1.5}>
          <Typography variant="h6" color="#172033">
            Geofence Builder
          </Typography>
          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6}>
              <TextField name="name" label="Geofence name" size="small" defaultValue="Office Circle Geofence" required fullWidth />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select label="Shape" size="small" value={boundaryType} onChange={(e) => setBoundaryType(e.target.value as BoundaryType)} fullWidth>
                <MenuItem value="circle">Circle perimeter</MenuItem>
                <MenuItem value="polygon">Polygon area</MenuItem>
              </TextField>
            </Grid>
            {boundaryType === "circle" ? (
              <>
                <Grid item xs={12} sm={4}>
                  <TextField name="center_lat" label="Latitude" size="small" defaultValue="12.9716" type="number" fullWidth />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField name="center_lng" label="Longitude" size="small" defaultValue="77.5946" type="number" fullWidth />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField name="radius_meters" label="Radius m" size="small" defaultValue="500" type="number" fullWidth />
                </Grid>
              </>
            ) : (
              <Grid item xs={12}>
                <TextField name="points" label="Polygon coordinates" size="small" multiline minRows={5} defaultValue={samplePolygon} fullWidth />
              </Grid>
            )}
            <Grid item xs={12} sm={6}>
              <TextField name="accuracy_buffer_meters" label="GPS tolerance m" size="small" defaultValue="15" type="number" fullWidth />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Button type="submit" startIcon={<FenceIcon />} variant="contained" fullWidth sx={{ height: 40, bgcolor: "#155e75" }}>
                Save Geofence
              </Button>
            </Grid>
          </Grid>
        </Stack>
      </Paper>
    );
  }

  function LocationForm() {
    return (
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, borderColor: "#d8e1ea" }}>
        <Stack component="form" onSubmit={submitLocation} spacing={1.5}>
          <Typography variant="h6" color="#172033">
            Location Intake
          </Typography>
          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6}>
              <TextField name="device_identifier" label="Device code" size="small" defaultValue="device-001" required fullWidth />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField name="accuracy_meters" label="Accuracy m" size="small" defaultValue="10" type="number" fullWidth />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField name="latitude" label="Latitude" size="small" defaultValue="12.9716" type="number" fullWidth />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField name="longitude" label="Longitude" size="small" defaultValue="77.5946" type="number" fullWidth />
            </Grid>
            <Grid item xs={12}>
              <Button type="submit" startIcon={<AddLocationAltIcon />} variant="contained" fullWidth sx={{ bgcolor: "#a16207" }}>
                Process Location
              </Button>
            </Grid>
          </Grid>
        </Stack>
      </Paper>
    );
  }

  function ShellTable({ children }: { children: ReactNode }) {
    return (
      <Paper variant="outlined" sx={{ overflow: "hidden", borderRadius: 2, borderColor: "#d8e1ea" }}>
        <Box sx={{ overflow: "auto" }}>{children}</Box>
      </Paper>
    );
  }

  if (!user) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", bgcolor: "#f3f6f2", p: 2 }}>
        <Paper variant="outlined" sx={{ width: "100%", maxWidth: 460, p: 3, borderRadius: 2, borderColor: "#d8e1ea" }}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <ExploreIcon sx={{ color: "#a16207", fontSize: 34 }} />
              <Box>
                <Typography variant="h4" fontWeight={800} color="#102a2f">
                  Geofence Event Monitor
                </Typography>
                <Typography color="text.secondary">Sign in to open the geofencing console.</Typography>
              </Box>
            </Stack>
            {authError && <Alert severity="error">{authError}</Alert>}
            <Stack component="form" onSubmit={submitAuth} spacing={1.5}>
              {authMode === "signup" && <TextField name="name" label="Name" defaultValue="Geo Admin" required fullWidth />}
              <TextField name="email" label="Email" defaultValue="admin@example.com" type="email" required fullWidth />
              <TextField name="password" label="Password" defaultValue="secret123" type="password" required fullWidth />
              <Button type="submit" startIcon={<LoginIcon />} variant="contained" sx={{ bgcolor: "#155e75", py: 1.2 }}>
                {authMode === "signup" ? "Create Account" : "Login"}
              </Button>
            </Stack>
            <Button variant="outlined" onClick={demoLogin}>
              Use Demo Login
            </Button>
            <Button variant="text" onClick={() => setAuthMode(authMode === "signup" ? "login" : "signup")}>
              {authMode === "signup" ? "Already have an account? Login" : "Need an account? Create one"}
            </Button>
          </Stack>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", gridTemplateColumns: { xs: "1fr", md: "248px 1fr" }, bgcolor: "#f3f6f2" }}>
      <Box sx={{ bgcolor: "#102a2f", color: "#f8fafc", p: 2.5, display: { xs: "none", md: "block" } }}>
        <Stack spacing={3} sx={{ position: "sticky", top: 20 }}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <ExploreIcon sx={{ color: "#facc15" }} />
            <Box>
              <Typography fontWeight={800}>Geofence Event Monitor</Typography>
              <Typography variant="caption" sx={{ color: "#b9c6d4" }}>
                Geofencing control console
              </Typography>
            </Box>
          </Stack>
          <Stack spacing={0.5}>
            {navItems.map((item) => (
              <Button
                key={item.id}
                startIcon={item.icon}
                onClick={() => setSection(item.id)}
                sx={{
                  justifyContent: "flex-start",
                  color: section === item.id ? "#172033" : "#dce6ef",
                  bgcolor: section === item.id ? "#facc15" : "transparent",
                  "&:hover": { bgcolor: section === item.id ? "#facc15" : "rgba(255,255,255,0.08)" }
                }}
              >
                {item.label}
              </Button>
            ))}
          </Stack>
        </Stack>
      </Box>

      <Box>
        <Box sx={{ bgcolor: "#ffffff", borderBottom: "1px solid #d8e1ea", px: { xs: 2, md: 3 }, py: 1.5 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" gap={2}>
            <Box>
              <Typography variant="h5" fontWeight={800} color="#172033">
                Geofence Monitoring
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Compact console for geofence state detection and live signals.
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <IconButton onClick={refresh} aria-label="refresh dashboard">
                <RefreshIcon />
              </IconButton>
              <Chip label={user.name || "Admin"} color="primary" variant="outlined" />
              <Button startIcon={<LogoutIcon />} variant="contained" color="warning" onClick={logout}>
                Logout
              </Button>
            </Stack>
          </Stack>
        </Box>

        <Box sx={{ p: { xs: 2, md: 3 } }}>
          <Stack direction="row" spacing={1} sx={{ display: { xs: "flex", md: "none" }, mb: 2, overflowX: "auto" }}>
            {navItems.map((item) => (
              <Chip key={item.id} icon={item.icon} label={item.label} onClick={() => setSection(item.id)} color={section === item.id ? "primary" : "default"} />
            ))}
          </Stack>

          {message && (
            <Alert severity={message.includes("not reachable") ? "warning" : "success"} sx={{ mb: 2 }}>
              {message}
            </Alert>
          )}

          {section === "overview" && (
            <Stack spacing={2}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <StatTile label="Active geofences" value={activeFences} helper={`${geofences.length} total configured`} tone="#155e75" />
                </Grid>
                <Grid item xs={12} md={3}>
                  <StatTile label="Devices seen" value={latestLocations.length} helper="latest known device positions" tone="#a16207" />
                </Grid>
                <Grid item xs={12} md={3}>
                  <StatTile label="Events" value={events.length} helper="recent location events" tone="#2563eb" />
                </Grid>
                <Grid item xs={12} md={3}>
                  <StatTile label="Inside now" value={events.filter((e) => e.current_state === "inside").length} helper="based on event stream" tone="#f59e0b" />
                </Grid>
              </Grid>
              <Grid container spacing={2}>
                <Grid item xs={12} lg={8}>
                  <Paper variant="outlined" sx={{ overflow: "hidden", borderRadius: 2, borderColor: "#d8e1ea" }}>
                    <GeofenceMap geofences={geofences} events={events} locations={locations} />
                  </Paper>
                </Grid>
                <Grid item xs={12} lg={4}>
                  <Stack spacing={2}>
                    <LocationForm />
                    <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, borderColor: "#d8e1ea" }}>
                      <Typography variant="h6" color="#172033">
                        Event Mix
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ my: 1 }} flexWrap="wrap">
                        {["enter", "exit", "inside", "outside"].map((type) => (
                          <Chip key={type} label={`${type}: ${eventCounts[type] ?? 0}`} size="small" />
                        ))}
                      </Stack>
                      <Divider sx={{ my: 1 }} />
                      {events.slice(0, 5).map((event) => (
                        <Typography key={event.id} variant="body2" sx={{ py: 0.6 }}>
                          {event.event_type.toUpperCase()} geofence {event.geofence_id} by Device {event.device_id}
                        </Typography>
                      ))}
                    </Paper>
                  </Stack>
                </Grid>
              </Grid>
            </Stack>
          )}

          {section === "map" && (
            <Grid container spacing={2}>
              <Grid item xs={12} lg={8}>
                <Paper variant="outlined" sx={{ overflow: "hidden", borderRadius: 2, borderColor: "#d8e1ea" }}>
                  <GeofenceMap geofences={geofences} events={events} locations={locations} />
                </Paper>
              </Grid>
              <Grid item xs={12} lg={4}>
                <Stack spacing={2}>
                  <BoundaryForm />
                  <LocationForm />
                </Stack>
              </Grid>
            </Grid>
          )}

          {section === "boundaries" && (
            <Stack spacing={2}>
              <BoundaryForm />
              <ShellTable>
                <Box component="table" sx={{ width: "100%", borderCollapse: "collapse", minWidth: 820 }}>
                  <thead>
                    <tr>
                      {["Geofence", "Shape", "Geometry", "Rules", "Enabled"].map((head) => (
                        <Box component="th" key={head} sx={{ textAlign: "left", p: 1.5, bgcolor: "#f8fafc", color: "#475569" }}>
                          {head}
                        </Box>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {geofences.map((fence) => (
                      <tr key={fence.id}>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0", fontWeight: 700 }}>
                          {fence.name}
                          <Typography variant="caption" display="block" color="text.secondary">
                            Geofence #{fence.id}
                          </Typography>
                        </Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                          <Chip label={fence.boundary_type} size="small" />
                        </Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                          {fence.boundary_type === "circle" ? `${fence.radius_meters} m radius` : `${fence.points.length} vertices`}
                        </Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                          <Stack direction="row" spacing={0.5}>
                            <Chip label="enter" size="small" />
                            <Chip label="exit" size="small" />
                            {fence.emit_inside_events && <Chip label="inside" size="small" />}
                          </Stack>
                        </Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                          <Switch checked={fence.is_enabled} size="small" />
                        </Box>
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </ShellTable>
            </Stack>
          )}

          {section === "devices" && (
            <ShellTable>
              <Box component="table" sx={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
                <thead>
                  <tr>
                    {["Device", "Last latitude", "Last longitude", "Accuracy", "Recorded"].map((head) => (
                      <Box component="th" key={head} sx={{ textAlign: "left", p: 1.5, bgcolor: "#f8fafc", color: "#475569" }}>
                        {head}
                      </Box>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {latestLocations.map((location) => (
                    <tr key={location.device_id}>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0", fontWeight: 700 }}>
                        Device {location.device_id}
                      </Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{location.latitude.toFixed(5)}</Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{location.longitude.toFixed(5)}</Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{location.accuracy_meters ?? 0} m</Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{new Date(location.recorded_at).toLocaleString()}</Box>
                    </tr>
                  ))}
                </tbody>
              </Box>
            </ShellTable>
          )}

          {section === "locations" && (
            <Stack spacing={2}>
              <LocationForm />
              <ShellTable>
                <Box component="table" sx={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
                  <thead>
                    <tr>
                      {["Device", "Coordinates", "Accuracy", "Timestamp", "Status"].map((head) => (
                        <Box component="th" key={head} sx={{ textAlign: "left", p: 1.5, bgcolor: "#f8fafc", color: "#475569" }}>
                          {head}
                        </Box>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {locations.slice(0, 80).map((location) => (
                      <tr key={location.id}>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>Device {location.device_id}</Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                          {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
                        </Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{location.accuracy_meters ?? 0} m</Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{new Date(location.recorded_at).toLocaleString()}</Box>
                        <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                          <Chip label="stored" size="small" color="success" />
                        </Box>
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </ShellTable>
            </Stack>
          )}

          {section === "events" && (
            <ShellTable>
              <Box component="table" sx={{ width: "100%", borderCollapse: "collapse", minWidth: 860 }}>
                <thead>
                  <tr>
                    {["Event", "Device", "Geofence", "State", "Location", "When"].map((head) => (
                      <Box component="th" key={head} sx={{ textAlign: "left", p: 1.5, bgcolor: "#f8fafc", color: "#475569" }}>
                        {head}
                      </Box>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {events.slice(0, 100).map((event) => (
                    <tr key={event.id}>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                        <Chip label={event.event_type} size="small" color={event.event_type === "exit" ? "error" : event.event_type === "enter" ? "success" : "info"} />
                      </Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>Device {event.device_id}</Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>Geofence {event.geofence_id}</Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                        {event.previous_state ?? "new"} to {event.current_state}
                      </Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>
                        {event.latitude.toFixed(5)}, {event.longitude.toFixed(5)}
                      </Box>
                      <Box component="td" sx={{ p: 1.5, borderTop: "1px solid #e2e8f0" }}>{new Date(event.occurred_at).toLocaleString()}</Box>
                    </tr>
                  ))}
                </tbody>
              </Box>
            </ShellTable>
          )}

          {section === "audit" && (
            <Paper variant="outlined" sx={{ p: 3, borderRadius: 2, borderColor: "#d8e1ea" }}>
              <Typography variant="h6" color="#172033">
                Audit Logs
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 1 }}>
                The backend exposes `/api/v1/audit-trail` and `/api/v1/health/database`. This panel is intentionally separate from the reference design and can be connected to the audit endpoint for production review.
              </Typography>
              <Button startIcon={<RefreshIcon />} variant="outlined" sx={{ mt: 2 }} onClick={refresh}>
                Refresh operational data
              </Button>
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  );
}
