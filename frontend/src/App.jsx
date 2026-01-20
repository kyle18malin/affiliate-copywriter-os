import { useState, useEffect } from 'react'
import { 
  Zap, Newspaper, FileText, Sparkles, TrendingUp, 
  Settings, ChevronRight, Plus, RefreshCw, Star,
  Copy, ExternalLink, Loader2, Check, Rss
} from 'lucide-react'

const API_BASE = '/api'

// API helper
async function api(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// Tab components
function Dashboard({ stats, onRefresh }) {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-electric/20 via-obsidian to-obsidian p-8 border border-electric/20">
        <div className="absolute top-0 right-0 w-96 h-96 bg-electric/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative">
          <h1 className="text-4xl font-display font-bold gradient-text mb-3">
            Affiliate Copywriter OS
          </h1>
          <p className="text-slate-400 text-lg max-w-xl">
            AI-powered hook generation combining trending news with proven ad patterns.
            Generate scroll-stopping copy for your affiliate campaigns.
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'RSS Feeds', value: stats.feeds, icon: Rss, color: 'electric' },
          { label: 'News Articles', value: stats.articles, icon: Newspaper, color: 'neon-amber' },
          { label: 'Winning Ads', value: stats.ads, icon: FileText, color: 'neon-green' },
          { label: 'Hooks Generated', value: stats.hooks_generated, icon: Sparkles, color: 'neon-rose' },
        ].map((stat, i) => (
          <div 
            key={i}
            className="glass rounded-xl p-5 hover:border-electric/30 transition-all group"
          >
            <stat.icon className={`w-5 h-5 mb-3 text-${stat.color}`} />
            <div className="text-3xl font-display font-bold text-white mb-1">
              {stat.value || 0}
            </div>
            <div className="text-sm text-slate-500">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-4">
        <QuickAction
          icon={RefreshCw}
          title="Fetch Latest News"
          description="Pull articles from all RSS feeds"
          onClick={onRefresh}
        />
        <QuickAction
          icon={Plus}
          title="Upload Winning Ad"
          description="Add an ad to your swipe file"
          href="#ads"
        />
        <QuickAction
          icon={Sparkles}
          title="Generate Hooks"
          description="Create AI-powered ad hooks"
          href="#generate"
        />
      </div>
    </div>
  )
}

function QuickAction({ icon: Icon, title, description, onClick, href }) {
  const content = (
    <div className="glass rounded-xl p-5 hover:border-electric/40 hover:glow-electric transition-all cursor-pointer group">
      <div className="flex items-start justify-between">
        <div>
          <Icon className="w-6 h-6 text-electric mb-3" />
          <h3 className="font-semibold text-white mb-1">{title}</h3>
          <p className="text-sm text-slate-500">{description}</p>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-electric transition-colors" />
      </div>
    </div>
  )

  if (onClick) {
    return <button onClick={onClick} className="text-left w-full">{content}</button>
  }
  return <a href={href} className="block">{content}</a>
}

function NewsPanel({ articles, onAnalyze, analyzing }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-display font-bold">News Feed</h2>
        <span className="text-sm text-slate-500">{articles.length} articles</span>
      </div>

      <div className="space-y-3">
        {articles.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <Newspaper className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500">No articles yet. Click "Fetch Latest News" to get started.</p>
          </div>
        ) : (
          articles.map((article) => (
            <div key={article.id} className="glass rounded-xl p-4 hover:border-electric/30 transition-all">
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <a 
                    href={article.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="font-medium text-white hover:text-electric transition-colors line-clamp-2"
                  >
                    {article.title}
                  </a>
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                    <span>{article.feed_name}</span>
                    {article.trending_angles && (
                      <span className="px-2 py-0.5 rounded-full bg-neon-green/20 text-neon-green">
                        Analyzed
                      </span>
                    )}
                  </div>
                  {article.trending_angles && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {article.trending_angles.slice(0, 3).map((angle, i) => (
                        <span key={i} className="text-xs px-2 py-1 rounded-lg bg-electric/10 text-electric-light">
                          {angle}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onAnalyze(article.id)}
                  disabled={analyzing === article.id}
                  className="px-3 py-1.5 text-sm rounded-lg bg-electric/10 text-electric hover:bg-electric/20 transition-colors disabled:opacity-50"
                >
                  {analyzing === article.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : article.trending_angles ? (
                    'Re-analyze'
                  ) : (
                    'Analyze'
                  )}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function AdsPanel({ ads, niches, onUpload, onAnalyze, analyzing }) {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ content: '', title: '', niche_id: '', source: '', performance_notes: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onUpload(form)
    setForm({ content: '', title: '', niche_id: '', source: '', performance_notes: '' })
    setShowForm(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-display font-bold">Ad Library</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-electric text-white hover:bg-electric-light transition-colors"
        >
          <Plus className="w-4 h-4" />
          Upload Ad
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Ad Copy *</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              className="w-full h-40 px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none resize-none"
              placeholder="Paste your winning ad copy here..."
              required
            />
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Title</label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
                placeholder="e.g., High CTR Insurance Ad"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Niche (optional)</label>
              <select
                value={form.niche_id}
                onChange={(e) => setForm({ ...form, niche_id: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
              >
                <option value="">Universal (all niches)</option>
                {niches.map((n) => (
                  <option key={n.id} value={n.id}>{n.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Why is this a winner?</label>
            <input
              type="text"
              value={form.performance_notes}
              onChange={(e) => setForm({ ...form, performance_notes: e.target.value })}
              className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
              placeholder="e.g., 2.5% CTR, 15% conversion rate"
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 rounded-lg bg-electric text-white font-medium hover:bg-electric-light transition-colors"
          >
            Save Ad
          </button>
        </form>
      )}

      <div className="space-y-3">
        {ads.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500">No ads yet. Upload your first winning ad to get started.</p>
          </div>
        ) : (
          ads.map((ad) => (
            <div key={ad.id} className="glass rounded-xl p-5 hover:border-electric/30 transition-all">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="font-medium text-white">{ad.title || 'Untitled Ad'}</h3>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                    {ad.niche_name && (
                      <span className="px-2 py-0.5 rounded-full bg-electric/20 text-electric-light">
                        {ad.niche_name}
                      </span>
                    )}
                    {ad.patterns && (
                      <span className="px-2 py-0.5 rounded-full bg-neon-green/20 text-neon-green">
                        Patterns Extracted
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => onAnalyze(ad.id)}
                  disabled={analyzing === ad.id}
                  className="px-3 py-1.5 text-sm rounded-lg bg-neon-amber/10 text-neon-amber hover:bg-neon-amber/20 transition-colors disabled:opacity-50"
                >
                  {analyzing === ad.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : ad.patterns ? (
                    'Re-analyze'
                  ) : (
                    'Extract Patterns'
                  )}
                </button>
              </div>
              <p className="text-sm text-slate-400 whitespace-pre-wrap line-clamp-4">{ad.content}</p>
              {ad.patterns && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <div className="text-xs text-slate-500 mb-2">Extracted Patterns:</div>
                  <div className="flex flex-wrap gap-2">
                    {ad.patterns.emotional_triggers?.slice(0, 5).map((t, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded bg-neon-rose/10 text-neon-rose">
                        {t}
                      </span>
                    ))}
                    {ad.patterns.power_words?.slice(0, 5).map((w, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded bg-neon-green/10 text-neon-green">
                        {w}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function GeneratePanel({ niches, onGenerate, generating }) {
  const [selectedNiche, setSelectedNiche] = useState('')
  const [numHooks, setNumHooks] = useState(5)
  const [hookStyle, setHookStyle] = useState('')
  const [hooks, setHooks] = useState([])
  const [copied, setCopied] = useState(null)

  const handleGenerate = async () => {
    if (!selectedNiche) return
    const result = await onGenerate(selectedNiche, numHooks, hookStyle)
    if (result?.hooks) {
      setHooks(result.hooks)
    }
  }

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-display font-bold mb-2">Generate Hooks</h2>
        <p className="text-slate-500">AI-powered hook generation combining your winning ads with trending news.</p>
      </div>

      <div className="glass rounded-xl p-6">
        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Niche *</label>
            <select
              value={selectedNiche}
              onChange={(e) => setSelectedNiche(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
            >
              <option value="">Select a niche</option>
              {niches.map((n) => (
                <option key={n.id} value={n.id}>{n.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Number of Hooks</label>
            <select
              value={numHooks}
              onChange={(e) => setNumHooks(parseInt(e.target.value))}
              className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
            >
              {[3, 5, 10, 15, 20].map((n) => (
                <option key={n} value={n}>{n} hooks</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Hook Style (optional)</label>
            <select
              value={hookStyle}
              onChange={(e) => setHookStyle(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
            >
              <option value="">Any style</option>
              <option value="question">Questions</option>
              <option value="shocking stat">Shocking Stats</option>
              <option value="story">Story Hooks</option>
              <option value="curiosity">Curiosity Gaps</option>
              <option value="fear">Fear/Urgency</option>
              <option value="benefit">Benefit-Led</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleGenerate}
          disabled={!selectedNiche || generating}
          className="w-full py-3 rounded-lg bg-gradient-to-r from-electric to-electric-light text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {generating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Generate Hooks
            </>
          )}
        </button>
      </div>

      {hooks.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Generated Hooks</h3>
          {hooks.map((hook, i) => (
            <div key={i} className="glass rounded-xl p-5 hover:border-electric/30 transition-all group">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-electric/20 text-electric flex items-center justify-center font-mono text-sm">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <p className="text-white text-lg leading-relaxed">{hook.hook_text}</p>
                  <div className="flex items-center gap-3 mt-3">
                    <span className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400">
                      {hook.hook_type}
                    </span>
                    <span className="text-xs px-2 py-1 rounded bg-neon-rose/10 text-neon-rose">
                      {hook.emotional_trigger}
                    </span>
                  </div>
                  {hook.inspiration && (
                    <p className="text-xs text-slate-500 mt-2">
                      <span className="text-slate-600">Inspiration:</span> {hook.inspiration}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => copyToClipboard(hook.hook_text, i)}
                  className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  {copied === i ? (
                    <Check className="w-5 h-5 text-neon-green" />
                  ) : (
                    <Copy className="w-5 h-5 text-slate-500" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function FeedsPanel({ feeds, onAdd }) {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', url: '', category: 'General' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onAdd(form)
    setForm({ name: '', url: '', category: 'General' })
    setShowForm(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-display font-bold">RSS Feeds</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-electric text-white hover:bg-electric-light transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Feed
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Feed Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
                placeholder="e.g., TechCrunch"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">RSS URL *</label>
              <input
                type="url"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
                placeholder="https://..."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Category</label>
              <input
                type="text"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-midnight border border-slate-800 text-white focus:border-electric focus:outline-none"
                placeholder="e.g., Tech, Finance"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-6 py-2 rounded-lg bg-electric text-white font-medium hover:bg-electric-light transition-colors"
          >
            Add Feed
          </button>
        </form>
      )}

      <div className="grid md:grid-cols-2 gap-3">
        {feeds.map((feed) => (
          <div key={feed.id} className="glass rounded-xl p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-neon-amber/20 text-neon-amber flex items-center justify-center">
              <Rss className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-white truncate">{feed.name}</h3>
              <p className="text-xs text-slate-500 truncate">{feed.url}</p>
            </div>
            <span className={`px-2 py-1 text-xs rounded-full ${feed.is_active ? 'bg-neon-green/20 text-neon-green' : 'bg-slate-800 text-slate-500'}`}>
              {feed.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Main App
export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [stats, setStats] = useState({ feeds: 0, articles: 0, ads: 0, patterns: 0, hooks_generated: 0 })
  const [niches, setNiches] = useState([])
  const [articles, setArticles] = useState([])
  const [ads, setAds] = useState([])
  const [feeds, setFeeds] = useState([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(null)
  const [generating, setGenerating] = useState(false)

  // Load data
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statsData, nichesData, articlesData, adsData, feedsData] = await Promise.all([
        api('/stats'),
        api('/niches'),
        api('/news?limit=30'),
        api('/ads'),
        api('/feeds')
      ])
      setStats(statsData)
      setNiches(nichesData)
      setArticles(articlesData)
      setAds(adsData)
      setFeeds(feedsData)
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchNews = async () => {
    try {
      await api('/feeds/fetch', { method: 'POST' })
      loadData()
    } catch (err) {
      console.error('Failed to fetch news:', err)
    }
  }

  const analyzeArticle = async (id) => {
    setAnalyzing(id)
    try {
      await api(`/news/${id}/analyze`, { method: 'POST' })
      loadData()
    } catch (err) {
      console.error('Failed to analyze:', err)
    } finally {
      setAnalyzing(null)
    }
  }

  const uploadAd = async (data) => {
    try {
      await api('/ads', { method: 'POST', body: JSON.stringify(data) })
      loadData()
    } catch (err) {
      console.error('Failed to upload ad:', err)
    }
  }

  const analyzeAd = async (id) => {
    setAnalyzing(id)
    try {
      await api(`/ads/${id}/analyze`, { method: 'POST' })
      loadData()
    } catch (err) {
      console.error('Failed to analyze ad:', err)
    } finally {
      setAnalyzing(null)
    }
  }

  const addFeed = async (data) => {
    try {
      await api('/feeds', { method: 'POST', body: JSON.stringify(data) })
      loadData()
    } catch (err) {
      console.error('Failed to add feed:', err)
    }
  }

  const generateHooks = async (nicheId, numHooks, hookStyle) => {
    setGenerating(true)
    try {
      const result = await api('/generate/hooks', {
        method: 'POST',
        body: JSON.stringify({
          niche_id: parseInt(nicheId),
          num_hooks: numHooks,
          hook_style: hookStyle || null
        })
      })
      loadData()
      return result
    } catch (err) {
      console.error('Failed to generate hooks:', err)
      return null
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-electric animate-spin" />
      </div>
    )
  }

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
    { id: 'generate', label: 'Generate', icon: Sparkles },
    { id: 'news', label: 'News', icon: Newspaper },
    { id: 'ads', label: 'Ads', icon: FileText },
    { id: 'feeds', label: 'Feeds', icon: Rss },
  ]

  return (
    <div className="min-h-screen pattern-grid">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 glass border-r border-slate-800/50 p-4 flex flex-col">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-electric to-electric-light flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-display font-bold text-white">CopywriterOS</h1>
            <p className="text-xs text-slate-500">Affiliate Edition</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all ${
                tab === t.id
                  ? 'bg-electric/20 text-electric'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
              }`}
            >
              <t.icon className="w-5 h-5" />
              <span className="font-medium">{t.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto pt-4 border-t border-slate-800">
          <div className="px-4 py-3">
            <p className="text-xs text-slate-500 mb-2">Active Niches</p>
            <div className="flex flex-wrap gap-1">
              {niches.map((n) => (
                <span key={n.id} className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400">
                  {n.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 p-8">
        <div className="max-w-5xl mx-auto">
          {tab === 'dashboard' && <Dashboard stats={stats} onRefresh={fetchNews} />}
          {tab === 'generate' && <GeneratePanel niches={niches} onGenerate={generateHooks} generating={generating} />}
          {tab === 'news' && <NewsPanel articles={articles} onAnalyze={analyzeArticle} analyzing={analyzing} />}
          {tab === 'ads' && <AdsPanel ads={ads} niches={niches} onUpload={uploadAd} onAnalyze={analyzeAd} analyzing={analyzing} />}
          {tab === 'feeds' && <FeedsPanel feeds={feeds} onAdd={addFeed} />}
        </div>
      </main>
    </div>
  )
}
