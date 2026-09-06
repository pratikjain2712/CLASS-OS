import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { Users, Building2, CreditCard, FileSpreadsheet } from 'lucide-react'

export default function InstituteAdmin() {
  const { user } = useAuth()
  const navigate = useNavigate()

  if (!user || user.role === 'teacher') {
    return <div className="p-8 text-slate-400 text-sm">Access denied.</div>
  }

  const cards = [
    { label: 'Teachers', icon: Users, desc: 'Manage teacher accounts', onClick: undefined },
    { label: 'Branches', icon: Building2, desc: 'Manage branches', onClick: undefined },
    { label: 'Credits', icon: CreditCard, desc: 'View credit balance', onClick: undefined },
    { label: 'Import Questions', icon: FileSpreadsheet, desc: 'Bulk upload via Excel', onClick: () => navigate('/admin/questions') },
  ]

  return (
    <div className="p-8">
      <h1 className="text-xl font-heading font-700 text-navy mb-6">Institute Admin</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {cards.map(({ label, icon: Icon, desc, onClick }) => (
          <div
            key={label}
            className={`card p-5 transition-shadow ${onClick ? 'cursor-pointer hover:shadow-md' : 'opacity-60 cursor-default'}`}
            onClick={onClick}
          >
            <div className="w-10 h-10 bg-navy-50 rounded-lg flex items-center justify-center mb-3">
              <Icon size={20} className="text-navy" />
            </div>
            <div className="font-heading font-700 text-navy text-sm">{label}</div>
            <div className="text-xs text-slate-400 mt-0.5">{desc}</div>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <p className="text-sm text-slate-500">
          Teacher management, subscription management, and credit purchase are coming in the next build.
        </p>
      </div>
    </div>
  )
}
