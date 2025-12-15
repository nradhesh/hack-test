import { useState, useEffect } from 'react';
import { Plus, X, Save, Building2, MapPin, AlertCircle } from 'lucide-react';
import { createAsset, createWard, getWards, createIssue, getAssets } from '../services/api';

export default function Admin() {
    const [activeTab, setActiveTab] = useState('asset');
    const [wards, setWards] = useState([]);
    const [assets, setAssets] = useState([]);
    const [message, setMessage] = useState(null);
    const [loading, setLoading] = useState(false);

    // Asset form
    const [assetForm, setAssetForm] = useState({
        name: '',
        asset_type: 'road',
        ward_id: '',
        zone: '',
        latitude: '',
        longitude: '',
        base_repair_cost: 50000,
        sla_days: 7,
        description: '',
    });

    // Ward form
    const [wardForm, setWardForm] = useState({
        ward_code: '',
        name: '',
        zone: '',
        center_latitude: '',
        center_longitude: '',
        population: '',
        ward_officer: '',
    });

    // Issue form
    const [issueForm, setIssueForm] = useState({
        asset_id: '',
        title: '',
        description: '',
        category: 'pothole',
        severity: 'medium',
        estimated_repair_cost: 10000,
    });

    useEffect(() => {
        loadWards();
        loadAssets();
    }, []);

    const loadWards = async () => {
        try {
            const res = await getWards();
            setWards(res.data || []);
        } catch (e) {
            console.error('Error loading wards:', e);
        }
    };

    const loadAssets = async () => {
        try {
            const res = await getAssets({ page_size: 100 });
            setAssets(res.data?.items || []);
        } catch (e) {
            console.error('Error loading assets:', e);
        }
    };

    const showMessage = (text, type = 'success') => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 3000);
    };

    const handleAssetSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await createAsset({
                ...assetForm,
                ward_id: assetForm.ward_id ? parseInt(assetForm.ward_id) : null,
                latitude: assetForm.latitude ? parseFloat(assetForm.latitude) : null,
                longitude: assetForm.longitude ? parseFloat(assetForm.longitude) : null,
                base_repair_cost: parseFloat(assetForm.base_repair_cost),
                sla_days: parseInt(assetForm.sla_days),
            });
            showMessage('Asset created successfully!');
            setAssetForm({ name: '', asset_type: 'road', ward_id: '', zone: '', latitude: '', longitude: '', base_repair_cost: 50000, sla_days: 7, description: '' });
            loadAssets();
        } catch (e) {
            showMessage(e.response?.data?.detail || 'Failed to create asset', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleWardSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await createWard({
                ...wardForm,
                center_latitude: wardForm.center_latitude ? parseFloat(wardForm.center_latitude) : null,
                center_longitude: wardForm.center_longitude ? parseFloat(wardForm.center_longitude) : null,
                population: wardForm.population ? parseInt(wardForm.population) : null,
            });
            showMessage('Ward created successfully!');
            setWardForm({ ward_code: '', name: '', zone: '', center_latitude: '', center_longitude: '', population: '', ward_officer: '' });
            loadWards();
        } catch (e) {
            showMessage(e.response?.data?.detail || 'Failed to create ward', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleIssueSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await createIssue({
                ...issueForm,
                asset_id: parseInt(issueForm.asset_id),
                estimated_repair_cost: parseFloat(issueForm.estimated_repair_cost),
            });
            showMessage('Issue created successfully!');
            setIssueForm({ asset_id: '', title: '', description: '', category: 'pothole', severity: 'medium', estimated_repair_cost: 10000 });
        } catch (e) {
            showMessage(e.response?.data?.detail || 'Failed to create issue', 'error');
        } finally {
            setLoading(false);
        }
    };

    const assetTypes = ['road', 'drain', 'streetlight', 'bridge', 'sidewalk', 'water_pipe', 'sewer', 'park'];
    const issueCategories = ['pothole', 'crack', 'blockage', 'flooding', 'outage', 'damage', 'wear', 'other'];
    const severities = ['low', 'medium', 'high', 'critical'];

    const inputClass = "w-full px-3 md:px-4 py-2.5 md:py-3 bg-dark-800 border border-dark-700 rounded-lg md:rounded-xl text-white focus:outline-none focus:border-primary-500 text-sm";
    const labelClass = "block text-dark-400 text-xs md:text-sm mb-1.5 md:mb-2";

    return (
        <div className="space-y-4 md:space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl md:text-3xl font-bold text-white">Admin Panel</h1>
                <p className="text-dark-400 text-sm md:text-base mt-1">Add new wards, assets, and issues</p>
            </div>

            {/* Message */}
            {message && (
                <div className={`p-3 md:p-4 rounded-xl text-sm ${message.type === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}>
                    {message.text}
                </div>
            )}

            {/* Tabs */}
            <div className="flex flex-wrap gap-2">
                {[
                    { id: 'asset', label: 'Add Asset', icon: Building2 },
                    { id: 'ward', label: 'Add Ward', icon: MapPin },
                    { id: 'issue', label: 'Report Issue', icon: AlertCircle },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 md:px-6 py-2.5 md:py-3 rounded-lg md:rounded-xl font-medium transition-all text-sm ${activeTab === tab.id
                                ? 'bg-primary-500 text-white'
                                : 'bg-dark-800 text-dark-400 hover:text-white hover:bg-dark-700'
                            }`}
                    >
                        <tab.icon className="w-4 h-4 md:w-5 md:h-5" />
                        <span className="hidden sm:inline">{tab.label}</span>
                        <span className="sm:hidden">{tab.label.split(' ')[1]}</span>
                    </button>
                ))}
            </div>

            {/* Asset Form */}
            {activeTab === 'asset' && (
                <form onSubmit={handleAssetSubmit} className="glass-card rounded-xl md:rounded-2xl p-4 md:p-6">
                    <h2 className="text-lg md:text-xl font-semibold text-white mb-4 md:mb-6">Create New Asset</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                        <div>
                            <label className={labelClass}>Asset Name *</label>
                            <input
                                type="text"
                                required
                                value={assetForm.name}
                                onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., Main Road Section A"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Asset Type *</label>
                            <select
                                value={assetForm.asset_type}
                                onChange={(e) => setAssetForm({ ...assetForm, asset_type: e.target.value })}
                                className={inputClass}
                            >
                                {assetTypes.map((type) => (
                                    <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className={labelClass}>Ward</label>
                            <select
                                value={assetForm.ward_id}
                                onChange={(e) => setAssetForm({ ...assetForm, ward_id: e.target.value })}
                                className={inputClass}
                            >
                                <option value="">Select Ward</option>
                                {wards.map((ward) => (
                                    <option key={ward.id} value={ward.id}>{ward.name}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className={labelClass}>Zone</label>
                            <input
                                type="text"
                                value={assetForm.zone}
                                onChange={(e) => setAssetForm({ ...assetForm, zone: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., North"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Latitude</label>
                            <input
                                type="number"
                                step="any"
                                value={assetForm.latitude}
                                onChange={(e) => setAssetForm({ ...assetForm, latitude: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., 12.9716"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Longitude</label>
                            <input
                                type="number"
                                step="any"
                                value={assetForm.longitude}
                                onChange={(e) => setAssetForm({ ...assetForm, longitude: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., 77.5946"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Base Repair Cost (₹)</label>
                            <input
                                type="number"
                                value={assetForm.base_repair_cost}
                                onChange={(e) => setAssetForm({ ...assetForm, base_repair_cost: e.target.value })}
                                className={inputClass}
                            />
                        </div>
                        <div>
                            <label className={labelClass}>SLA Days</label>
                            <input
                                type="number"
                                value={assetForm.sla_days}
                                onChange={(e) => setAssetForm({ ...assetForm, sla_days: e.target.value })}
                                className={inputClass}
                            />
                        </div>
                        <div className="md:col-span-2">
                            <label className={labelClass}>Description</label>
                            <textarea
                                value={assetForm.description}
                                onChange={(e) => setAssetForm({ ...assetForm, description: e.target.value })}
                                className={inputClass}
                                rows={3}
                                placeholder="Optional description..."
                            />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="mt-4 md:mt-6 w-full sm:w-auto px-6 md:px-8 py-2.5 md:py-3 bg-gradient-to-r from-primary-500 to-purple-600 text-white rounded-lg md:rounded-xl font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
                    >
                        <Save className="w-4 h-4 md:w-5 md:h-5" />
                        {loading ? 'Creating...' : 'Create Asset'}
                    </button>
                </form>
            )}

            {/* Ward Form */}
            {activeTab === 'ward' && (
                <form onSubmit={handleWardSubmit} className="glass-card rounded-xl md:rounded-2xl p-4 md:p-6">
                    <h2 className="text-lg md:text-xl font-semibold text-white mb-4 md:mb-6">Create New Ward</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                        <div>
                            <label className={labelClass}>Ward Code *</label>
                            <input
                                type="text"
                                required
                                value={wardForm.ward_code}
                                onChange={(e) => setWardForm({ ...wardForm, ward_code: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., W006"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Ward Name *</label>
                            <input
                                type="text"
                                required
                                value={wardForm.name}
                                onChange={(e) => setWardForm({ ...wardForm, name: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., Tech Park Zone"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Zone</label>
                            <input
                                type="text"
                                value={wardForm.zone}
                                onChange={(e) => setWardForm({ ...wardForm, zone: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., East"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Ward Officer</label>
                            <input
                                type="text"
                                value={wardForm.ward_officer}
                                onChange={(e) => setWardForm({ ...wardForm, ward_officer: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., John Doe"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Center Latitude</label>
                            <input
                                type="number"
                                step="any"
                                value={wardForm.center_latitude}
                                onChange={(e) => setWardForm({ ...wardForm, center_latitude: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., 12.9716"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Center Longitude</label>
                            <input
                                type="number"
                                step="any"
                                value={wardForm.center_longitude}
                                onChange={(e) => setWardForm({ ...wardForm, center_longitude: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., 77.5946"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Population</label>
                            <input
                                type="number"
                                value={wardForm.population}
                                onChange={(e) => setWardForm({ ...wardForm, population: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., 50000"
                            />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="mt-4 md:mt-6 w-full sm:w-auto px-6 md:px-8 py-2.5 md:py-3 bg-gradient-to-r from-primary-500 to-purple-600 text-white rounded-lg md:rounded-xl font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
                    >
                        <Save className="w-4 h-4 md:w-5 md:h-5" />
                        {loading ? 'Creating...' : 'Create Ward'}
                    </button>
                </form>
            )}

            {/* Issue Form */}
            {activeTab === 'issue' && (
                <form onSubmit={handleIssueSubmit} className="glass-card rounded-xl md:rounded-2xl p-4 md:p-6">
                    <h2 className="text-lg md:text-xl font-semibold text-white mb-4 md:mb-6">Report New Issue</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                        <div>
                            <label className={labelClass}>Asset *</label>
                            <select
                                required
                                value={issueForm.asset_id}
                                onChange={(e) => setIssueForm({ ...issueForm, asset_id: e.target.value })}
                                className={inputClass}
                            >
                                <option value="">Select Asset</option>
                                {assets.map((asset) => (
                                    <option key={asset.id} value={asset.id}>{asset.name} ({asset.asset_code})</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className={labelClass}>Title *</label>
                            <input
                                type="text"
                                required
                                value={issueForm.title}
                                onChange={(e) => setIssueForm({ ...issueForm, title: e.target.value })}
                                className={inputClass}
                                placeholder="e.g., Large pothole on main road"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Category *</label>
                            <select
                                value={issueForm.category}
                                onChange={(e) => setIssueForm({ ...issueForm, category: e.target.value })}
                                className={inputClass}
                            >
                                {issueCategories.map((cat) => (
                                    <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className={labelClass}>Severity *</label>
                            <select
                                value={issueForm.severity}
                                onChange={(e) => setIssueForm({ ...issueForm, severity: e.target.value })}
                                className={inputClass}
                            >
                                {severities.map((sev) => (
                                    <option key={sev} value={sev}>{sev.charAt(0).toUpperCase() + sev.slice(1)}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className={labelClass}>Estimated Repair Cost (₹)</label>
                            <input
                                type="number"
                                value={issueForm.estimated_repair_cost}
                                onChange={(e) => setIssueForm({ ...issueForm, estimated_repair_cost: e.target.value })}
                                className={inputClass}
                            />
                        </div>
                        <div className="md:col-span-2">
                            <label className={labelClass}>Description</label>
                            <textarea
                                value={issueForm.description}
                                onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })}
                                className={inputClass}
                                rows={3}
                                placeholder="Describe the issue..."
                            />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="mt-4 md:mt-6 w-full sm:w-auto px-6 md:px-8 py-2.5 md:py-3 bg-gradient-to-r from-primary-500 to-purple-600 text-white rounded-lg md:rounded-xl font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
                    >
                        <Save className="w-4 h-4 md:w-5 md:h-5" />
                        {loading ? 'Creating...' : 'Report Issue'}
                    </button>
                </form>
            )}
        </div>
    );
}
