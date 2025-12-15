import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import ScoreGauge from '../components/ScoreGauge';
import { getAllWardScores, getCityScore } from '../services/api';
import { formatCurrency, getMDIColor, getMDIBgColor } from '../utils/helpers';

export default function Wards() {
    const [wards, setWards] = useState([]);
    const [cityScore, setCityScore] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortBy, setSortBy] = useState('score');

    useEffect(() => {
        loadData();
    }, [sortBy]);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [wardsRes, cityRes] = await Promise.all([
                getAllWardScores({ sort_by: sortBy, order: sortBy === 'name' ? 'asc' : 'desc' }),
                getCityScore(),
            ]);
            setWards(wardsRes.data || []);
            setCityScore(cityRes.data);
        } catch (error) {
            console.error('Error loading wards:', error);
            setError('Failed to load ward data. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-4 md:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-white">Wards</h1>
                    <p className="text-dark-400 text-sm md:text-base mt-1">Administrative ward health overview ({wards.length} wards)</p>
                </div>
                <div className="flex items-center gap-2 sm:gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-dark-400 text-xs sm:text-sm hidden sm:inline">Sort:</span>
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="px-2 sm:px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-xs sm:text-sm"
                        >
                            <option value="score">MDI Score</option>
                            <option value="debt">Total Debt</option>
                            <option value="name">Name</option>
                        </select>
                    </div>
                    <button
                        onClick={loadData}
                        className="px-3 sm:px-4 py-2 bg-primary-500/20 text-primary-400 rounded-lg hover:bg-primary-500/30 transition-colors flex items-center gap-2 text-sm"
                    >
                        <RefreshCw className="w-4 h-4" />
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400 text-sm">
                    {error}
                </div>
            )}

            {/* City Summary */}
            {cityScore && (
                <div className="glass-card rounded-2xl p-4 md:p-6 gradient-border">
                    <div className="flex flex-col md:flex-row items-center md:items-start gap-4 md:gap-6">
                        <div className="order-first md:order-last">
                            <ScoreGauge score={cityScore.mdi_score || 75} size="md" />
                        </div>
                        <div className="flex-1 text-center md:text-left">
                            <h2 className="text-lg md:text-xl font-semibold text-white mb-4">City Overview</h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-6">
                                <div>
                                    <p className="text-dark-500 text-xs md:text-sm">Total Wards</p>
                                    <p className="text-xl md:text-2xl font-bold text-white">{cityScore.total_wards || wards.length}</p>
                                </div>
                                <div>
                                    <p className="text-dark-500 text-xs md:text-sm">Total Assets</p>
                                    <p className="text-xl md:text-2xl font-bold text-white">{cityScore.total_assets || 0}</p>
                                </div>
                                <div>
                                    <p className="text-dark-500 text-xs md:text-sm">Total Debt</p>
                                    <p className="text-xl md:text-2xl font-bold text-red-400">{formatCurrency(cityScore.total_debt || 0)}</p>
                                </div>
                                <div>
                                    <p className="text-dark-500 text-xs md:text-sm">Open Issues</p>
                                    <p className="text-xl md:text-2xl font-bold text-yellow-400">{cityScore.total_open_issues || 0}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Ward Grid */}
            {wards.length === 0 ? (
                <div className="glass-card rounded-2xl p-12 text-center">
                    <p className="text-dark-400">No wards found</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
                    {wards.map((ward, idx) => (
                        <div key={ward.ward_id || idx} className="glass-card rounded-xl md:rounded-2xl p-4 md:p-5 hover:border-primary-500/30 transition-all">
                            <div className="flex items-start justify-between mb-3 md:mb-4">
                                <div className="flex items-center gap-2 md:gap-3">
                                    <div className={`w-8 h-8 md:w-10 md:h-10 rounded-lg md:rounded-xl ${getMDIBgColor(ward.mdi_score)} bg-opacity-20 flex items-center justify-center`}>
                                        <span className={`text-sm md:text-base font-bold ${getMDIColor(ward.mdi_score)}`}>#{ward.city_rank || idx + 1}</span>
                                    </div>
                                    <div>
                                        <h3 className="text-white font-semibold text-sm md:text-base">{ward.ward_name}</h3>
                                        <p className="text-dark-500 text-xs">{ward.zone || 'Zone'}</p>
                                    </div>
                                </div>
                                <span className={`text-xl md:text-2xl font-bold ${getMDIColor(ward.mdi_score)}`}>
                                    {ward.mdi_score?.toFixed(0) || '0'}
                                </span>
                            </div>

                            <div className="grid grid-cols-3 gap-2 md:gap-3 mb-3 md:mb-4">
                                <div className="p-2 rounded-lg bg-dark-800/50 text-center">
                                    <p className="text-dark-500 text-xs">Assets</p>
                                    <p className="text-white font-medium text-sm">{ward.total_assets || 0}</p>
                                </div>
                                <div className="p-2 rounded-lg bg-dark-800/50 text-center">
                                    <p className="text-dark-500 text-xs">Issues</p>
                                    <p className="text-yellow-400 font-medium text-sm">{ward.open_issues || 0}</p>
                                </div>
                                <div className="p-2 rounded-lg bg-dark-800/50 text-center">
                                    <p className="text-dark-500 text-xs">Overdue</p>
                                    <p className="text-red-400 font-medium text-sm">{ward.overdue_issues || 0}</p>
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-3 border-t border-white/5">
                                <div>
                                    <p className="text-dark-500 text-xs">Total Debt</p>
                                    <p className="text-red-400 font-medium text-sm">{formatCurrency(ward.total_debt || 0)}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-dark-500 text-xs">Category</p>
                                    <p className={`font-medium text-sm ${getMDIColor(ward.mdi_score)}`}>{ward.score_category || 'Good'}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
