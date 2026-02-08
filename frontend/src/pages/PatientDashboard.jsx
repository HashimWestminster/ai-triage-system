import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMyCases } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Plus, Clock, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';

const urgencyConfig = {
  emergency: { label: 'Emergency', color: 'bg-red-100 text-red-800', dot: 'bg-red-500' },
  urgent: { label: 'Urgent', color: 'bg-amber-100 text-amber-800', dot: 'bg-amber-500' },
  routine: { label: 'Routine', color: 'bg-green-100 text-green-800', dot: 'bg-green-500' },
  self_care: { label: 'Self-care', color: 'bg-blue-100 text-blue-800', dot: 'bg-blue-500' },
};

const statusConfig = {
  new: { label: 'New', color: 'text-blue-600' },
  in_progress: { label: 'In Progress', color: 'text-amber-600' },
  decided: { label: 'Decided', color: 'text-purple-600' },
  closed: { label: 'Closed', color: 'text-gray-600' },
};

export default function PatientDashboard() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyCases()
      .then(({ data }) => setCases(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* Welcome banner */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Welcome, {user?.first_name || user?.username}
        </h1>
        <p className="text-gray-500">Manage your triage cases below</p>
      </div>

      {/* Quick action */}
      <Link
        to="/patient/submit"
        className="flex items-center gap-3 bg-emerald-600 text-white px-6 py-4 rounded-xl mb-6 hover:bg-emerald-700 transition shadow-sm"
      >
        <Plus className="w-6 h-6" />
        <div>
          <div className="font-semibold">Submit New Case</div>
          <div className="text-emerald-100 text-sm">Tell us about your symptoms</div>
        </div>
      </Link>

      {/* Cases list */}
      <div className="bg-white rounded-xl shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h2 className="font-semibold text-gray-900">Your Cases</h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading cases...</div>
        ) : cases.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <ClipboardList className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No cases submitted yet.</p>
            <p className="text-sm">Click "Submit New Case" to get started.</p>
          </div>
        ) : (
          <div className="divide-y">
            {cases.map((c) => {
              const urg = urgencyConfig[c.ai_urgency] || urgencyConfig.routine;
              const stat = statusConfig[c.status] || statusConfig.new;
              return (
                <Link
                  key={c.id}
                  to={`/patient/case/${c.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full ${urg.dot}`} />
                    <div>
                      <div className="font-medium text-gray-900">{c.visit_type}</div>
                      <div className="text-sm text-gray-500">
                        {c.body_location && `${c.body_location} · `}
                        {new Date(c.created_at).toLocaleDateString('en-GB')}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${urg.color}`}>
                      {urg.label}
                    </span>
                    <span className={`text-xs font-medium ${stat.color}`}>
                      {stat.label}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function ClipboardList(props) {
  return <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>;
}
