import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getAssetsForMap } from '../services/api';
import { getMDIHexColor, formatCurrency, getAssetTypeIcon, getMDIColor, getMDIBgColor } from '../utils/helpers';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icon based on MDI score
const createCustomIcon = (score) => {
    const color = getMDIHexColor(score);
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="
      background-color: ${color};
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 10px rgba(0,0,0,0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: bold;
      color: white;
    ">${Math.round(score)}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14],
    });
};

// Component to fit map bounds to markers
function FitBounds({ assets }) {
    const map = useMap();

    useEffect(() => {
        if (assets.length > 0) {
            const bounds = assets
                .filter(a => a.latitude && a.longitude)
                .map(a => [a.latitude, a.longitude]);
            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [assets, map]);

    return null;
}

export default function MapView() {
    const [assets, setAssets] = useState([]);
    const [selectedAsset, setSelectedAsset] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Bangalore center coordinates
    const defaultCenter = [12.9716, 77.5946];
    const defaultZoom = 12;

    useEffect(() => {
        loadAssets();
    }, []);

    const loadAssets = async () => {
        try {
            const response = await getAssetsForMap();
            setAssets(response.data || []);
        } catch (error) {
            console.error('Error loading assets:', error);
            setError('Failed to load assets');
            setAssets([]);
        } finally {
            setLoading(false);
        }
    };

    // Group by score for grid
    const groupByScore = () => {
        return {
            excellent: assets.filter(a => a.mdi_score >= 90),
            good: assets.filter(a => a.mdi_score >= 70 && a.mdi_score < 90),
            fair: assets.filter(a => a.mdi_score >= 50 && a.mdi_score < 70),
            poor: assets.filter(a => a.mdi_score >= 30 && a.mdi_score < 50),
            critical: assets.filter(a => a.mdi_score < 30),
        };
    };

    const groups = groupByScore();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">City Map</h1>
                    <p className="text-dark-400 mt-1">Infrastructure health visualization - Bangalore</p>
                </div>
                <div className="flex items-center gap-4 text-sm">
                    <span className="text-dark-400">Total: <span className="text-white font-medium">{assets.length}</span> assets</span>
                    <span className="text-dark-400">With Issues: <span className="text-yellow-400 font-medium">{assets.filter(a => a.open_issues > 0).length}</span></span>
                    <span className="text-dark-400">Critical: <span className="text-red-400 font-medium">{assets.filter(a => a.mdi_score < 30).length}</span></span>
                </div>
            </div>

            {/* Legend */}
            <div className="glass-card rounded-xl p-4 flex items-center gap-6">
                <span className="text-dark-400 text-sm font-medium">MDI Score:</span>
                {[
                    { label: 'Excellent (90+)', color: '#10b981', count: groups.excellent.length },
                    { label: 'Good (70-89)', color: '#22c55e', count: groups.good.length },
                    { label: 'Fair (50-69)', color: '#eab308', count: groups.fair.length },
                    { label: 'Poor (30-49)', color: '#f97316', count: groups.poor.length },
                    { label: 'Critical (<30)', color: '#ef4444', count: groups.critical.length },
                ].map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full" style={{ background: item.color }} />
                        <span className="text-dark-300 text-sm">{item.label}</span>
                        <span className="text-dark-500 text-xs">({item.count})</span>
                    </div>
                ))}
            </div>

            {/* Error */}
            {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400">
                    {error}
                </div>
            )}

            {/* Interactive Map */}
            <div className="glass-card rounded-2xl p-4">
                <h3 className="text-lg font-semibold text-white mb-4">📍 Interactive Map</h3>
                <div className="relative rounded-xl overflow-hidden" style={{ height: '500px' }}>
                    <MapContainer
                        center={defaultCenter}
                        zoom={defaultZoom}
                        style={{ height: '100%', width: '100%' }}
                        className="z-0 rounded-xl"
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        />

                        <FitBounds assets={assets} />

                        {assets.map((asset) => (
                            asset.latitude && asset.longitude && (
                                <Marker
                                    key={asset.id}
                                    position={[asset.latitude, asset.longitude]}
                                    icon={createCustomIcon(asset.mdi_score || 100)}
                                    eventHandlers={{
                                        click: () => setSelectedAsset(asset),
                                    }}
                                >
                                    <Popup className="custom-popup">
                                        <div className="p-2 min-w-[200px]">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-xl">{getAssetTypeIcon(asset.asset_type)}</span>
                                                <div>
                                                    <h3 className="font-semibold text-gray-900">{asset.name}</h3>
                                                    <p className="text-gray-500 text-xs">{asset.asset_code}</p>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                                                <div>
                                                    <p className="text-gray-500">MDI Score</p>
                                                    <p className="font-bold" style={{ color: getMDIHexColor(asset.mdi_score) }}>
                                                        {asset.mdi_score?.toFixed(1) || '100'}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-gray-500">Debt</p>
                                                    <p className="font-bold text-red-600">{formatCurrency(asset.current_debt || 0)}</p>
                                                </div>
                                            </div>
                                            <Link
                                                to={`/assets/${asset.id}`}
                                                className="block w-full text-center py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600"
                                            >
                                                View Details
                                            </Link>
                                        </div>
                                    </Popup>
                                </Marker>
                            )
                        ))}
                    </MapContainer>
                </div>
            </div>

            {/* Asset Grid */}
            <div className="glass-card rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">📊 Asset Distribution</h3>

                {assets.length === 0 ? (
                    <div className="flex items-center justify-center h-64 text-dark-400">
                        No assets found
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
                        {assets.map((asset) => (
                            <div
                                key={asset.id}
                                onClick={() => setSelectedAsset(selectedAsset?.id === asset.id ? null : asset)}
                                className={`p-3 rounded-xl cursor-pointer transition-all hover:scale-105 ${selectedAsset?.id === asset.id ? 'ring-2 ring-white' : ''
                                    }`}
                                style={{ background: `${getMDIHexColor(asset.mdi_score)}20`, borderLeft: `4px solid ${getMDIHexColor(asset.mdi_score)}` }}
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-lg">{getAssetTypeIcon(asset.asset_type)}</span>
                                    <span className={`text-sm font-bold ${getMDIColor(asset.mdi_score)}`}>
                                        {asset.mdi_score?.toFixed(0) || '100'}
                                    </span>
                                </div>
                                <p className="text-white text-xs font-medium truncate">{asset.name}</p>
                                <p className="text-dark-400 text-xs">{asset.asset_code}</p>
                                {asset.open_issues > 0 && (
                                    <span className="inline-block mt-1 px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">
                                        {asset.open_issues} issues
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Selected Asset Details */}
            {selectedAsset && (
                <div className="glass-card rounded-2xl p-6">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                            <span className="text-4xl">{getAssetTypeIcon(selectedAsset.asset_type)}</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">{selectedAsset.name}</h3>
                                <p className="text-dark-400">{selectedAsset.asset_code}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className={`text-3xl font-bold ${getMDIColor(selectedAsset.mdi_score)}`}>
                                {selectedAsset.mdi_score?.toFixed(1) || '100'}
                            </p>
                            <p className="text-dark-400 text-sm">MDI Score</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4 mt-6">
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm">Current Debt</p>
                            <p className="text-xl font-bold text-red-400">{formatCurrency(selectedAsset.current_debt || 0)}</p>
                        </div>
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm">Base Cost</p>
                            <p className="text-xl font-bold text-white">{formatCurrency(selectedAsset.base_repair_cost || 0)}</p>
                        </div>
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm">Open Issues</p>
                            <p className="text-xl font-bold text-yellow-400">{selectedAsset.open_issues || 0}</p>
                        </div>
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm">Overdue</p>
                            <p className="text-xl font-bold text-orange-400">{selectedAsset.overdue_issues || 0}</p>
                        </div>
                    </div>

                    <div className="mt-4 flex gap-3">
                        <Link
                            to={`/assets/${selectedAsset.id}`}
                            className="px-6 py-2 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 transition-colors"
                        >
                            View Details
                        </Link>
                        <button
                            onClick={() => setSelectedAsset(null)}
                            className="px-6 py-2 bg-dark-700 text-white rounded-lg font-medium hover:bg-dark-600 transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
