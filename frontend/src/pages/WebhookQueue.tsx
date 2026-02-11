import { useState, useEffect } from 'react';
import { AlertCircle, RefreshCw, Trash2, Archive, ChevronDown } from 'lucide-react';

interface QueueItem {
  id: number;
  webhook_type: string;
  status: string;
  retry_count: number;
  max_retries: number;
  error_message: string;
  last_error: string;
  last_retry_at: string | null;
  next_retry_at: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
}

interface QueueStats {
  pending: number;
  failed: number;
  processing: number;
  by_type: Record<string, number>;
}

export default function WebhookQueue() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [page, setPage] = useState(0);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: '50',
        offset: (page * 50).toString(),
      });
      if (filter) params.append('status', filter);
      if (typeFilter) params.append('webhook_type', typeFilter);

      const res = await fetch(`/api/webhook-queue/list?${params}`);
      const data = await res.json();
      if (data.success) {
        setItems(data.items);
      }
    } catch (error) {
      console.error('Failed to fetch queue:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/webhook-queue/stats');
      const data = await res.json();
      if (data.success) {
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchQueue();
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, [filter, typeFilter, page]);

  const handleRetry = async (id: number) => {
    try {
      const res = await fetch(`/api/webhook-queue/${id}/retry`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert('וובהוק הורץ בהצלחה');
      } else {
        alert(`כשל: ${data.error}`);
      }
      fetchQueue();
    } catch (error) {
      console.error('Retry failed:', error);
      alert('שגיאה בריצה מחדש');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק?')) return;
    try {
      const res = await fetch(`/api/webhook-queue/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        alert('נמחק בהצלחה');
        fetchQueue();
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('שגיאה במחיקה');
    }
  };

  const handleArchive = async (id: number) => {
    try {
      const res = await fetch(`/api/webhook-queue/${id}/archive`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert('הועבר לארכיון');
        fetchQueue();
      }
    } catch (error) {
      console.error('Archive failed:', error);
      alert('שגיאה בהעברה לארכיון');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'success': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'archived': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: 'ממתין',
      processing: 'בעיבוד',
      success: 'הצליח',
      failed: 'נכשל',
      archived: 'בארכיון',
    };
    return labels[status] || status;
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">תור וובהוקים כושלים</h1>
          <p className="text-gray-600">ניהול וובהוקים שנכשלו בעיבוד וריצה מחדש</p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">ממתינים</div>
              <div className="text-3xl font-bold text-yellow-600">{stats.pending}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">נכשלו</div>
              <div className="text-3xl font-bold text-red-600">{stats.failed}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">בעיבוד</div>
              <div className="text-3xl font-bold text-blue-600">{stats.processing}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">סוגים</div>
              <div className="text-3xl font-bold text-gray-600">
                {Object.keys(stats.by_type).length}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">סטטוס</label>
              <select
                value={filter}
                onChange={(e) => {
                  setFilter(e.target.value);
                  setPage(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">הכל</option>
                <option value="pending">ממתין</option>
                <option value="failed">נכשל</option>
                <option value="processing">בעיבוד</option>
                <option value="success">הצליח</option>
                <option value="archived">בארכיון</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">סוג וובהוק</label>
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value);
                  setPage(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">הכל</option>
                <option value="elementor">Elementor</option>
                <option value="yemot">Yemot</option>
                <option value="nedarim">Nedarim</option>
                <option value="generic">Generic</option>
                <option value="lesson-complete">Lesson Complete</option>
                <option value="kinyan-approval">Kinyan Approval</option>
                <option value="file-upload">File Upload</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  fetchQueue();
                  fetchStats();
                }}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <RefreshCw size={18} />
                רענן
              </button>
            </div>
          </div>
        </div>

        {/* Queue Items */}
        <div className="space-y-3">
          {items.length === 0 ? (
            <div className="bg-white p-8 rounded-lg shadow text-center">
              <AlertCircle size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">אין פריטים בתור</p>
            </div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow">
                <div
                  className="p-4 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                  onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <ChevronDown
                        size={20}
                        className={`transition-transform ${
                          expandedId === item.id ? 'rotate-180' : ''
                        }`}
                      />
                      <div>
                        <div className="font-medium text-gray-900">
                          {item.webhook_type}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {item.id} • {new Date(item.created_at).toLocaleString('he-IL')}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(item.status)}`}>
                      {getStatusLabel(item.status)}
                    </span>
                    <span className="text-sm text-gray-600">
                      {item.retry_count}/{item.max_retries}
                    </span>
                  </div>
                </div>

                {expandedId === item.id && (
                  <div className="border-t border-gray-200 p-4 bg-gray-50">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-sm font-medium text-gray-700 mb-1">הודעת שגיאה</div>
                        <div className="text-sm text-red-600 bg-white p-2 rounded border border-red-200">
                          {item.error_message || 'אין'}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-700 mb-1">שגיאה אחרונה</div>
                        <div className="text-sm text-gray-600 bg-white p-2 rounded border border-gray-200">
                          {item.last_error || 'אין'}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-700 mb-1">ריצה אחרונה</div>
                        <div className="text-sm text-gray-600">
                          {item.last_retry_at
                            ? new Date(item.last_retry_at).toLocaleString('he-IL')
                            : 'לא הורץ עדיין'}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-700 mb-1">ריצה הבאה</div>
                        <div className="text-sm text-gray-600">
                          {item.next_retry_at
                            ? new Date(item.next_retry_at).toLocaleString('he-IL')
                            : 'לא מתוכננת'}
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      {item.status !== 'success' && (
                        <button
                          onClick={() => handleRetry(item.id)}
                          className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
                        >
                          <RefreshCw size={18} />
                          הרץ מחדש
                        </button>
                      )}
                      {item.status !== 'archived' && (
                        <button
                          onClick={() => handleArchive(item.id)}
                          className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center justify-center gap-2"
                        >
                          <Archive size={18} />
                          ארכיון
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center gap-2"
                      >
                        <Trash2 size={18} />
                        מחק
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {items.length > 0 && (
          <div className="mt-6 flex justify-center gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
            >
              הקודם
            </button>
            <span className="px-4 py-2 text-gray-700">עמוד {page + 1}</span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={items.length < 50}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
            >
              הבא
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
