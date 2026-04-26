import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Home from './pages/Home';
import Review from './pages/Review';
import Reader from './pages/Reader';
import PocSession from './pages/PocSession';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/review" element={<Home />} />
        <Route path="/review/:jobId" element={<Review />} />
        <Route path="/read/:sessionId" element={<Reader />} />
        <Route path="/poc" element={<Home />} />
        <Route path="/poc/:sessionId" element={<PocSession />} />
      </Routes>
    </BrowserRouter>
  )
}
