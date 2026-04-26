import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Home from './pages/Home';
import Review from './pages/Review';
import Reader from './pages/Reader';
import PocSession from './pages/PocSession';
import Home from './pages/Home'
import Review from './pages/Review'
import Reader from './pages/Reader'
import ResearchLanding from './pages/research/ResearchLanding'
import ResearchDeepDive from './pages/research/ResearchDeepDive'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/review" element={<Home />} />
        <Route path="/review/:jobId" element={<Review />} />
        <Route path="/read/:sessionId" element={<Reader />} />
        <Route path="/research" element={<ResearchLanding />} />
        <Route path="/research/:runId" element={<ResearchDeepDive />} />
        <Route path="/poc" element={<Home />} />
        <Route path="/poc/:sessionId" element={<PocSession />} />
      </Routes>
    </BrowserRouter>
  )
}
