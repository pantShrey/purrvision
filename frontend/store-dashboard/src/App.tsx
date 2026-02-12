import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { StoreDetails } from './pages/StoreDetails'; // Import the new page

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stores/:id" element={<StoreDetails />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;