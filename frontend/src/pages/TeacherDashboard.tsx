import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import { Sparkles, FileText, Clock, ChevronRight } from 'lucide-react'
import type { Paper } from '@/types'

export default function TeacherDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: papers = [] } = useQuery<Paper[]>({
    queryKey: ['papers'],
    queryFn: () => api.get('/papers').then((r) => r.data),
  })

  const recent = papers.slice(0, 5)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-700 text-navy">
          Good morning, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p className="text-slate-500 mt-1 text-sm">Ready to create a question paper?</p>
      </div>

      {/* Primary CTA */}
      <div className="card p-6 bg-gradient-to-br from-navy to-navy-700 border-0 mb-8">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-heading font-700 text-white mb-1">Generate a Paper</h2>
            <p className="text-white/60 text-sm mb-4">
              7 quick steps — select chapters, pick a template, done.
            </p>
            <button
              onClick={() => navigate('/generate')}
              className="inline-flex items-center gap-2 bg-amber text-white font-heading font-700 px-5 py-2.5 rounded-lg hover:bg-amber-600 transition-colors"
            >
              <Sparkles size={16} />
              Start Generating
            </button>
          </div>
          <div className="text-white/10 text-8xl font-heading font-800 leading-none -mt-2">Q</div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Papers Created', value: papers.length, icon: FileText },
          { label: 'This Month', value: papers.filter(p => new Date(p.created_at) > new Date(Date.now() - 30 * 86400000)).length, icon: Clock },
          { label: 'Finalised', value: papers.filter(p => p.status === 'final').length, icon: Sparkles },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="card p-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-amber-50 rounded-lg flex items-center justify-center">
                <Icon size={18} className="text-amber" />
              </div>
              <div>
                <div className="text-2xl font-heading font-700 text-navy">{value}</div>
                <div className="text-xs text-slate-500">{label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Papers */}
      {recent.length > 0 && (
        <div className="card">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-heading font-700 text-navy text-sm">Recent Papers</h3>
            <button
              onClick={() => navigate('/papers')}
              className="text-xs text-amber hover:underline flex items-center gap-1"
            >
              View all <ChevronRight size={12} />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {recent.map((paper) => (
              <div
                key={paper.id}
                className="px-5 py-3.5 flex items-center justify-between hover:bg-slate-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/papers/${paper.id}/review`)}
              >
                <div>
                  <div className="text-sm font-medium text-navy">{paper.title}</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Class {paper.class_}{paper.section ? ` ${paper.section}` : ''} · {paper.subject} · {paper.total_marks}M
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
                  <ChevronRight size={14} className="text-slate-300" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {papers.length === 0 && (
        <div className="card p-10 text-center">
          <FileText size={32} className="text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No papers yet. Generate your first paper above.</p>
        </div>
      )}
    </div>
  )
}
