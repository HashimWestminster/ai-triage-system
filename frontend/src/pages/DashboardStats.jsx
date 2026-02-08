import { useState, useEffect } from 'react';
import { getDashboardStats } from '../services/api';
import { Activity, Clock, CheckCircle, AlertTriangle, BarChart3 } from 'lucide-react';

export default function DashboardStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then(({ data }) => setStats(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-12 text-gray-500">Loading dashboard...</div>;
  if (!stats) return <div className="text-center py-12 text-gray-500">No data available</div>;

  const cards = [
    { label: 'Total Cases', value: stats.total_cases, icon: <BarChart3 className="w-6 h-6" />, color: 'bg-blue-500' },
    { label: 'New (Unhandled)', value: stats.new_cases, icon: <Clock className="w-6 h-6" />, color: 'bg-amber-500' },
    { label: 'In Progress', value: stats.in_progress, icon: <Activity className="w-6 h-6" />, color: 'bg-purple-500' },
    { label: 'Closed Today', value: stats.closed, icon: <CheckCircle className="w-6 h-6" />, color: 'bg-green-500' },
  ];

  const urgencyBars = [
    { label: 'Emergency', count: stats.urgency_breakdown.emergency, color: 'bg-red-500' },
    { label: 'Urgent', count: stats.urgency_breakdown.urgent, color: 'bg-amber-500' },
    { label: 'Routine', count: stats.urgency_breakdown.routine, color: 'bg-green-500' },
    { label: 'Self-care', count: stats.urgency_breakdown.self_care, color: 'bg-blue-500' },
  ];

  const totalUrgency = Object.values(stats.urgency_breakdown).reduce((a, b) => a + b, 0) || 1;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {cards.map((card) => (
          <div key={card.label} className="bg-white rounded-xl shadow-sm border p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-500">{card.label}</span>
              <span className={`${card.color} text-white p-2 rounded-lg`}>{card.icon}</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">{card.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Urgency breakdown */}
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Urgency Breakdown</h2>
          <div className="space-y-3">
            {urgencyBars.map((bar) => (
              <div key={bar.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{bar.label}</span>
                  <span className="font-medium">{bar.count} ({Math.round(bar.count / totalUrgency * 100)}%)</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full">
                  <div className={`h-3 rounded-full ${bar.color} transition-all`}
                    style={{ width: `${(bar.count / totalUrgency) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Agreement */}
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="font-semibold text-gray-900 mb-4">AI Performance</h2>
          <div className="text-center py-6">
            <div className="text-5xl font-bold text-emerald-600 mb-2">
              {stats.ai_agreement_rate !== null ? `${stats.ai_agreement_rate}%` : 'N/A'}
            </div>
            <p className="text-gray-500">Clinician-AI agreement rate</p>
            <p className="text-xs text-gray-400 mt-2">
              Percentage of cases where clinician agreed with AI suggestion
            </p>
          </div>

          <div className="border-t pt-4 mt-4">
            <div className="text-sm text-gray-600 space-y-2">
              <div className="flex justify-between">
                <span>Cases today</span>
                <span className="font-medium">{stats.today_cases}</span>
              </div>
              <div className="flex justify-between">
                <span>Decided cases</span>
                <span className="font-medium">{stats.decided}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
