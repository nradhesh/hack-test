import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import Assets from './pages/Assets';
import AssetDetail from './pages/AssetDetail';
import Wards from './pages/Wards';
import Simulator from './pages/Simulator';
import Admin from './pages/Admin';

function App() {
    return (
        <Router> 
            <Layout>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/map" element={<MapView />} />
                    <Route path="/assets" element={<Assets />} />
                    <Route path="/assets/:id" element={<AssetDetail />} />
                    <Route path="/wards" element={<Wards />} />
                    <Route path="/simulator" element={<Simulator />} />
                    <Route path="/admin" element={<Admin />} />
                </Routes>
            </Layout>
        </Router>
    );
}

export default App;
