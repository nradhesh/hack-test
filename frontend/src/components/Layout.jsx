import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Map,
    Building2,
    MapPin,
    Calculator,
    Activity,
    TrendingDown,
    Settings
} from 'lucide-react';

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/map', icon: Map, label: 'City Map' },
    { path: '/assets', icon: Building2, label: 'Assets' },
    { path: '/wards', icon: MapPin, label: 'Wards' },
    { path: '/simulator', icon: Calculator, label: 'Simulator' },
    { path: '/admin', icon: Settings, label: 'Admin' },
];

export default function Layout({ children }) {
    const location = useLocation();

    return (
        <div className="min-h-screen flex">
            {/* Sidebar */}
            <aside className="w-64 glass-card border-r border-white/5 flex flex-col">
                {/* Logo */}
                <div className="p-6 border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
                            <TrendingDown className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-gradient">MDI</h1>
                            <p className="text-xs text-dark-400">Maintenance Debt Index</p>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4">
                    <ul className="space-y-2">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            const Icon = item.icon;

                            return (
                                <li key={item.path}>
                                    <Link
                                        to={item.path}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${isActive
                                            ? 'bg-primary-500/20 text-primary-400 shadow-lg shadow-primary-500/10'
                                            : 'text-dark-400 hover:text-white hover:bg-white/5'
                                            }`}
                                    >
                                        <Icon className="w-5 h-5" />
                                        <span className="font-medium">{item.label}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                {/* Status indicator */}
                <div className="p-4 border-t border-white/5">
                    <div className="glass rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Activity className="w-4 h-4 text-green-500" />
                            <span className="text-sm text-dark-300">System Status</span>
                        </div>
                        <p className="text-xs text-dark-500">All services operational</p>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-auto">
                <div className="p-6">
                    {children}
                </div>
            </main>
        </div>
    );
}
