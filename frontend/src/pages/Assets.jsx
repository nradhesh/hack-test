import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, ChevronRight, AlertTriangle, RefreshCw } from 'lucide-react';
import { getAssets } from '../services/api';
import { formatCurrency, getMDIColor, getAssetTypeIcon, formatDate } from '../utils/helpers';

export default function Assets() {
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [search, setSearch] = useState('');
    const [typeFilter, setTypeFilter] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        loadAssets();
    }, [page, typeFilter]);

    const loadAssets = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getAssets({
                page,
                page_size: 15,
                search: search || undefined,
                asset_type: typeFilter || undefined,
            });
            setAssets(response.data.items || []);
            setTotalPages(response.data.total_pages || 1);
            setTotal(response.data.total || 0);
        } catch (error) {
            console.error('Error loading assets:', error);
            setError('Failed to load assets. Please try again.');
            setAssets([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = () => {
        setPage(1);
        loadAssets();
    };

    const assetTypes = ['road', 'drain', 'streetlight', 'bridge', 'sidewalk'];

    return (
        <div className="space-y-4 md:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-white">Assets</h1>
                    <p className="text-dark-400 text-sm md:text-base mt-1">Manage infrastructure ({total} total)</p>
                </div>
                <button
                    onClick={loadAssets}
                    className="self-start px-4 py-2 bg-primary-500/20 text-primary-400 rounded-lg hover:bg-primary-500/30 transition-colors flex items-center gap-2 text-sm"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                    <input
                        type="text"
                        placeholder="Search assets..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 text-sm"
                    />
                </div>
                <div className="flex gap-2">
                    <select
                        value={typeFilter}
                        onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
                        className="flex-1 sm:flex-none px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500 text-sm"
                    >
                        <option value="">All Types</option>
                        {assetTypes.map((type) => (
                            <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                        ))}
                    </select>
                    <button
                        onClick={handleSearch}
                        className="px-4 sm:px-6 py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors text-sm"
                    >
                        Search
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400 text-sm">
                    {error}
                </div>
            )}

            {/* Mobile Card View */}
            <div className="block md:hidden space-y-3">
                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500 mx-auto"></div>
                        <p className="text-dark-400 mt-2 text-sm">Loading assets...</p>
                    </div>
                ) : assets.length === 0 ? (
                    <div className="text-center py-12 text-dark-400">No assets found</div>
                ) : (
                    assets.map((asset) => (
                        <Link
                            key={asset.id}
                            to={`/assets/${asset.id}`}
                            className="block glass-card rounded-xl p-4 hover:border-primary-500/30 transition-colors"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">{getAssetTypeIcon(asset.asset_type)}</span>
                                    <div>
                                        <p className="text-white font-medium">{asset.name}</p>
                                        <p className="text-dark-500 text-xs">{asset.asset_code}</p>
                                    </div>
                                </div>
                                <span className={`text-lg font-bold ${getMDIColor(asset.mdi_score || 100)}`}>
                                    {(asset.mdi_score || 100).toFixed(0)}
                                </span>
                            </div>
                            <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
                                <span className="px-2 py-1 bg-dark-700 text-dark-300 rounded text-xs capitalize">
                                    {asset.asset_type}
                                </span>
                                <div className="flex items-center gap-4 text-xs">
                                    <span className={asset.current_debt > 0 ? 'text-red-400' : 'text-green-400'}>
                                        {formatCurrency(asset.current_debt || 0)}
                                    </span>
                                    {asset.open_issue_count > 0 && (
                                        <span className="flex items-center gap-1 text-yellow-400">
                                            <AlertTriangle className="w-3 h-3" />
                                            {asset.open_issue_count}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </Link>
                    ))
                )}
            </div>

            {/* Desktop Table View */}
            <div className="hidden md:block glass-card rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/5">
                                <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Asset</th>
                                <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Type</th>
                                <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">MDI Score</th>
                                <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Current Debt</th>
                                <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Issues</th>
                                <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Location</th>
                                <th className="px-6 py-4"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="text-center py-12">
                                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500 mx-auto"></div>
                                        <p className="text-dark-400 mt-2">Loading assets...</p>
                                    </td>
                                </tr>
                            ) : assets.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="text-center py-12 text-dark-400">
                                        No assets found. Try adjusting your filters.
                                    </td>
                                </tr>
                            ) : (
                                assets.map((asset) => (
                                    <tr key={asset.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">{getAssetTypeIcon(asset.asset_type)}</span>
                                                <div>
                                                    <p className="text-white font-medium">{asset.name}</p>
                                                    <p className="text-dark-500 text-sm">{asset.asset_code}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-3 py-1 bg-dark-700 text-dark-300 rounded-full text-sm capitalize">
                                                {asset.asset_type}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`text-lg font-bold ${getMDIColor(asset.mdi_score || 100)}`}>
                                                {(asset.mdi_score || 100).toFixed(1)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={asset.current_debt > 0 ? 'text-red-400' : 'text-green-400'}>
                                                {formatCurrency(asset.current_debt || 0)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {asset.open_issue_count > 0 ? (
                                                <span className="flex items-center gap-1 text-yellow-400">
                                                    <AlertTriangle className="w-4 h-4" />
                                                    {asset.open_issue_count}
                                                </span>
                                            ) : (
                                                <span className="text-green-400">None</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-dark-400">
                                            {asset.zone || 'N/A'}
                                        </td>
                                        <td className="px-6 py-4">
                                            <Link
                                                to={`/assets/${asset.id}`}
                                                className="p-2 hover:bg-white/10 rounded-lg transition-colors inline-block"
                                            >
                                                <ChevronRight className="w-5 h-5 text-dark-400" />
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-2">
                    <p className="text-dark-400 text-sm">
                        Page {page} of {totalPages} ({total} assets)
                    </p>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-4 py-2 bg-dark-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-600 transition-colors text-sm"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-4 py-2 bg-dark-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-600 transition-colors text-sm"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
