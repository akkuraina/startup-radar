'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Company {
  id: number;
  company_name: string;
  amount_usd: number | null;
  round_type: string | null;
  investors: string[] | null;
  country: string | null;
  announcement_date: string | null;
  website_url: string | null;
  is_hiring: boolean;
  open_roles_count: number | null;
  job_titles: string[] | null;
  created_at: string;
}

interface Stats {
  total_companies: number;
  total_funding_usd: number;
  hiring_count: number;
  latest_announcement: string | null;
  by_round: Record<string, { count: number; total: number }>;
  by_country: Record<string, number>;
}

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  
  const [filters, setFilters] = useState({
    search: '',
    country: '',
    round: '',
    hiring: false,
  });
  
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 25,
  });

  // Fetch stats
  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/stats`);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  // Fetch companies
  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('skip', pagination.skip.toString());
      params.append('limit', pagination.limit.toString());
      
      if (filters.search) params.append('search', filters.search);
      if (filters.country) params.append('country', filters.country);
      if (filters.round) params.append('round_type', filters.round);
      if (filters.hiring) params.append('hiring_only', 'true');

      const res = await axios.get(`${API_BASE}/api/companies?${params}`);
      setCompanies(res.data);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    } finally {
      setLoading(false);
    }
  };

  // Run pipeline
  const runPipeline = async () => {
    try {
      setPipelineRunning(true);
      const res = await axios.post(`${API_BASE}/api/pipeline/run`);
      
      // Refresh data
      await fetchStats();
      await fetchCompanies();
      
      alert(`✅ Pipeline executed!\n- Articles found: ${res.data.articles_found}\n- Companies extracted: ${res.data.companies_extracted}\n- Inserted: ${res.data.inserted}\n- Updated: ${res.data.updated}`);
    } catch (err) {
      alert('❌ Failed to run pipeline: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setPipelineRunning(false);
    }
  };

  // Export CSV
  const exportCSV = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/export/csv`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'companies.csv');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      alert('Failed to export CSV');
    }
  };

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchCompanies();
  }, []);

  // Refetch when filters or pagination change
  useEffect(() => {
    fetchCompanies();
  }, [filters, pagination]);

  const rounds = stats ? Object.keys(stats.by_round) : [];
  const countries = stats ? Object.keys(stats.by_country) : [];

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">🚀 Startup Radar</h1>
          <p className="text-gray-600">Discover funded startups and hiring signals</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Total Companies</div>
              <div className="text-3xl font-bold text-blue-600">{stats.total_companies}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Total Funding</div>
              <div className="text-3xl font-bold text-green-600">
                ${(stats.total_funding_usd / 1e9).toFixed(2)}B
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Hiring Now</div>
              <div className="text-3xl font-bold text-purple-600">{stats.hiring_count}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Latest Announcement</div>
              <div className="text-lg font-bold text-gray-900">
                {stats.latest_announcement 
                  ? format(new Date(stats.latest_announcement), 'MMM dd, yyyy')
                  : 'N/A'
                }
              </div>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex flex-col gap-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search companies..."
                value={filters.search}
                onChange={(e) => {
                  setFilters({ ...filters, search: e.target.value });
                  setPagination({ ...pagination, skip: 0 });
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              
              <select
                value={filters.country}
                onChange={(e) => {
                  setFilters({ ...filters, country: e.target.value });
                  setPagination({ ...pagination, skip: 0 });
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Countries</option>
                {countries.map(country => (
                  <option key={country} value={country}>{country}</option>
                ))}
              </select>

              <select
                value={filters.round}
                onChange={(e) => {
                  setFilters({ ...filters, round: e.target.value });
                  setPagination({ ...pagination, skip: 0 });
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Rounds</option>
                {rounds.map(round => (
                  <option key={round} value={round}>{round}</option>
                ))}
              </select>

              <label className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={filters.hiring}
                  onChange={(e) => {
                    setFilters({ ...filters, hiring: e.target.checked });
                    setPagination({ ...pagination, skip: 0 });
                  }}
                />
                <span>Hiring</span>
              </label>
            </div>

            <div className="flex gap-4">
              <button
                onClick={runPipeline}
                disabled={pipelineRunning}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
              >
                {pipelineRunning ? '⏳ Running...' : '🔄 Run Pipeline'}
              </button>
              
              <button
                onClick={exportCSV}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              >
                📥 Export CSV
              </button>
            </div>
          </div>
        </div>

        {/* Companies Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Company</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Amount</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Round</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Country</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Hiring</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Links</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : companies.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    No companies found
                  </td>
                </tr>
              ) : (
                companies.map(company => (
                  <tr key={company.id} className="border-b hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{company.company_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {company.amount_usd ? `$${(company.amount_usd / 1e6).toFixed(1)}M` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {company.round_type && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                          {company.round_type}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{company.country || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {company.announcement_date 
                        ? format(new Date(company.announcement_date), 'MMM dd, yyyy')
                        : 'N/A'
                      }
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {company.is_hiring ? (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                          ✅ {company.open_roles_count || '?'} roles
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex gap-2">
                        {company.website_url && (
                          <a href={company.website_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            Web
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="px-6 py-4 border-t flex gap-4">
            <button
              onClick={() => setPagination({ ...pagination, skip: Math.max(0, pagination.skip - pagination.limit) })}
              disabled={pagination.skip === 0}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-50 disabled:text-gray-400"
            >
              ← Previous
            </button>
            
            <span className="py-2 text-sm text-gray-600">
              Showing {pagination.skip + 1} - {pagination.skip + companies.length} of {stats?.total_companies || 0}
            </span>
            
            <button
              onClick={() => setPagination({ ...pagination, skip: pagination.skip + pagination.limit })}
              disabled={companies.length < pagination.limit}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-50 disabled:text-gray-400"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
