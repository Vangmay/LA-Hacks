import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/review" element={<Home />} />
        <Route path="/poc" element={<Home />} />
        <Route path="/review/:jobId" element={<div className="p-8">Review page (Person C builds this)</div>} />
        <Route path="/poc/:sessionId" element={<div className="p-8">PoC page (Person C builds this)</div>} />
      </Routes>
    </BrowserRouter>
  )
}
