import { useState } from 'react';
import { Calculator, Play, Clock, DollarSign, AlertTriangle } from 'lucide-react';
import { SimulationChart } from '../components/Charts';
import { simulateDebt } from '../services/api';
import { formatCurrency, formatMultiplier, formatDate } from '../utils/helpers';

export default function Simulator() {
    const [formData, setFormData] = useState({
        base_cost: 50000,
        report_date: new Date().toISOString().split('T')[0],
        asset_type: 'road',
        severity: 'medium',
        future_days: 60,
    });
    const [simulation, setSimulation] = useState(null);
    const [loading, setLoading] = useState(false);

    const runSimulation = async () => {
        setLoading(true);
        try {
            const response = await simulateDebt(formData);
            setSimulation(response.data);
        } catch (error) {
            console.error('Simulation error:', error);
            // Generate demo simulation
            generateDemoSimulation();
        } finally {
            setLoading(false);
        }
    };

    const generateDemoSimulation = () => {
        const points = [];
        const baseCost = formData.base_cost;
        const decayRate = 0.02;

        for (let i = 0; i <= formData.future_days; i++) {
            const slaBreachDay = formData.asset_type === 'road' ? 14 : 7;
            const delayDays = Math.max(0, i - slaBreachDay);
            const multiplier = Math.min(10, Math.pow(1 + decayRate, delayDays));
            const currentCost = baseCost * multiplier;

            points.push({
                date: new Date(Date.now() + i * 86400000).toISOString().split('T')[0],
                day_offset: i,
                base_cost: baseCost,
                current_cost: currentCost,
                debt: currentCost - baseCost,
                multiplier: multiplier,
                delay_days: delayDays,
                is_overdue: delayDays > 0,
            });
        }

        setSimulation({
            simulation_points: points,
            starting_cost: baseCost,
            ending_cost: points[points.length - 1].current_cost,
            total_debt_accumulated: points[points.length - 1].debt,
            max_multiplier: points[points.length - 1].multiplier,
            sla_breach_date: points.find(p => p.is_overdue)?.date,
            double_cost_date: points.find(p => p.multiplier >= 2)?.date,
            triple_cost_date: points.find(p => p.multiplier >= 3)?.date,
        });
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Debt Simulator</h1>
                <p className="text-dark-400 mt-1">Visualize how maintenance delays increase costs over time</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Input Form */}
                <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Calculator className="w-5 h-5 text-primary-400" />
                        Simulation Parameters
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-dark-400 text-sm mb-2">Base Repair Cost (₹)</label>
                            <input
                                type="number"
                                value={formData.base_cost}
                                onChange={(e) => handleChange('base_cost', parseFloat(e.target.value))}
                                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                            />
                        </div>

                        <div>
                            <label className="block text-dark-400 text-sm mb-2">Issue Report Date</label>
                            <input
                                type="date"
                                value={formData.report_date}
                                onChange={(e) => handleChange('report_date', e.target.value)}
                                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                            />
                        </div>

                        <div>
                            <label className="block text-dark-400 text-sm mb-2">Asset Type</label>
                            <select
                                value={formData.asset_type}
                                onChange={(e) => handleChange('asset_type', e.target.value)}
                                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                            >
                                <option value="road">Road (14 days SLA)</option>
                                <option value="drain">Drain (7 days SLA)</option>
                                <option value="streetlight">Streetlight (3 days SLA)</option>
                                <option value="bridge">Bridge (21 days SLA)</option>
                                <option value="sidewalk">Sidewalk (10 days SLA)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-dark-400 text-sm mb-2">Severity</label>
                            <select
                                value={formData.severity}
                                onChange={(e) => handleChange('severity', e.target.value)}
                                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                            >
                                <option value="low">Low (1× multiplier)</option>
                                <option value="medium">Medium (1.5× multiplier)</option>
                                <option value="high">High (2× multiplier)</option>
                                <option value="critical">Critical (3× multiplier)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-dark-400 text-sm mb-2">Simulate Days: {formData.future_days}</label>
                            <input
                                type="range"
                                min="7"
                                max="180"
                                value={formData.future_days}
                                onChange={(e) => handleChange('future_days', parseInt(e.target.value))}
                                className="w-full"
                            />
                        </div>

                        <button
                            onClick={runSimulation}
                            disabled={loading}
                            className="w-full py-3 bg-gradient-to-r from-primary-500 to-purple-600 text-white rounded-xl font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {loading ? (
                                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                            ) : (
                                <>
                                    <Play className="w-5 h-5" />
                                    Run Simulation
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Results */}
                <div className="lg:col-span-2 space-y-6">
                    {simulation ? (
                        <>
                            {/* Chart */}
                            <div className="glass-card rounded-2xl p-6">
                                <h3 className="text-lg font-semibold text-white mb-4">Cost Projection Over Time</h3>
                                <SimulationChart data={simulation.simulation_points} height={300} />
                            </div>

                            {/* Summary Cards */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="glass-card rounded-xl p-4">
                                    <div className="flex items-center gap-2 text-dark-400 text-sm mb-2">
                                        <DollarSign className="w-4 h-4" />
                                        Starting Cost
                                    </div>
                                    <p className="text-xl font-bold text-white">{formatCurrency(simulation.starting_cost)}</p>
                                </div>
                                <div className="glass-card rounded-xl p-4">
                                    <div className="flex items-center gap-2 text-dark-400 text-sm mb-2">
                                        <DollarSign className="w-4 h-4" />
                                        Ending Cost
                                    </div>
                                    <p className="text-xl font-bold text-red-400">{formatCurrency(simulation.ending_cost)}</p>
                                </div>
                                <div className="glass-card rounded-xl p-4">
                                    <div className="flex items-center gap-2 text-dark-400 text-sm mb-2">
                                        <AlertTriangle className="w-4 h-4" />
                                        Total Debt
                                    </div>
                                    <p className="text-xl font-bold text-orange-400">{formatCurrency(simulation.total_debt_accumulated)}</p>
                                </div>
                                <div className="glass-card rounded-xl p-4">
                                    <div className="flex items-center gap-2 text-dark-400 text-sm mb-2">
                                        <Clock className="w-4 h-4" />
                                        Max Multiplier
                                    </div>
                                    <p className="text-xl font-bold text-yellow-400">{formatMultiplier(simulation.max_multiplier)}</p>
                                </div>
                            </div>

                            {/* Milestones */}
                            <div className="glass-card rounded-2xl p-6">
                                <h3 className="text-lg font-semibold text-white mb-4">Key Milestones</h3>
                                <div className="space-y-3">
                                    {simulation.sla_breach_date && (
                                        <div className="flex items-center justify-between p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                            <span className="text-yellow-400">SLA Breach</span>
                                            <span className="text-white font-medium">{formatDate(simulation.sla_breach_date)}</span>
                                        </div>
                                    )}
                                    {simulation.double_cost_date && (
                                        <div className="flex items-center justify-between p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
                                            <span className="text-orange-400">Cost Doubles (2×)</span>
                                            <span className="text-white font-medium">{formatDate(simulation.double_cost_date)}</span>
                                        </div>
                                    )}
                                    {simulation.triple_cost_date && (
                                        <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                            <span className="text-red-400">Cost Triples (3×)</span>
                                            <span className="text-white font-medium">{formatDate(simulation.triple_cost_date)}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="glass-card rounded-2xl p-12 text-center">
                            <Calculator className="w-16 h-16 text-dark-600 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-white mb-2">Ready to Simulate</h3>
                            <p className="text-dark-400 max-w-md mx-auto">
                                Configure the parameters on the left and click "Run Simulation" to see how maintenance costs
                                escalate over time when repairs are delayed.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
