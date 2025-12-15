import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ChevronRight, AlertTriangle } from 'lucide-react';
import { getAssets } from '../services/api';
import { formatCurrency, getMDIColor, getAssetTypeIcon, formatDate } from '../utils/helpers';

export default function Assets() {
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [search, setSearch] = useState('');
    const [typeFilter, setTypeFilter] = useState('');

    useEffect(() => {
        loadAssets();
    }, [page, search, typeFilter]);

    const loadAssets = async () => {
        setLoading(true);
        try {
            const response = await getAssets({
                page,
                page_size: 15,
                search: search || undefined,
                asset_type: typeFilter || undefined,
            });
            setAssets(response.data.items);
            setTotalPages(response.data.total_pages);
        } catch (error) {
            console.error('Error loading assets:', error);
        } finally {
            setLoading(false);
        }
    };

    const assetTypes = ['road', 'drain', 'streetlight', 'bridge', 'sidewalk'];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Assets</h1>
                    <p className="text-dark-400 mt-1">Manage urban infrastructure assets</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                    <input
                        type="text"
                        placeholder="Search assets..."
                        value={search}
                        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                        className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
                    />
                </div>
                <select
                    value={typeFilter}
                    onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
                    className="px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                >
                    <option value="">All Types</option>
                    {assetTypes.map((type) => (
                        <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                    ))}
                </select>
            </div>

            {/* Table */}
            <div className="glass-card rounded-2xl overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-white/5">
                            <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Asset</th>
                            <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Type</th>
                            <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">MDI Score</th>
                            <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Current Debt</th>
                            <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Issues</th>
                            <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Last Maintenance</th>
                            <th className="px-6 py-4"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={7} className="text-center py-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500 mx-auto"></div>
                                </td>
                            </tr>
                        ) : assets.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="text-center py-12 text-dark-400">No assets found</td>
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
                                        {formatDate(asset.last_maintenance_date)}
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

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between px-6 py-4 border-t border-white/5">
                        <p className="text-dark-400 text-sm">
                            Page {page} of {totalPages}
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-4 py-2 bg-dark-700 text-white rounded-lg disabled:opacity-50"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-4 py-2 bg-dark-700 text-white rounded-lg disabled:opacity-50"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
