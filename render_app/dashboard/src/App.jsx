import React, { useState, useEffect } from 'react';
import './index.css';

function App() {
  const [data, setData] = useState({
    devices: [],
    total_hashrate: 0,
    decision_log: [],
    server_time: ''
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/status'); // Relative path for Render deployment
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <header>
        <div className="logo-section">
          <h1>ANTIGRAVITY <span style={{fontSize: '0.8rem', opacity: 0.6}}>COMMAND CENTER v2.0</span></h1>
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: '20px'}}>
          <div className="live-badge">LIVE TELEMETRY</div>
          <div style={{fontSize: '0.9rem', opacity: 0.7}}>{data.server_time}</div>
        </div>
      </header>

      <div className="stats-grid">
        <div className="card">
          <h3>Total Ecosystem Hashrate</h3>
          <div className="hashrate-value">{(data.total_hashrate / 1000).toFixed(2)} MH/s</div>
          <p style={{opacity: 0.5}}>Active Nodes: {data.devices.length}</p>
        </div>

        <div className="card">
          <h3>Local AI Decision Log</h3>
          <div className="log-container">
            {data.decision_log.map((log, index) => (
              <div key={index} className="log-entry">
                <span style={{color: 'var(--secondary)'}}>[{log.timestamp}]</span> {log.message}
              </div>
            ))}
            {data.decision_log.length === 0 && <div style={{opacity: 0.3}}>Waiting for system signals...</div>}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{marginBottom: '1rem'}}>Connected Devices</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem'}}>
          {data.devices.map((device, index) => (
            <div key={index} className="device-item">
              <div style={{display: 'flex', alignItems: 'center'}}>
                <div className="status-indicator online"></div>
                <div>
                  <div style={{fontWeight: 'bold'}}>{device.device_id}</div>
                  <div style={{fontSize: '0.7rem', opacity: 0.6}}>{device.status}</div>
                </div>
              </div>
              <div style={{textAlign: 'right'}}>
                <div style={{color: device.temp > 70 ? '#ff4b2b' : 'var(--primary)'}}>{device.temp}°C</div>
                <div style={{fontSize: '0.7rem', opacity: 0.6}}>{device.threads} Threads</div>
              </div>
            </div>
          ))}
          {data.devices.length === 0 && <div style={{opacity: 0.5}}>No devices currently connected.</div>}
        </div>
      </div>
      
      <footer style={{marginTop: '3rem', textAlign: 'center', opacity: 0.4, fontSize: '0.8rem'}}>
        Antigravity Distributed Ecosystem © 2026 | Wallet: 0xb71d...0701
      </footer>
    </div>
  );
}

export default App;
