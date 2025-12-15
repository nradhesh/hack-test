import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function StatCard({
    title,
    value,
    subtitle,
    icon: Icon,
    trend,
    trendValue,
    color = 'primary',
    className = ''
}) {
    const colors = {
        primary: 'from-primary-500 to-primary-600',
        green: 'from-green-500 to-emerald-600',
        yellow: 'from-yellow-500 to-amber-600',
        red: 'from-red-500 to-rose-600',
        purple: 'from-purple-500 to-violet-600',
    };

    const getTrendIcon = () => {
        if (trend === 'up') return <TrendingUp className="w-4 h-4" />;
        if (trend === 'down') return <TrendingDown className="w-4 h-4" />;
        return <Minus className="w-4 h-4" />;
    };

    const getTrendColor = () => {
        if (trend === 'up') return 'text-green-400';
        if (trend === 'down') return 'text-red-400';
        return 'text-dark-400';
    };

    return (
        <div className={`glass-card rounded-2xl p-6 ${className}`}>
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-dark-400 text-sm font-medium mb-1">{title}</p>
                    <h3 className="text-3xl font-bold text-white mb-1">{value}</h3>
                    {subtitle && (
                        <p className="text-dark-500 text-sm">{subtitle}</p>
                    )}
                </div>
                {Icon && (
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center shadow-lg`}>
                        <Icon className="w-6 h-6 text-white" />
                    </div>
                )}
            </div>

            {(trend || trendValue) && (
                <div className="mt-4 pt-4 border-t border-white/5 flex items-center gap-2">
                    <span className={`flex items-center gap-1 ${getTrendColor()}`}>
                        {getTrendIcon()}
                        {trendValue}
                    </span>
                    <span className="text-dark-500 text-sm">vs last week</span>
                </div>
            )}
        </div>
    );
}
