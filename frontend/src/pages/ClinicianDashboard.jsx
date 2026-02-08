import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCases } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Filter, Search, RefreshCw, ArrowRight } from 'lucide-react';

const urgencyConfig = {
  emergency: { label: 'Emergency', color: 'bg-red-100 text-red-800', dot: 'bg-red-500', ring: 'ring-red-200' },
  urgent: { label: 'Urgent', color: 'bg-amber-100 text-amber-800', dot: 'bg-amber-500', ring: 'ring-amber-200' },
  routine: { label: 'Routine', color: 'bg-green-100 text-green-800', dot: 'bg-green-500', ring: 'ring-green-200' },
  self_care: { label: 'Self-care', color: 'bg-blue-100 text-blue-800', dot: 'bg-blue-500', ring: 'ring-blue-200' },
};

const statusConfig = {
  new: { label: 'New', color: 'bg-blue-100 text-blue-800' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-800' },
  decided: { label: 'Decided', color: 'bg-purple-100 text-purple-800' },
  closed: { label: 'Closed', color: 'bg-gray-100 text-gray-800' },
};

export default function ClinicianDashboard() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [urgencyFilter, setUrgencyFilter] = useState('');
  const [search, setSearch] = useState('');

  const fetchCases = () => {
    setLoading(true);
    const params = {};
    if (statusFilter) params.status = statusFilter;
    if (urgencyFilter) params.urgency = urgencyFilter;
    getCases(params)
      .then(({ data }) => setCases(data.results || data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchCases(); }, [statusFilter, urgencyFilter]);

  const filteredCases = search
    ? cases.filter(c =>
        c.patient_name?.toLowerCase().includes(search.toLowerCase()) ||
        c.visit_type?.toLowerCase().includes(search.toLowerCase()) ||
        c.case_number?.toLowerCase().includes(search.toLowerCase())
      )
    : cases;

  const newCount = cases.filter(c => c.status === 'new').length;
  const basePath = user?.role === 'clinician' ? '/clinician' : '/admin';

  return (
    <div>
      {/* Header with counts */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patient Cases</h1>
          <p className="text-gray-500 text-sm">{cases.length} total cases</p>
        </div>
        <div className="flex items-center gap-3">
          {newCount > 0 && (
            <span className="flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm font-medium">
              <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs">{newCount}</span>
              Unhandled cases
            </span>
          )}
          <button onClick={fetchCases} className="p-2 rounded-lg hover:bg-gray-100 transition" title="Refresh">
            <RefreshCw className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Filters bar - mimicking Klinik */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex items-center gap-2 bg-white border rounded-lg px-3 py-2">
          <Search className="w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search..." className="outline-none text-sm w-40" />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white border rounded-lg px-3 py-2 text-sm">
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="in_progress">In Progress</option>
          <option value="decided">Decided</option>
          <option value="closed">Closed</option>
        </select>
        <select value={urgencyFilter} onChange={(e) => setUrgencyFilter(e.target.value)}
          className="bg-white border rounded-lg px-3 py-2 text-sm">
          <option value="">All urgencies</option>
          <option value="emergency">Emergency</option>
          <option value="urgent">Urgent</option>
          <option value="routine">Routine</option>
          <option value="self_care">Self-care</option>
        </select>
      </div>

      {/* Cases table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Arrived</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Patient</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Subject</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">AI Urgency</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : filteredCases.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No cases found</td></tr>
            ) : (
              filteredCases.map(c => {
                const urg = urgencyConfig[c.ai_urgency] || urgencyConfig.routine;
                const stat = statusConfig[c.status] || statusConfig.new;
                return (
                  <tr key={c.id} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(c.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'numeric', year: 'numeric' })}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{c.patient_name}</td>
                    <td className="px-4 py-3">
                      <Link to={`${basePath}/case/${c.id}`} className="text-sm text-emerald-600 hover:underline">
                        {c.visit_type}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${urg.color}`}>
                        {urg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${stat.color}`}>
                        {stat.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`${basePath}/case/${c.id}`}
                        className="text-emerald-600 hover:text-emerald-700">
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
