import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { FileText, ChevronRight } from 'lucide-react'
import type { Paper } from '@/types'

export default function MyPapers() {
  const navigate = useNavigate()
  const { data: papers = [], isLoading } = useQuery<Paper[]>({
    queryKey: ['papers'],
    queryFn: () => api.get('/papers').then((r) => r.data),
  })

  if (isLoading) return <div className="p-8 text-slate-400 text-sm">Loading…</div>

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-heading font-700 text-navy">My Papers</h1>
          <p className="text-slate-500 text-sm mt-0.5">{papers.length} paper{papers.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => navigate('/generate')} className="btn-primary">
          + New Paper
        </button>
      </div>

      {papers.length === 0 ? (
        <div className="card p-10 text-center">
          <FileText size={32} className="text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No papers yet.</p>
          <button onClick={() => navigate('/generate')} className="btn-primary mt-4">Generate your first paper</button>
        </div>
      ) : (
        <div className="card divide-y divide-slate-100">
          {papers.map((paper) => (
            <div
              key={paper.id}
              className="px-5 py-4 flex items-center justify-between hover:bg-slate-50 cursor-pointer transition-colors"
              onClick={() => navigate(`/papers/${paper.id}/review`)}
            >
              <div>
                <div className="text-sm font-medium text-navy">{paper.title}</div>
                <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                  <span>Class {paper.class_}{paper.section ? ` ${paper.section}` : ''}</span>
                  <span>·</span>
                  <span>{paper.subject}</span>
                  <span>·</span>
                  <span>{paper.board}</span>
                  <span>·</span>
                  <span>{paper.total_marks}M</span>
                  <span>·</span>
                  <span>{new Date(paper.created_at).toLocaleDateString('en-IN')}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  paper.status === 'final'
                    ? 'bg-green-50 text-green-600'
                    : 'bg-slate-100 text-slate-500'
                }`}>
                  {paper.status}
                </span>
                <span className="text-xs text-slate-400 capitalize">{paper.generation_mode}</span>
                <ChevronRight size={14} className="text-slate-300" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
