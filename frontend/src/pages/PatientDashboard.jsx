import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMyCases, getSurgeryStatus } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Plus, Clock, AlertCircle } from 'lucide-react';

const urgencyConfig = {
  emergency: { label: 'Emergency', color: 'bg-red-50 text-red-700 ring-1 ring-red-200', dot: 'bg-red-500' },
  urgent: { label: 'Urgent', color: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200', dot: 'bg-amber-500' },
  routine: { label: 'Routine', color: 'bg-green-50 text-green-700 ring-1 ring-green-200', dot: 'bg-green-500' },
  self_care: { label: 'Self-care', color: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200', dot: 'bg-blue-500' },
};

const statusConfig = {
  new: { label: 'Submitted', color: 'text-blue-600' },
  in_progress: { label: 'In Review', color: 'text-amber-600' },
  decided: { label: 'Decided', color: 'text-purple-600' },
  closed: { label: 'Closed', color: 'text-gray-500' },
};

export default function PatientDashboard() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [surgeryOpen, setSurgeryOpen] = useState(null);

  useEffect(() => {
    getMyCases()
      .then(({ data }) => setCases(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));

    getSurgeryStatus()
      .then(({ data }) => setSurgeryOpen(data))
      .catch(() => setSurgeryOpen({ is_open: true }));
  }, []);

  const isOpen = surgeryOpen?.is_open;

  return (
    <div>
      {/* Welcome */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Welcome back, {user?.first_name || user?.username}
        </h1>
        <p className="text-gray-500 text-sm">Manage your triage cases below.</p>
      </div>

      {/* Surgery status banner */}
      {surgeryOpen && !surgeryOpen.not_configured && (
        <div className={`flex items-center gap-3 px-5 py-3.5 rounded-xl mb-4 text-sm ${
          isOpen
            ? 'bg-green-50 border border-green-200 text-green-700'
            : 'bg-amber-50 border border-amber-200 text-amber-700'
        }`}>
          {isOpen ? (
            <>
              <Clock className="w-4 h-4 shrink-0" />
              <span>The surgery is <strong>open</strong> today ({surgeryOpen.day}) &mdash; {surgeryOpen.open_time} to {surgeryOpen.close_time}. You can submit a new case.</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>
                The surgery is <strong>currently closed</strong>
                {surgeryOpen.is_closed_today
                  ? ` on ${surgeryOpen.day}s`
                  : ` (opens ${surgeryOpen.open_time || 'tomorrow'})`
                }. You cannot submit cases right now.
                {' '}For emergencies, call <strong>999</strong> or go to A&amp;E.
              </span>
            </>
          )}
        </div>
      )}

      {/* Submit new case button */}
      {isOpen !== false ? (
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
      ) : (
        <div className="flex items-center gap-3 bg-gray-100 text-gray-400 px-6 py-4 rounded-xl mb-6 cursor-not-allowed">
          <Plus className="w-6 h-6" />
          <div>
            <div className="font-semibold">Submit New Case</div>
            <div className="text-sm">Unavailable outside surgery hours</div>
          </div>
        </div>
      )}

      {/* Cases list */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Your Cases</h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading cases...</div>
        ) : cases.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <p className="font-medium">No cases submitted yet.</p>
            <p className="text-sm mt-1">Click "Submit New Case" to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {cases.map((c) => {
              const urg = urgencyConfig[c.ai_urgency] || urgencyConfig.routine;
              const stat = statusConfig[c.status] || statusConfig.new;
              return (
                <Link
                  key={c.id}
                  to={`/patient/case/${c.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50/50 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-2.5 h-2.5 rounded-full ${urg.dot}`} />
                    <div>
                      <div className="font-medium text-gray-900 text-sm">{c.visit_type}</div>
                      <div className="text-xs text-gray-500">
                        {c.body_location && `${c.body_location} · `}
                        {new Date(c.created_at).toLocaleDateString('en-GB')}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
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
