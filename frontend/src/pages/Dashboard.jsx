import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    Building2, AlertTriangle, TrendingDown, DollarSign,
    Clock, MapPin, Activity, ArrowRight, RefreshCw
} from 'lucide-react';
import StatCard from '../components/StatCard';
import ScoreGauge from '../components/ScoreGauge';
import { DebtGrowthChart, WardScoreChart } from '../components/Charts';
import { getDashboard, getCityScore, getAllWardScores } from '../services/api';
import { formatCurrency, getMDIColor } from '../utils/helpers';

export default function Dashboard() {
    const [loading, setLoading] = useState(true);
    const [dashboard, setDashboard] = useState(null);
    const [cityScore, setCityScore] = useState(null);
    const [wardScores, setWardScores] = useState([]);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [dashRes, cityRes, wardsRes] = await Promise.all([
                getDashboard(),
                getCityScore(),
                getAllWardScores({ sort_by: 'score', order: 'desc' }),
            ]);
            setDashboard(dashRes.data);
            setCityScore(cityRes.data);
            setWardScores(wardsRes.data);
        } catch (error) {
            console.error('Error loading dashboard:', error);
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

    const mockDebtHistory = Array.from({ length: 30 }, (_, i) => ({
        date: `Day ${i + 1}`,
        debt: Math.floor(50000 + i * 2000 + Math.random() * 5000),
    }));

    return (
        <div className="space-y-4 md:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-white">Dashboard</h1>
                    <p className="text-dark-400 text-sm md:text-base mt-1">Urban Infrastructure Health Overview</p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-dark-400 text-xs md:text-sm hidden sm:inline">Last updated: Just now</span>
                    <button
                        onClick={loadData}
                        className="px-3 md:px-4 py-2 bg-primary-500/20 text-primary-400 rounded-lg hover:bg-primary-500/30 transition-colors flex items-center gap-2 text-sm"
                    >
                        <RefreshCw className="w-4 h-4" />
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                </div>
            </div>

            {/* City Score Hero */}
            <div className="glass-card rounded-2xl p-4 md:p-8 gradient-border">
                <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
                    {/* Score Gauge - First on mobile */}
                    <div className="order-first md:order-last">
                        <ScoreGauge score={cityScore?.mdi_score || 85} size="lg" />
                    </div>

                    <div className="flex-1 text-center md:text-left">
                        <h2 className="text-lg md:text-xl font-semibold text-white mb-2">City MDI Score</h2>
                        <p className="text-dark-400 text-sm mb-6 max-w-xl">
                            The Maintenance Debt Index measures the overall health of urban infrastructure.
                            A higher score indicates well-maintained assets.
                        </p>
                        <div className="grid grid-cols-3 gap-3 md:gap-6">
                            <div>
                                <p className="text-dark-500 text-xs md:text-sm mb-1">Total Debt</p>
                                <p className="text-lg md:text-2xl font-bold text-red-400">
                                    {formatCurrency(cityScore?.total_debt || 0)}
                                </p>
                            </div>
                            <div>
                                <p className="text-dark-500 text-xs md:text-sm mb-1">Total Assets</p>
                                <p className="text-lg md:text-2xl font-bold text-white">
                                    {cityScore?.total_assets || 0}
                                </p>
                            </div>
                            <div>
                                <p className="text-dark-500 text-xs md:text-sm mb-1">Open Issues</p>
                                <p className="text-lg md:text-2xl font-bold text-yellow-400">
                                    {cityScore?.total_open_issues || 0}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                <StatCard
                    title="Total Wards"
                    value={cityScore?.total_wards || 0}
                    icon={MapPin}
                    color="purple"
                    subtitle="Administrative divisions"
                />
                <StatCard
                    title="Wards Critical"
                    value={cityScore?.wards_critical || 0}
                    icon={AlertTriangle}
                    color="red"
                    subtitle="Needing attention"
                />
                <StatCard
                    title="Debt Change (7d)"
                    value={formatCurrency(dashboard?.debt_change_7d || 0)}
                    icon={TrendingDown}
                    color="yellow"
                    trend={dashboard?.debt_change_7d > 0 ? 'up' : 'down'}
                />
                <StatCard
                    title="Issues Today"
                    value={dashboard?.issues_reported_today || 0}
                    icon={Activity}
                    color="primary"
                    subtitle={`${dashboard?.issues_resolved_today || 0} resolved`}
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
                {/* Debt Growth */}
                <div className="glass-card rounded-2xl p-4 md:p-6">
                    <h3 className="text-base md:text-lg font-semibold text-white mb-4">City Debt Trend</h3>
                    <div className="h-[200px] md:h-[280px]">
                        <DebtGrowthChart data={mockDebtHistory} height={200} />
                    </div>
                </div>

                {/* Ward Rankings */}
                <div className="glass-card rounded-2xl p-4 md:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base md:text-lg font-semibold text-white">Ward Rankings</h3>
                        <Link to="/wards" className="text-primary-400 text-sm hover:underline flex items-center gap-1">
                            View all <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                    <div className="space-y-2 md:space-y-3">
                        {wardScores.slice(0, 5).map((ward, idx) => (
                            <div key={ward.ward_id} className="flex items-center gap-3 md:gap-4 p-2 md:p-3 rounded-lg bg-dark-800/50">
                                <span className={`w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center text-xs md:text-sm font-bold ${idx === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                                    idx === 1 ? 'bg-gray-400/20 text-gray-300' :
                                        idx === 2 ? 'bg-amber-600/20 text-amber-500' :
                                            'bg-dark-700 text-dark-400'
                                    }`}>
                                    {idx + 1}
                                </span>
                                <div className="flex-1 min-w-0">
                                    <p className="text-white font-medium text-sm md:text-base truncate">{ward.ward_name}</p>
                                    <p className="text-dark-500 text-xs">{ward.total_assets} assets</p>
                                </div>
                                <div className="text-right">
                                    <p className={`font-bold text-sm md:text-base ${getMDIColor(ward.mdi_score)}`}>
                                        {ward.mdi_score.toFixed(1)}
                                    </p>
                                    <p className="text-dark-500 text-xs hidden sm:block">{ward.score_category}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Category Breakdown */}
            <div className="glass-card rounded-2xl p-4 md:p-6">
                <h3 className="text-base md:text-lg font-semibold text-white mb-4">Ward Health Distribution</h3>
                <div className="grid grid-cols-5 gap-2 md:gap-4">
                    {[
                        { label: 'Excellent', count: cityScore?.wards_excellent || 0, color: 'bg-mdi-excellent' },
                        { label: 'Good', count: cityScore?.wards_good || 0, color: 'bg-mdi-good' },
                        { label: 'Fair', count: cityScore?.wards_fair || 0, color: 'bg-mdi-fair' },
                        { label: 'Poor', count: cityScore?.wards_poor || 0, color: 'bg-mdi-poor' },
                        { label: 'Critical', count: cityScore?.wards_critical || 0, color: 'bg-mdi-critical' },
                    ].map((item) => (
                        <div key={item.label} className="text-center">
                            <div className={`w-10 h-10 md:w-16 md:h-16 mx-auto rounded-lg md:rounded-xl ${item.color} flex items-center justify-center mb-1 md:mb-2`}>
                                <span className="text-lg md:text-2xl font-bold text-white">{item.count}</span>
                            </div>
                            <p className="text-dark-400 text-xs md:text-sm">{item.label}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
