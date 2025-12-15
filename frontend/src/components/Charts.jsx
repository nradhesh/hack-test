import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { getMDIHexColor } from '../utils/helpers';

// Custom tooltip
function CustomTooltip({ active, payload, label, formatter }) {
    if (!active || !payload?.length) return null;

    return (
        <div className="glass rounded-lg p-3 shadow-xl border border-white/10">
            <p className="text-dark-300 text-sm mb-2">{label}</p>
            {payload.map((item, idx) => (
                <p key={idx} className="text-sm font-medium" style={{ color: item.color }}>
                    {item.name}: {formatter ? formatter(item.value) : item.value}
                </p>
            ))}
        </div>
    );
}

// Debt growth chart
export function DebtGrowthChart({ data, height = 300 }) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                    <linearGradient id="debtGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip formatter={(v) => `₹${v.toLocaleString()}`} />} />
                <Area
                    type="monotone"
                    dataKey="debt"
                    stroke="#ef4444"
                    fill="url(#debtGradient)"
                    strokeWidth={2}
                    name="Maintenance Debt"
                />
            </AreaChart>
        </ResponsiveContainer>
    );
}

// MDI Score trend chart
export function ScoreTrendChart({ data, height = 300 }) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                <YAxis domain={[0, 100]} stroke="#64748b" fontSize={12} />
                <Tooltip content={<CustomTooltip formatter={(v) => v.toFixed(1)} />} />
                <Line
                    type="monotone"
                    dataKey="mdi_score"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    dot={{ fill: '#38bdf8', strokeWidth: 0, r: 4 }}
                    name="MDI Score"
                />
            </LineChart>
        </ResponsiveContainer>
    );
}

// Cost comparison bar chart
export function CostComparisonChart({ data, height = 300 }) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip formatter={(v) => `₹${v.toLocaleString()}`} />} />
                <Legend />
                <Bar dataKey="baseCost" fill="#38bdf8" name="Base Cost" radius={[4, 4, 0, 0]} />
                <Bar dataKey="currentCost" fill="#f97316" name="Current Cost" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

// Ward score comparison
export function WardScoreChart({ data, height = 400 }) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} layout="vertical" margin={{ top: 10, right: 10, left: 80, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                    dataKey="mdi_score"
                    name="MDI Score"
                    radius={[0, 4, 4, 0]}
                    fill="#38bdf8"
                >
                    {data?.map((entry, index) => (
                        <rect key={index} fill={getMDIHexColor(entry.mdi_score)} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
}

// Simulation chart
export function SimulationChart({ data, height = 350 }) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                    <linearGradient id="simGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day_offset" stroke="#64748b" fontSize={12} label={{ value: 'Days', position: 'bottom' }} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip formatter={(v) => `₹${v.toLocaleString()}`} />} />
                <Legend />
                <Line type="monotone" dataKey="base_cost" stroke="#38bdf8" strokeDasharray="5 5" name="Base Cost" dot={false} />
                <Area type="monotone" dataKey="current_cost" stroke="#f97316" fill="url(#simGradient)" strokeWidth={2} name="Projected Cost" />
            </AreaChart>
        </ResponsiveContainer>
    );
}
