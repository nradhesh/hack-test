import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, AlertTriangle, TrendingUp, Calendar } from 'lucide-react';
import ScoreGauge from '../components/ScoreGauge';
import { DebtGrowthChart, ScoreTrendChart, SimulationChart } from '../components/Charts';
import { getAsset, getAssetDebt, getAssetDebtHistory, explainAsset, simulateDebt } from '../services/api';
import { formatCurrency, getMDIColor, getAssetTypeIcon, formatDate, formatMultiplier } from '../utils/helpers';

export default function AssetDetail() {
    const { id } = useParams();
    const [asset, setAsset] = useState(null);
    const [debt, setDebt] = useState(null);
    const [history, setHistory] = useState([]);
    const [explanation, setExplanation] = useState(null);
    const [simulation, setSimulation] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, [id]);

    const loadData = async () => {
        try {
            const [assetRes, debtRes, historyRes, explainRes, simRes] = await Promise.all([
                getAsset(id),
                getAssetDebt(id),
                getAssetDebtHistory(id, 30),
                explainAsset(id),
                simulateDebt({ asset_id: parseInt(id), future_days: 60 }),
            ]);
            setAsset(assetRes.data);
            setDebt(debtRes.data);
            setHistory(historyRes.data.snapshots || []);
            setExplanation(explainRes.data);
            setSimulation(simRes.data);
        } catch (error) {
            console.error('Error loading asset:', error);
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

    if (!asset) {
        return (
            <div className="text-center py-12">
                <p className="text-dark-400">Asset not found</p>
                <Link to="/assets" className="text-primary-400 hover:underline mt-4 inline-block">Back to Assets</Link>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link to="/assets" className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                    <ArrowLeft className="w-5 h-5 text-dark-400" />
                </Link>
                <div className="flex-1">
                    <div className="flex items-center gap-3">
                        <span className="text-3xl">{getAssetTypeIcon(asset.asset_type)}</span>
                        <div>
                            <h1 className="text-2xl font-bold text-white">{asset.name}</h1>
                            <p className="text-dark-400">{asset.asset_code} • {asset.asset_type}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Score & Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Score Card */}


            
                <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center">
                    <ScoreGauge score={asset.mdi_score || 100} size="lg" />
                </div>

                {/* Debt Summary */}
                <div className="glass-card rounded-2xl p-6 lg:col-span-2">
                    <h3 className="text-lg font-semibold text-white mb-4">Debt Summary</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm mb-1">Base Cost</p>
                            <p className="text-xl font-bold text-white">{formatCurrency(debt?.total_base_cost || asset.base_repair_cost)}</p>
                        </div>
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm mb-1">Current Cost</p>
                            <p className="text-xl font-bold text-red-400">{formatCurrency(debt?.total_current_cost || asset.base_repair_cost)}</p>
                        </div>
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm mb-1">Debt</p>
                            <p className="text-xl font-bold text-orange-400">{formatCurrency(debt?.total_debt || 0)}</p>
                        </div>
                        <div className="p-4 rounded-xl bg-dark-800/50">
                            <p className="text-dark-500 text-sm mb-1">Multiplier</p>
                            <p className="text-xl font-bold text-yellow-400">{formatMultiplier(debt?.avg_debt_multiplier || 1)}</p>
                        </div>
                    </div>

                    {/* Issues */}
                    <div className="mt-4 flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-yellow-400" />
                            <span className="text-dark-300">{debt?.open_issues || 0} open issues</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Clock className="w-5 h-5 text-red-400" />
                            <span className="text-dark-300">{debt?.overdue_issues || 0} overdue</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-dark-400" />
                            <span className="text-dark-300">Max delay: {debt?.max_delay_days || 0} days</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Explanation */}
            {explanation && (
                <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-3">{explanation.headline}</h3>
                    <p className="text-dark-300 mb-4">{explanation.summary}</p>
                    <div className="p-4 rounded-xl bg-dark-800/50 border-l-4 border-primary-500">
                        <p className="text-dark-400">{explanation.debt_explanation}</p>
                    </div>
                    {explanation.recommended_action && (
                        <div className="mt-4 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                            <p className="text-yellow-400 font-medium">Recommended: {explanation.recommended_action}</p>
                        </div>
                    )}
                </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Debt History */}
                <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Debt History (30 days)</h3>
                    {history.length > 0 ? (
                        <DebtGrowthChart data={history.map(h => ({ date: h.snapshot_date, debt: h.total_debt }))} height={250} />
                    ) : (
                        <p className="text-dark-400 text-center py-8">No historical data available</p>
                    )}
                </div>

                {/* Future Simulation */}
                <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Cost Projection (60 days)</h3>
                    {simulation?.simulation_points ? (
                        <SimulationChart data={simulation.simulation_points} height={250} />
                    ) : (
                        <p className="text-dark-400 text-center py-8">Unable to generate simulation</p>
                    )}
                </div>
            </div>

            {/* Issue Details */}
            {debt?.issue_debts?.length > 0 && (
                <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Issue Breakdown</h3>
                    <div className="space-y-3">
                        {debt.issue_debts.map((issue) => (
                            <div key={issue.issue_id} className="flex items-center justify-between p-4 rounded-xl bg-dark-800/50">
                                <div>
                                    <p className="text-white font-medium">Issue #{issue.issue_id}</p>
                                    <p className="text-dark-500 text-sm">
                                        {issue.delay_days > 0 ? `${issue.delay_days} days overdue` : 'Within SLA'}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-dark-300">
                                        {formatCurrency(issue.base_cost)} → <span className="text-red-400">{formatCurrency(issue.current_cost)}</span>
                                    </p>
                                    <p className="text-dark-500 text-sm">{formatMultiplier(issue.debt_multiplier)} multiplier</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
