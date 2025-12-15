import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Map,
    Building2,
    MapPin,
    Calculator,
    Activity,
    TrendingDown,
    Settings,
    Menu,
    X
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
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
    const closeSidebar = () => setSidebarOpen(false);

    return (
        <div className="min-h-screen flex flex-col md:flex-row">
            {/* Mobile Header */}
            <div className="md:hidden glass-card border-b border-white/5 p-4 flex items-center justify-between sticky top-0 z-50">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
                        <TrendingDown className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h1 className="text-base font-bold text-gradient">MDI</h1>
                    </div>
                </div>
                <button
                    onClick={toggleSidebar}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                    {sidebarOpen ? <X className="w-6 h-6 text-white" /> : <Menu className="w-6 h-6 text-white" />}
                </button>
            </div>

            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="md:hidden fixed inset-0 bg-black/60 z-40"
                    onClick={closeSidebar}
                />
            )}

            {/* Sidebar */}
            <aside className={`
        fixed md:static inset-y-0 left-0 z-50
        w-64 glass-card border-r border-white/5 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
                {/* Logo - Hidden on mobile (shown in header) */}
                <div className="hidden md:block p-6 border-b border-white/5">
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

                {/* Mobile close button area */}
                <div className="md:hidden p-4 border-b border-white/5">
                    <p className="text-dark-400 text-sm">Navigation</p>
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
                                        onClick={closeSidebar}
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
                <div className="p-4 md:p-6">
                    {children}
                </div>
            </main>
        </div>
    );
}
