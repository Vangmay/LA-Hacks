import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Review from './pages/Review'
import PoCPage from './pages/PoCPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/review" element={<Home />} />
        <Route path="/poc" element={<Home />} />
        <Route path="/review/:jobId" element={<Review />} />
        <Route path="/poc/:sessionId" element={<PoCPage />} />
      </Routes>
    </BrowserRouter>
  )
}
