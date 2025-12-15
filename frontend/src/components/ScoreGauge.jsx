import { getMDIColor, getMDIBgColor, getMDICategory } from '../utils/helpers';

export default function ScoreGauge({ score, size = 'md', showLabel = true }) {
    const sizes = {
        sm: { width: 80, stroke: 6, fontSize: 'text-lg' },
        md: { width: 120, stroke: 8, fontSize: 'text-2xl' },
        lg: { width: 180, stroke: 10, fontSize: 'text-4xl' },
    };

    const { width, stroke, fontSize } = sizes[size] || sizes.md;
    const radius = (width - stroke) / 2;
    const circumference = 2 * Math.PI * radius;
    const progress = (score / 100) * circumference;
    const offset = circumference - progress;

    return (
        <div className="flex flex-col items-center">
            <div className="relative" style={{ width, height: width }}>
                <svg className="transform -rotate-90" width={width} height={width}>
                    {/* Background circle */}
                    <circle
                        cx={width / 2}
                        cy={width / 2}
                        r={radius}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={stroke}
                        className="text-dark-700"
                    />
                    {/* Progress circle */}
                    <circle
                        cx={width / 2}
                        cy={width / 2}
                        r={radius}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={stroke}
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        strokeLinecap="round"
                        className={getMDIColor(score)}
                        style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`font-bold ${fontSize} ${getMDIColor(score)}`}>
                        {score.toFixed(0)}
                    </span>
                    {showLabel && (
                        <span className="text-xs text-dark-400 mt-1">MDI Score</span>
                    )}
                </div>
            </div>
            {showLabel && (
                <div className={`mt-2 px-3 py-1 rounded-full text-xs font-medium ${getMDIBgColor(score)} bg-opacity-20 ${getMDIColor(score)}`}>
                    {getMDICategory(score)}
                </div>
            )}
        </div>
    );
}
