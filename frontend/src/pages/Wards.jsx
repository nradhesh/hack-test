import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, TrendingUp, TrendingDown, ChevronRight } from 'lucide-react';
import ScoreGauge from '../components/ScoreGauge';
import { getAllWardScores, getCityScore } from '../services/api';
import { formatCurrency, getMDIColor, getMDIBgColor } from '../utils/helpers';

export default function Wards() {
    const [wards, setWards] = useState([]);
    const [cityScore, setCityScore] = useState(null);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState('score');

    useEffect(() => {
        loadData();
    }, [sortBy]);

    const loadData = async () => {
        try {
            const [wardsRes, cityRes] = await Promise.all([
                getAllWardScores({ sort_by: sortBy, order: sortBy === 'name' ? 'asc' : 'desc' }),
                getCityScore(),
            ]);
            setWards(wardsRes.data);
            setCityScore(cityRes.data);
        } catch (error) {
            console.error('Error loading wards:', error);
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
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Wards</h1>
                    <p className="text-dark-400 mt-1">Administrative ward health overview</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-dark-400 text-sm">Sort by:</span>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
                    >
                        <option value="score">MDI Score</option>
                        <option value="debt">Total Debt</option>
                        <option value="name">Name</option>
                    </select>
                </div>
            </div>

            {/* City Summary */}
            {cityScore && (
                <div className="glass-card rounded-2xl p-6 gradient-border">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-white mb-2">City Overview</h2>
                            <div className="grid grid-cols-4 gap-6 mt-4">
                                <div>
                                    <p className="text-dark-500 text-sm">Total Wards</p>
                                    <p className="text-2xl font-bold text-white">{cityScore.total_wards}</p>
                                </div>
                                <div>
                                    <p className="text-dark-500 text-sm">Total Assets</p>
                                    <p className="text-2xl font-bold text-white">{cityScore.total_assets}</p>
                                </div>
                                <div>
                                    <p className="text-dark-500 text-sm">Total Debt</p>
                                    <p className="text-2xl font-bold text-red-400">{formatCurrency(cityScore.total_debt)}</p>
                                </div>
                                <div>
                                    <p className="text-dark-500 text-sm">Open Issues</p>
                                    <p className="text-2xl font-bold text-yellow-400">{cityScore.total_open_issues}</p>
                                </div>
                            </div>
                        </div>
                        <ScoreGauge score={cityScore.mdi_score} size="md" />
                    </div>
                </div>
            )}

            {/* Ward Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {wards.map((ward, idx) => (
                    <div key={ward.ward_id} className="glass-card rounded-2xl p-5 hover:border-primary-500/30 transition-all">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-xl ${getMDIBgColor(ward.mdi_score)} bg-opacity-20 flex items-center justify-center`}>
                                    <span className={`font-bold ${getMDIColor(ward.mdi_score)}`}>#{ward.city_rank || idx + 1}</span>
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold">{ward.ward_name}</h3>
                                    <p className="text-dark-500 text-sm">{ward.zone}</p>
                                </div>
                            </div>
                            <span className={`text-2xl font-bold ${getMDIColor(ward.mdi_score)}`}>
                                {ward.mdi_score.toFixed(0)}
                            </span>
                        </div>

                        <div className="grid grid-cols-3 gap-3 mb-4">
                            <div className="p-2 rounded-lg bg-dark-800/50 text-center">
                                <p className="text-dark-500 text-xs">Assets</p>
                                <p className="text-white font-medium">{ward.total_assets}</p>
                            </div>
                            <div className="p-2 rounded-lg bg-dark-800/50 text-center">
                                <p className="text-dark-500 text-xs">Issues</p>
                                <p className="text-yellow-400 font-medium">{ward.open_issues}</p>
                            </div>
                            <div className="p-2 rounded-lg bg-dark-800/50 text-center">
                                <p className="text-dark-500 text-xs">Overdue</p>
                                <p className="text-red-400 font-medium">{ward.overdue_issues}</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-3 border-t border-white/5">
                            <div>
                                <p className="text-dark-500 text-xs">Total Debt</p>
                                <p className="text-red-400 font-medium">{formatCurrency(ward.total_debt)}</p>
                            </div>
                            {ward.score_change_7d !== null && (
                                <div className={`flex items-center gap-1 ${ward.score_change_7d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {ward.score_change_7d >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                    <span className="text-sm">{Math.abs(ward.score_change_7d).toFixed(1)}</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
