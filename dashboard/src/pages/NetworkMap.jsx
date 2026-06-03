import React, { useState, useEffect, useCallback } from 'react';

import {

  MapContainer, TileLayer, Marker, Popup,

  ZoomControl, ScaleControl

} from 'react-leaflet';

import { useNavigate } from 'react-router-dom';

import L from 'leaflet';

import { AlertTriangle, RadioTower, CheckCircle2, Activity, Clock } from 'lucide-react';

import axios from 'axios';



import Sidebar from '../components/Sidebar';

import { API_BASE_URL, authCfg } from '../services/apiConfig';

import { useAuth } from '../auth/AuthContext';

import { REFRESH_MS } from '../dataRefreshMs';

import { mergeById } from '../utils/silentRefresh';

import { formatDateTimeTN } from '../utils/dateTime';

import '../styles/MapStyles.css';

import 'leaflet/dist/leaflet.css';



const OSM_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';



delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({

  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',

  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',

  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',

});



const STATUS_COLOR = {

  normal: '#059669',

  alerte: '#d97706',

  critique: '#dc2626',

  maintenance: '#94a3b8',

};



const makeIcon = (status) => {

  const color = STATUS_COLOR[status] || STATUS_COLOR.normal;

  const isPulse = status === 'critique';

  const isWarn = status === 'alerte';

  const svg = `

    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">

      <circle cx="12" cy="12" r="9" fill="${color}" fill-opacity="0.18"/>

      <circle cx="12" cy="12" r="5.5" fill="${color}"/>

    </svg>`;

  return L.divIcon({

    html: `<div class="noc-marker${isPulse ? ' marker-pulse-red' : isWarn ? ' marker-pulse-orange' : ''}"

                style="width:24px;height:24px">${svg}</div>`,

    className: 'custom-noc-icon',

    iconSize: [24, 24],

    iconAnchor: [12, 12],

    popupAnchor: [0, -14],

  });

};



const val = (v, unit = '') => (v !== undefined && v !== null ? `${Number(v).toFixed(1)}${unit}` : '—');

// Couleur d'une métrique selon sa gravité : rouge si critique, orange si alerte, vert sinon.
// (version lisible de l'ancien ternaire imbriqué : mêmes seuils, mêmes couleurs)
const metricColor = (valeur, seuilAlerte, seuilCritique) => {
  const v = Number(valeur);
  if (v >= seuilCritique) return '#dc2626'; // rouge
  if (v >= seuilAlerte)   return '#d97706'; // orange
  return '#059669';                         // vert
};



export default function MapPage() {

  const { token } = useAuth();

  const navigate = useNavigate();

  const [antennes, setAntennes] = useState([]);

  const [filter, setFilter] = useState('tous');



  const fetchData = useCallback(async () => {

    if (!token) return;

    const cfg = authCfg(token);

    try {

      const aRes = await axios.get(`${API_BASE_URL}/antennes`, cfg);

      setAntennes(prev => mergeById(prev, aRes.data));

    } catch (_) {}

  }, [token]);



  useEffect(() => {

    fetchData();

    const id = setInterval(fetchData, REFRESH_MS.map);

    return () => clearInterval(id);

  }, [fetchData]);



  const visible = filter === 'tous' ? antennes : antennes.filter(a => a.statut === filter);



  const statusLabel = (s) => {

    if (s === 'critique') return { text: 'Critique', bg: '#fef2f2', color: '#dc2626' };

    if (s === 'alerte') return { text: 'Alerte', bg: '#fffbeb', color: '#d97706' };

    if (s === 'maintenance') return { text: 'Maintenance', bg: '#f1f5f9', color: '#64748b' };

    return { text: 'Normal', bg: '#f0fdf4', color: '#059669' };

  };



  return (

    <div style={{ display: 'flex' }}>

      <Sidebar />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>

        <div style={{ flex: 1, position: 'relative' }}>

          <MapContainer

            center={[35.35, 10.85]}

            zoom={10}

            style={{ height: '100%', width: '100%' }}

            zoomControl={false}

          >

            <ZoomControl position="bottomright" />

            <ScaleControl position="bottomleft" />



            <TileLayer

              url={OSM_URL}

              attribution="&copy; OpenStreetMap contributors"

            />



            {visible.map(ant => (

              <Marker

                key={ant.id}

                position={[parseFloat(ant.latitude), parseFloat(ant.longitude)]}

                icon={makeIcon(ant.statut)}

              >

                <Popup minWidth={230} maxWidth={260}>

                  <div className="map-popup">

                    <div className="map-popup-header">

                      <strong style={{ fontSize: '0.97rem' }}>{ant.nom}</strong>

                      {(() => {

                        const st = statusLabel(ant.statut);

                        return (

                          <span style={{

                            background: st.bg, color: st.color,

                            padding: '2px 9px', borderRadius: 20,

                            fontSize: '0.72rem', fontWeight: 700,

                          }}>

                            {st.text}

                          </span>

                        );

                      })()}

                    </div>

                    <div className="map-popup-sub">{ant.zone} · {ant.type}</div>

                    <div className="map-popup-metrics">

                      <div className="metric-row">

                        <span>Température</span>

                        <strong style={{ color: metricColor(ant.temperature, 65, 80) }}>

                          {val(ant.temperature, '°C')}

                        </strong>

                      </div>

                      <div className="metric-row">

                        <span>CPU</span>

                        <strong style={{ color: metricColor(ant.cpu, 70, 85) }}>

                          {val(ant.cpu, '%')}

                        </strong>

                      </div>

                      <div className="metric-row">

                        <span>Disponibilité</span>

                        <strong style={{ color: ant.disponibilite < 95 ? '#dc2626' : '#059669' }}>

                          {val(ant.disponibilite, '%')}

                        </strong>

                      </div>

                      <div className="metric-row">

                        <span>Score IA</span>

                        <strong style={{ color: 'var(--accent)' }}>

                          {val(ant.risk_score, '%')}

                        </strong>

                      </div>

                    </div>

                    {ant.date_mesure && (

                      <div className="map-popup-time">

                        <Clock size={11} style={{ marginRight: 4 }} />

                        {formatDateTimeTN(ant.date_mesure)}

                      </div>

                    )}

                    <button

                      type="button"

                      className="map-popup-history-btn"

                      onClick={() => navigate(`/antenne/${ant.id}/history`)}

                    >

                      Historique

                    </button>

                  </div>

                </Popup>

              </Marker>

            ))}

          </MapContainer>



          <div className="map-stats-overlay" style={{ top: '20px', left: '20px' }}>

            {[

              { key: 'tous', icon: <RadioTower size={14} />, label: 'Sites', value: antennes.length, color: 'var(--accent)' },

              { key: 'normal', icon: <CheckCircle2 size={14} />, label: 'Normaux', value: antennes.filter(a => a.statut === 'normal').length, color: '#059669' },

              { key: 'alerte', icon: <AlertTriangle size={14} />, label: 'Alertes', value: antennes.filter(a => a.statut === 'alerte').length, color: '#d97706' },

              { key: 'critique', icon: <Activity size={14} />, label: 'Crit.', value: antennes.filter(a => a.statut === 'critique').length, color: '#dc2626' },

            ].map(s => (

              <div

                key={s.label}

                role="button"

                tabIndex={0}

                className="map-stat-chip"

                onClick={() => setFilter(s.key)}

                onKeyDown={e => e.key === 'Enter' && setFilter(s.key)}

                style={{

                  cursor: 'pointer',

                  border: filter === s.key ? `2px solid ${s.color}` : '1px solid var(--border-color)',

                  boxShadow: filter === s.key ? `0 4px 12px ${s.color}33` : '0 2px 8px rgba(0,0,0,0.05)',

                  background: filter === s.key ? '#ffffff' : 'rgba(255, 255, 255, 0.9)',

                }}

              >

                <span style={{ color: s.color }}>{s.icon}</span>

                <span className="map-stat-value" style={{ color: s.color }}>{s.value}</span>

                <span className="map-stat-label">{s.label}</span>

              </div>

            ))}

          </div>

        </div>

      </div>

    </div>

  );

}

