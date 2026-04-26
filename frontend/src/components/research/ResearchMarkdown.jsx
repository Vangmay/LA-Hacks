import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'

const markdownComponents = {
  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
  table: ({ node, ...props }) => (
    <div className="my-4 overflow-x-auto">
      <table {...props} />
    </div>
  ),
}

export default function ResearchMarkdown({ children, empty = 'No markdown yet.' }) {
  const content = children && String(children).trim() ? children : empty
  return (
    <div className="research-markdown prose prose-invert prose-sm max-w-none prose-headings:font-semibold prose-headings:text-[#E4E7F0] prose-a:text-[#67E8F9] prose-strong:text-white prose-code:break-words prose-code:text-[#67E8F9] prose-pre:overflow-x-auto prose-pre:rounded-md prose-pre:border prose-pre:border-white/10 prose-pre:bg-[#0A0C10] prose-pre:whitespace-pre-wrap prose-table:text-xs prose-th:border-white/10 prose-td:border-white/10">
      <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm, remarkBreaks]}>{content}</ReactMarkdown>
    </div>
  )
}
