import { useState, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import { getAssetsForMap, getAssetDebt } from '../services/api';
import { getMDIHexColor, formatCurrency, getAssetTypeIcon } from '../utils/helpers';

// Replace with your Mapbox token
mapboxgl.accessToken = 'pk.eyJ1IjoibWRpLWRlbW8iLCJhIjoiY2x1ZXhhbXAwMDAxNjJrcGI1MzN0bjNxbCJ9.demo_token';

export default function MapView() {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const [assets, setAssets] = useState([]);
    const [selectedAsset, setSelectedAsset] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAssets();
    }, []);

    useEffect(() => {
        if (!mapContainer.current || assets.length === 0) return;

        initMap();

        return () => {
            if (map.current) map.current.remove();
        };
    }, [assets]);

    const loadAssets = async () => {
        try {
            const response = await getAssetsForMap();
            setAssets(response.data);
        } catch (error) {
            console.error('Error loading assets:', error);
            // Use demo data if API fails
            setAssets(generateDemoAssets());
        } finally {
            setLoading(false);
        }
    };

    const generateDemoAssets = () => {
        const types = ['road', 'drain', 'streetlight', 'bridge', 'sidewalk'];
        return Array.from({ length: 50 }, (_, i) => ({
            id: i + 1,
            asset_code: `AST-${String(i + 1).padStart(4, '0')}`,
            name: `Demo Asset ${i + 1}`,
            asset_type: types[i % types.length],
            latitude: 12.9716 + (Math.random() - 0.5) * 0.1,
            longitude: 77.5946 + (Math.random() - 0.5) * 0.1,
            base_repair_cost: 10000 + Math.random() * 50000,
            current_debt: Math.random() * 30000,
            mdi_score: 30 + Math.random() * 70,
            open_issues: Math.floor(Math.random() * 5),
            overdue_issues: Math.floor(Math.random() * 3),
        }));
    };

    const initMap = () => {
        if (map.current) return;

        const bounds = assets.reduce((acc, asset) => {
            if (asset.latitude && asset.longitude) {
                acc.minLat = Math.min(acc.minLat, asset.latitude);
                acc.maxLat = Math.max(acc.maxLat, asset.latitude);
                acc.minLng = Math.min(acc.minLng, asset.longitude);
                acc.maxLng = Math.max(acc.maxLng, asset.longitude);
            }
            return acc;
        }, { minLat: 90, maxLat: -90, minLng: 180, maxLng: -180 });

        const centerLat = (bounds.minLat + bounds.maxLat) / 2 || 12.9716;
        const centerLng = (bounds.minLng + bounds.maxLng) / 2 || 77.5946;

        map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/dark-v11',
            center: [centerLng, centerLat],
            zoom: 12,
        });

        map.current.on('load', () => {
            addMarkers();
        });

        map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    };

    const addMarkers = () => {
        assets.forEach((asset) => {
            if (!asset.latitude || !asset.longitude) return;

            const el = document.createElement('div');
            el.className = 'asset-marker';
            el.style.cssText = `
        width: 24px;
        height: 24px;
        background: ${getMDIHexColor(asset.mdi_score)};
        border: 3px solid white;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        transition: transform 0.2s;
      `;
            el.onmouseenter = () => { el.style.transform = 'scale(1.3)'; };
            el.onmouseleave = () => { el.style.transform = 'scale(1)'; };

            const marker = new mapboxgl.Marker(el)
                .setLngLat([asset.longitude, asset.latitude])
                .addTo(map.current);

            el.addEventListener('click', () => {
                setSelectedAsset(asset);
            });
        });
    };

    return (
        <div className="h-[calc(100vh-120px)] relative">
            {/* Map */}
            <div ref={mapContainer} className="absolute inset-0 rounded-2xl overflow-hidden" />

            {/* Loading overlay */}
            {loading && (
                <div className="absolute inset-0 bg-dark-900/80 flex items-center justify-center rounded-2xl">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
                        <p className="text-dark-400">Loading map data...</p>
                    </div>
                </div>
            )}

            {/* Legend */}
            <div className="absolute top-4 left-4 glass rounded-xl p-4 z-10">
                <h4 className="text-white font-medium mb-3">MDI Score</h4>
                <div className="space-y-2">
                    {[
                        { label: 'Excellent (90+)', color: '#10b981' },
                        { label: 'Good (70-89)', color: '#22c55e' },
                        { label: 'Fair (50-69)', color: '#eab308' },
                        { label: 'Poor (30-49)', color: '#f97316' },
                        { label: 'Critical (<30)', color: '#ef4444' },
                    ].map((item) => (
                        <div key={item.label} className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded-full" style={{ background: item.color }} />
                            <span className="text-dark-300 text-sm">{item.label}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Selected Asset Panel */}
            {selectedAsset && (
                <div className="absolute top-4 right-4 w-80 glass-card rounded-xl p-5 z-10">
                    <div className="flex items-start justify-between mb-4">
                        <div>
                            <span className="text-2xl mr-2">{getAssetTypeIcon(selectedAsset.asset_type)}</span>
                            <h3 className="text-white font-semibold text-lg inline">{selectedAsset.name}</h3>
                            <p className="text-dark-400 text-sm mt-1">{selectedAsset.asset_code}</p>
                        </div>
                        <button
                            onClick={() => setSelectedAsset(null)}
                            className="text-dark-400 hover:text-white"
                        >
                            ✕
                        </button>
                    </div>

                    <div className="space-y-4">
                        {/* Score */}
                        <div className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50">
                            <span className="text-dark-400">MDI Score</span>
                            <span className="text-2xl font-bold" style={{ color: getMDIHexColor(selectedAsset.mdi_score) }}>
                                {selectedAsset.mdi_score.toFixed(1)}
                            </span>
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-3 rounded-lg bg-dark-800/50">
                                <p className="text-dark-500 text-xs mb-1">Current Debt</p>
                                <p className="text-red-400 font-semibold">{formatCurrency(selectedAsset.current_debt)}</p>
                            </div>
                            <div className="p-3 rounded-lg bg-dark-800/50">
                                <p className="text-dark-500 text-xs mb-1">Open Issues</p>
                                <p className="text-yellow-400 font-semibold">{selectedAsset.open_issues}</p>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="pt-2 flex gap-2">
                            <a
                                href={`/assets/${selectedAsset.id}`}
                                className="flex-1 py-2 px-4 bg-primary-500 text-white rounded-lg text-center font-medium hover:bg-primary-600 transition-colors"
                            >
                                View Details
                            </a>
                        </div>
                    </div>
                </div>
            )}

            {/* Stats Bar */}
            <div className="absolute bottom-4 left-4 right-4 glass rounded-xl p-4 z-10 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <div>
                        <p className="text-dark-400 text-xs">Total Assets</p>
                        <p className="text-white font-semibold">{assets.length}</p>
                    </div>
                    <div>
                        <p className="text-dark-400 text-xs">With Issues</p>
                        <p className="text-yellow-400 font-semibold">{assets.filter(a => a.open_issues > 0).length}</p>
                    </div>
                    <div>
                        <p className="text-dark-400 text-xs">Critical</p>
                        <p className="text-red-400 font-semibold">{assets.filter(a => a.mdi_score < 30).length}</p>
                    </div>
                </div>
                <p className="text-dark-500 text-sm">Click on a marker to view asset details</p>
            </div>
        </div>
    );
}
