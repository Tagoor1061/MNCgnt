(function () {
  // Leaflet flood/depth demo layer + live location marker.
  // Shows realistic risk zones for Guntur area with default landmark markers & Admin Drawing Tools

  function getColorByDepth(depth) {
    if (depth >= 5) return '#d32f2f';      // red (high depth/high risk)
    if (depth >= 2) return '#f9a825';      // yellow (moderate)
    return '#2e7d32';                       // green (high altitude/safer)
  }

  const HEX_COLORS = {
    safe: '#2e7d32',
    moderate: '#f9a825',
    danger: '#d32f2f',
    green: '#2e7d32',
    yellow: '#f9a825',
    red: '#d32f2f'
  };

  // Enhanced GeoJSON with realistic risk zones around Guntur
  const DEMO_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "properties": { "depth": 6.5, "name": "Penumarru Village - High Risk", "riskLevel": "High Risk" },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [80.410, 16.298], [80.428, 16.295], [80.438, 16.300], [80.442, 16.312],
              [80.435, 16.320], [80.420, 16.325], [80.405, 16.318], [80.410, 16.298]
            ]
          ]
        }
      },
      {
        "type": "Feature",
        "properties": { "depth": 6.2, "name": "Narasaraopet Area - High Risk", "riskLevel": "High Risk" },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [80.452, 16.305], [80.472, 16.302], [80.478, 16.310], [80.480, 16.325],
              [80.468, 16.335], [80.450, 16.330], [80.448, 16.315], [80.452, 16.305]
            ]
          ]
        }
      },
      {
        "type": "Feature",
        "properties": { "depth": 3.0, "name": "Guntur City Center - Moderate", "riskLevel": "Moderate Risk" },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [80.428, 16.330], [80.450, 16.328], [80.462, 16.338], [80.458, 16.352],
              [80.440, 16.358], [80.425, 16.355], [80.422, 16.340], [80.428, 16.330]
            ]
          ]
        }
      },
      {
        "type": "Feature",
        "properties": { "depth": 2.8, "name": "Pedakakani Village - Moderate", "riskLevel": "Moderate Risk" },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [80.390, 16.308], [80.408, 16.305], [80.415, 16.315], [80.420, 16.330],
              [80.405, 16.338], [80.388, 16.332], [80.385, 16.318], [80.390, 16.308]
            ]
          ]
        }
      },
      {
        "type": "Feature",
        "properties": { "depth": 0.5, "name": "Divi Bazaar - Safe Zone", "riskLevel": "Safe Zone" },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [80.405, 16.278], [80.425, 16.275], [80.435, 16.282], [80.438, 16.295],
              [80.420, 16.298], [80.408, 16.292], [80.405, 16.278]
            ]
          ]
        }
      },
      {
        "type": "Feature",
        "properties": { "depth": 0.3, "name": "Uppal Cheruvu Hills - Safe Zone", "riskLevel": "Safe Zone" },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [80.458, 16.345], [80.475, 16.342], [80.485, 16.350], [80.488, 16.362],
              [80.475, 16.370], [80.460, 16.365], [80.455, 16.355], [80.458, 16.345]
            ]
          ]
        }
      }
    ]
  };

  const DEFAULT_LANDMARKS = [
    { name: "Guntur Medical College", lat: 16.3100, lng: 80.4300, type: "hospital" },
    { name: "Municipal Corporation Office", lat: 16.3090, lng: 80.4380, type: "admin" },
    { name: "Railway Station", lat: 16.3050, lng: 80.4250, type: "transport" },
    { name: "Central Market", lat: 16.3120, lng: 80.4400, type: "market" },
    { name: "Bus Stand", lat: 16.3150, lng: 80.4320, type: "transport" },
    { name: "Emergency Services - Police", lat: 16.3080, lng: 80.4320, type: "emergency" }
  ];

  function getLandmarkIcon(type) {
    const iconColors = {
      hospital: '#e53935',
      admin: '#1976d2',
      transport: '#00897b',
      market: '#f57f17',
      emergency: '#d32f2f'
    };
    const color = iconColors[type] || '#666';

    return L.divIcon({
      className: `landmark-icon landmark-${type}`,
      html: `
        <div style="
          width: 30px;
          height: 30px;
          background: ${color};
          border: 2px solid white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 5px rgba(0,0,0,0.3);
          font-size: 16px;
          color: white;
          font-weight: bold;
        ">
          ${type === 'hospital' ? '🏥' : type === 'admin' ? '🏛️' : type === 'transport' ? '🚌' : type === 'market' ? '🏪' : type === 'emergency' ? '🚨' : '📍'}
        </div>
      `,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!window.L) return;
    if (!document.getElementById('map')) return;

    const center = [16.3067, 80.4360];
    const selectMode = new URLSearchParams(window.location.search).get('select') === '1';
    const map = L.map('map', {
      zoomControl: true,
      zoom: 13,
      minZoom: 10,
      maxZoom: 19
    }).setView(center, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    function style(feature) {
      const depth = Number(feature.properties && feature.properties.depth);
      return {
        color: 'rgba(0,0,0,0.15)',
        weight: 0.5,
        fillOpacity: 0.55,
        fillColor: getColorByDepth(depth)
      };
    }

    const layer = L.geoJSON(DEMO_GEOJSON, { style }).addTo(map);

    layer.eachLayer(function (l) {
      if (l.feature && l.feature.properties) {
        const props = l.feature.properties;
        const depth = Number(props.depth);
        const name = props.name || 'Area';
        const riskLevel = props.riskLevel || 'Unknown';

        l.bindPopup(`
          <div style="font-family: Arial, sans-serif; max-width: 200px;">
            <b>${name}</b><br/>
            <span style="color: #666;">Depth: ${depth} m</span><br/>
            <span style="background: ${getColorByDepth(depth)}; color: white; padding: 2px 6px; border-radius: 3px; display: inline-block; margin-top: 5px; font-size: 12px;">
              ${riskLevel}
            </span>
          </div>
        `);

        l.on('mouseover', function() {
          this.setStyle({ weight: 2, fillOpacity: 0.75 });
        });
        l.on('mouseout', function() {
          this.setStyle({ weight: 0.5, fillOpacity: 0.55 });
        });
      }
    });

    // Feature Groups for Admin & DB Markings
    const savedGroup = L.featureGroup().addTo(map);
    const draftGroup = L.featureGroup().addTo(map);

    // Global delete marking helper
    window.deleteMarking = function (markingId) {
      if (!confirm('Are you sure you want to delete this marking?')) return;
      fetch(`/api/markings/${markingId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            loadServerMarkings();
          } else {
            alert(data.message || 'Error deleting marking');
          }
        })
        .catch(err => console.error('Delete error:', err));
    };

    // Load server-persisted markings
    function loadServerMarkings() {
      savedGroup.clearLayers();
      fetch('/api/markings')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success' && Array.isArray(data.markings)) {
            data.markings.forEach(function (m) {
              const hex = HEX_COLORS[m.color] || HEX_COLORS[m.risk_level] || '#2e7d32';
              const geo = m.geojson_data;
              let layerItem = null;

              if (m.shape_type === 'circle' && geo.center && geo.radius) {
                layerItem = L.circle(geo.center, {
                  radius: geo.radius,
                  color: hex,
                  fillColor: hex,
                  fillOpacity: 0.45,
                  weight: 3
                });
              } else if (m.shape_type === 'marker' && geo) {
                const latlng = geo.center || (geo.coordinates ? [geo.coordinates[1], geo.coordinates[0]] : null);
                if (latlng) {
                  layerItem = L.circleMarker(latlng, {
                    radius: 12,
                    fillColor: hex,
                    color: '#ffffff',
                    weight: 3,
                    fillOpacity: 0.9
                  });
                }
              } else if (geo && (geo.type || geo.coordinates)) {
                layerItem = L.geoJSON(geo, {
                  style: {
                    color: hex,
                    fillColor: hex,
                    fillOpacity: m.shape_type === 'pencil' ? 0.2 : 0.45,
                    weight: m.shape_type === 'pencil' ? 5 : 3
                  }
                });
              }

              if (layerItem) {
                const badgeColor = m.color === 'yellow' ? 'black' : 'white';
                const riskLabel = m.risk_level === 'safe' ? '🟢 Safe Zone' : m.risk_level === 'moderate' ? '🟡 Moderate Zone' : '🔴 Danger Zone';
                const popupHTML = `
                  <div style="font-family: Arial, sans-serif; min-width: 150px;">
                    <b style="font-size: 1.05em;">${m.title}</b><br/>
                    <div style="background:${hex}; color:${badgeColor}; padding:3px 8px; border-radius:4px; font-weight:bold; display:inline-block; margin:5px 0; font-size:12px;">
                      ${riskLabel}
                    </div><br/>
                    <small style="color:#666;">Shape: ${m.shape_type.toUpperCase()} | By: ${m.created_by}</small>
                    ${window.IS_ADMIN_USER ? `<br/><button type="button" onclick="deleteMarking(${m.id})" style="background:#d32f2f; color:white; border:none; padding:4px 8px; border-radius:4px; margin-top:8px; cursor:pointer; font-size:12px;">🗑️ Delete Marking</button>` : ''}
                  </div>
                `;
                layerItem.bindPopup(popupHTML);
                layerItem.addTo(savedGroup);
              }
            });
          }
        })
        .catch(err => console.error('Error loading markings:', err));
    }

    loadServerMarkings();

    // Landmarks Layer
    const landmarksLayer = L.featureGroup().addTo(map);
    DEFAULT_LANDMARKS.forEach(function(landmark) {
      const marker = L.marker([landmark.lat, landmark.lng], {
        icon: getLandmarkIcon(landmark.type),
        title: landmark.name
      }).addTo(landmarksLayer);

      marker.bindPopup(`
        <div style="font-family: Arial, sans-serif;">
          <b>${landmark.name}</b><br/>
          <small style="color: #999;">Lat: ${landmark.lat.toFixed(4)}, Lng: ${landmark.lng.toFixed(4)}</small>
        </div>
      `);
    });

    if (selectMode) {
      let selectedMarker = null;

      map.on('click', function (event) {
        if (window.IS_ADMIN_USER && window.currentTool !== 'select') {
          // Skip select mode when drawing
        } else {
          const lat = event.latlng.lat.toFixed(6);
          const lng = event.latlng.lng.toFixed(6);

          if (selectedMarker) {
            selectedMarker.setLatLng(event.latlng);
          } else {
            selectedMarker = L.marker(event.latlng, {
              icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
              })
            }).addTo(map);
          }

          selectedMarker.bindPopup(`
            <b>Selected location</b><br/>
            ${Number(lat).toFixed(5)}, ${Number(lng).toFixed(5)}<br/>
            <button type="button" id="confirm-map-location" style="
              background: #1976d2;
              color: white;
              border: none;
              padding: 6px 12px;
              border-radius: 4px;
              cursor: pointer;
              margin-top: 5px;
            ">Use this location</button>
          `).openPopup();

          setTimeout(function () {
            const button = document.getElementById('confirm-map-location');
            if (!button) return;
            button.addEventListener('click', function () {
              window.location.href = `/dashboard?latitude=${encodeURIComponent(lat)}&longitude=${encodeURIComponent(lng)}`;
            });
          }, 0);
        }
      });
    }

    // Live user location
    let userMarker = null;

    function setUserMarker(latlng) {
      const icon = L.divIcon({
        className: 'user-live-dot',
        html: `
          <div style="
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #1e88e5;
            border: 3px solid #fff;
            box-shadow: 0 0 0 4px rgba(30,136,229,0.3);
            animation: pulse 2s infinite;
          "></div>
          <style>
            @keyframes pulse {
              0% { box-shadow: 0 0 0 4px rgba(30,136,229,0.3); }
              50% { box-shadow: 0 0 0 8px rgba(30,136,229,0.15); }
              100% { box-shadow: 0 0 0 4px rgba(30,136,229,0.3); }
            }
          </style>
        `,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      if (userMarker) {
        userMarker.setLatLng(latlng);
      } else {
        userMarker = L.marker(latlng, { title: 'Your live location', icon }).addTo(map);
      }
      userMarker.bindPopup(`
        <div style="font-family: Arial, sans-serif;">
          <b>Your Current Location</b><br/>
          <small>Lat: ${latlng.lat.toFixed(6)}, Lng: ${latlng.lng.toFixed(6)}</small>
        </div>
      `);
    }

    if (navigator.geolocation) {
      navigator.geolocation.watchPosition(
        function (pos) {
          setUserMarker([pos.coords.latitude, pos.coords.longitude]);
        },
        function (error) {
          console.log('Geolocation unavailable:', error.message);
        },
        { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
      );
    }

    // ==========================================
    // ADMIN DRAWING & MARKING INTERACTIVE SYSTEM
    // ==========================================
    if (window.IS_ADMIN_USER) {
      window.currentTool = 'pencil';
      window.currentRisk = 'safe';
      window.currentColor = 'green';
      window.currentHex = '#2e7d32';

      let unsavedMarkings = [];
      let isMouseDown = false;
      let activeLayer = null;

      // Pencil state
      let pencilPoints = [];

      // Circle / Rect state
      let startLatLng = null;

      // Polygon state
      let polyPoints = [];
      let polyPreview = null;

      const statusEl = document.getElementById('drawing-status');

      function updateStatusMessage() {
        if (!statusEl) return;
        const colorName = window.currentColor.toUpperCase();
        const riskName = window.currentRisk.toUpperCase();

        let toolDesc = '';
        switch (window.currentTool) {
          case 'pencil':
            toolDesc = '✏️ <b>Pencil Mode:</b> Click & drag cursor on map to draw freehand lines/shapes.';
            break;
          case 'marker':
            toolDesc = '📍 <b>Marker Mode:</b> Click on map to place a highlighted location marker.';
            break;
          case 'circle':
            toolDesc = '⭕ <b>Circle Mode:</b> Click & drag on map to expand a circular risk zone.';
            break;
          case 'rectangle':
            toolDesc = '⬛ <b>Rectangle Mode:</b> Click & drag on map to draw a rectangular box zone.';
            break;
          case 'polygon':
            toolDesc = '⬡ <b>Polygon Mode:</b> Click sequential points on map to build a custom zone polygon. Double-click to close.';
            break;
          case 'eraser':
            toolDesc = '🧹 <b>Eraser Mode:</b> Click any drawn shape or marker on the map to remove it.';
            break;
        }

        statusEl.innerHTML = `${toolDesc} Active Risk: <strong style="color:${window.currentHex}">${riskName} (${colorName})</strong>. Unsaved shapes: <strong>${unsavedMarkings.length}</strong>.`;
      }

      // Tool Switch Buttons
      document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', function () {
          document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
          this.classList.add('active');
          window.currentTool = this.getAttribute('data-tool');

          if (polyPreview) {
            draftGroup.removeLayer(polyPreview);
            polyPreview = null;
          }
          polyPoints = [];

          updateStatusMessage();
        });
      });

      // Color / Risk Buttons
      document.querySelectorAll('.color-btn').forEach(btn => {
        btn.addEventListener('click', function () {
          document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
          this.classList.add('active');
          window.currentRisk = this.getAttribute('data-risk');
          window.currentColor = this.getAttribute('data-color');
          window.currentHex = this.getAttribute('data-hex');
          updateStatusMessage();
        });
      });

      // Helper to add draft marking item
      function addDraftItem(shapeType, geoData, layer) {
        const title = `${window.currentRisk.toUpperCase()} Zone (${shapeType.toUpperCase()})`;
        const item = {
          title: title,
          risk_level: window.currentRisk,
          color: window.currentColor,
          shape_type: shapeType,
          geojson_data: geoData,
          layer: layer
        };

        // Attach popup & eraser click listener
        const badgeColor = window.currentColor === 'yellow' ? 'black' : 'white';
        layer.bindPopup(`
          <div style="font-family: Arial, sans-serif;">
            <b>${title} [Draft]</b><br/>
            <div style="background:${window.currentHex}; color:${badgeColor}; padding:2px 6px; border-radius:3px; display:inline-block; margin:4px 0; font-size:12px;">
              ${window.currentRisk.toUpperCase()}
            </div><br/>
            <small style="color:#e65100;">⚠️ Click "Save All Markings" to commit</small>
          </div>
        `);

        layer.on('click', function (e) {
          if (window.currentTool === 'eraser') {
            L.DomEvent.stopPropagation(e);
            draftGroup.removeLayer(layer);
            unsavedMarkings = unsavedMarkings.filter(m => m.layer !== layer);
            updateStatusMessage();
          }
        });

        unsavedMarkings.push(item);
        updateStatusMessage();
      }

      // Map Drawing Event Handlers
      map.on('mousedown', function (e) {
        if (window.currentTool === 'eraser') return;
        isMouseDown = true;
        startLatLng = e.latlng;

        if (window.currentTool === 'pencil') {
          map.dragging.disable();
          pencilPoints = [e.latlng];
          activeLayer = L.polyline(pencilPoints, {
            color: window.currentHex,
            weight: 5,
            opacity: 0.85
          }).addTo(draftGroup);
        } else if (window.currentTool === 'circle') {
          map.dragging.disable();
          activeLayer = L.circle(startLatLng, {
            radius: 1,
            color: window.currentHex,
            fillColor: window.currentHex,
            fillOpacity: 0.45,
            weight: 2
          }).addTo(draftGroup);
        } else if (window.currentTool === 'rectangle') {
          map.dragging.disable();
          activeLayer = L.rectangle([startLatLng, startLatLng], {
            color: window.currentHex,
            fillColor: window.currentHex,
            fillOpacity: 0.45,
            weight: 2
          }).addTo(draftGroup);
        }
      });

      map.on('mousemove', function (e) {
        if (!isMouseDown) return;

        if (window.currentTool === 'pencil' && activeLayer) {
          pencilPoints.push(e.latlng);
          activeLayer.setLatLngs(pencilPoints);
        } else if (window.currentTool === 'circle' && activeLayer) {
          const radius = startLatLng.distanceTo(e.latlng);
          activeLayer.setRadius(radius);
        } else if (window.currentTool === 'rectangle' && activeLayer) {
          activeLayer.setBounds(L.latLngBounds(startLatLng, e.latlng));
        }
      });

      map.on('mouseup', function (e) {
        if (!isMouseDown) return;
        isMouseDown = false;
        map.dragging.enable();

        if (window.currentTool === 'pencil' && activeLayer) {
          if (pencilPoints.length > 1) {
            addDraftItem('pencil', activeLayer.toGeoJSON(), activeLayer);
          } else {
            draftGroup.removeLayer(activeLayer);
          }
        } else if (window.currentTool === 'circle' && activeLayer) {
          if (activeLayer.getRadius() > 5) {
            const geoData = {
              type: 'Circle',
              center: [startLatLng.lat, startLatLng.lng],
              radius: activeLayer.getRadius()
            };
            addDraftItem('circle', geoData, activeLayer);
          } else {
            draftGroup.removeLayer(activeLayer);
          }
        } else if (window.currentTool === 'rectangle' && activeLayer) {
          addDraftItem('rectangle', activeLayer.toGeoJSON(), activeLayer);
        }

        activeLayer = null;
      });

      // Map Click Handler for Marker & Polygon
      map.on('click', function (e) {
        if (window.currentTool === 'marker') {
          const markerLayer = L.circleMarker(e.latlng, {
            radius: 12,
            fillColor: window.currentHex,
            color: '#ffffff',
            weight: 3,
            fillOpacity: 0.9
          }).addTo(draftGroup);

          const geoData = {
            type: 'Point',
            coordinates: [e.latlng.lng, e.latlng.lat],
            center: [e.latlng.lat, e.latlng.lng]
          };
          addDraftItem('marker', geoData, markerLayer);
        } else if (window.currentTool === 'polygon') {
          polyPoints.push(e.latlng);
          if (!polyPreview) {
            polyPreview = L.polygon(polyPoints, {
              color: window.currentHex,
              fillColor: window.currentHex,
              fillOpacity: 0.45,
              weight: 2
            }).addTo(draftGroup);
          } else {
            polyPreview.setLatLngs(polyPoints);
          }
        }
      });

      // Polygon Double Click Finish
      map.on('dblclick', function (e) {
        if (window.currentTool === 'polygon' && polyPoints.length >= 3 && polyPreview) {
          L.DomEvent.stopPropagation(e);
          addDraftItem('polygon', polyPreview.toGeoJSON(), polyPreview);
          polyPreview = null;
          polyPoints = [];
        }
      });

      // Erase saved layers on click when Eraser active
      savedGroup.on('layeradd', function (e) {
        const layer = e.layer;
        layer.on('click', function (ev) {
          if (window.currentTool === 'eraser') {
            L.DomEvent.stopPropagation(ev);
            // Search popup content for delete button
            const popupContent = layer.getPopup() ? layer.getPopup().getContent() : '';
            const match = typeof popupContent === 'string' && popupContent.match(/deleteMarking\((\d+)\)/);
            if (match && match[1]) {
              window.deleteMarking(match[1]);
            }
          }
        });
      });

      // Save All Markings Button
      const saveBtn = document.getElementById('save-markings-btn');
      if (saveBtn) {
        saveBtn.addEventListener('click', function () {
          if (unsavedMarkings.length === 0) {
            alert('No draft markings to save! Use Pencil, Marker, Circle, Rectangle, or Polygon to draw first.');
            return;
          }

          const payload = unsavedMarkings.map(item => ({
            title: item.title,
            risk_level: item.risk_level,
            color: item.color,
            shape_type: item.shape_type,
            geojson_data: item.geojson_data
          }));

          fetch('/api/markings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ markings: payload })
          })
            .then(res => res.json())
            .then(data => {
              if (data.status === 'success') {
                alert(`✅ Successfully saved ${payload.length} marking(s) to database!`);
                draftGroup.clearLayers();
                unsavedMarkings = [];
                loadServerMarkings();
                updateStatusMessage();
              } else {
                alert(data.message || 'Error saving markings');
              }
            })
            .catch(err => console.error('Save error:', err));
        });
      }

      // Clear Draft Button
      const clearDraftBtn = document.getElementById('clear-draft-btn');
      if (clearDraftBtn) {
        clearDraftBtn.addEventListener('click', function () {
          draftGroup.clearLayers();
          unsavedMarkings = [];
          if (polyPreview) {
            polyPreview = null;
          }
          polyPoints = [];
          updateStatusMessage();
        });
      }

      // Delete All DB Markings Button
      const deleteDbBtn = document.getElementById('delete-all-db-btn');
      if (deleteDbBtn) {
        deleteDbBtn.addEventListener('click', function () {
          if (!confirm('🚨 Are you sure you want to delete ALL saved markings from the database? This cannot be undone.')) return;
          fetch('/api/markings/clear', { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
              if (data.status === 'success') {
                alert('✅ All DB markings deleted successfully!');
                savedGroup.clearLayers();
                loadServerMarkings();
              } else {
                alert(data.message || 'Error clearing markings');
              }
            })
            .catch(err => console.error('Clear error:', err));
        });
      }

      updateStatusMessage();
    }

    // Keyboard Zoom Shortcuts
    document.addEventListener('keydown', function(e) {
      if (e.key === '+' || e.key === '=') {
        map.zoomIn();
      } else if (e.key === '-' || e.key === '_') {
        map.zoomOut();
      }
    });
  });
})();

