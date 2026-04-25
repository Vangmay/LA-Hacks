import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-900">
      <h1 className="text-5xl font-bold mb-4">PaperCourt</h1>
      <p className="text-slate-600 mb-10">
        Adversarial review and reproducibility for research papers.
      </p>
      <div className="flex gap-4">
        <Link
          to="/review"
          className="px-6 py-3 rounded-lg bg-slate-900 text-white hover:bg-slate-700 transition"
        >
          Review a Paper
        </Link>
        <Link
          to="/poc"
          className="px-6 py-3 rounded-lg border border-slate-900 hover:bg-slate-100 transition"
        >
          Build a PoC
        </Link>
      </div>
    </div>
  )
}
