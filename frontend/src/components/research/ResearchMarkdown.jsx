import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'

export default function ResearchMarkdown({ children, empty = 'No markdown yet.' }) {
  const content = children && String(children).trim() ? children : empty
  return (
    <div className="prose prose-invert prose-sm max-w-none prose-headings:font-semibold prose-headings:text-[#E4E7F0] prose-a:text-[#67E8F9] prose-strong:text-white prose-code:text-[#67E8F9] prose-pre:bg-[#0A0C10] prose-pre:border prose-pre:border-white/10 prose-pre:rounded-md prose-table:text-xs prose-th:border-white/10 prose-td:border-white/10">
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{content}</ReactMarkdown>
    </div>
  )
}
