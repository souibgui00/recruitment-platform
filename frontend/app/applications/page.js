'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import api from '../../lib/api';
import { 
  Send, 
  Check, 
  X, 
  Settings, 
  Info, 
  AlertTriangle, 
  Loader2, 
  Clock, 
  FileText, 
  User, 
  ExternalLink,
  Camera,
  Terminal,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Copy
} from 'lucide-react';

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [settings, setSettings] = useState({ auto_apply_enabled: false });
  const [loading, setLoading] = useState(true);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('ALL');
  
  // Storing rejection prompts locally for each application
  const [rejectionReasons, setRejectionReasons] = useState({});
  const [showRejectForm, setShowRejectForm] = useState({});
  
  // Toggle proof details accordion per card
  const [expandedProofs, setExpandedProofs] = useState({});
  const [activeProofTab, setActiveProofTab] = useState({});
  const [copiedAppId, setCopiedAppId] = useState(null);
  
  // Loading state per action
  const [actionLoading, setActionLoading] = useState({});

  useEffect(() => {
    async function fetchData() {
      try {
        const [appsRes, settingsRes] = await Promise.all([
          api.get('/applications'),
          api.get('/applications/settings')
        ]);
        setApplications(appsRes.data);
        setSettings(settingsRes.data);
      } catch (err) {
        console.error(err);
        setError("Erreur de chargement des données. Veuillez réessayer.");
      } finally {
        setLoading(false);
        setSettingsLoading(false);
      }
    }
    fetchData();
  }, []);

  // Poll for status updates if any application is processing (status === 'APPROVED')
  useEffect(() => {
    const hasProcessingApps = applications.some(app => app.status === 'APPROVED');
    if (!hasProcessingApps) return;

    const interval = setInterval(async () => {
      try {
        const response = await api.get('/applications');
        setApplications(response.data);
      } catch (err) {
        console.error("Failed to poll applications:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [applications]);

  const handleToggleAutoApply = async () => {
    setSettingsLoading(true);
    const newValue = !settings.auto_apply_enabled;
    try {
      const response = await api.put('/applications/settings', {
        auto_apply_enabled: newValue
      });
      setSettings(response.data);
    } catch (err) {
      console.error(err);
      alert("Impossible de mettre à jour les paramètres d'auto-apply.");
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleApprove = async (appId) => {
    setActionLoading(prev => ({ ...prev, [appId]: 'approve' }));
    try {
      const response = await api.post(`/applications/${appId}/approve`);
      setApplications(apps => apps.map(a => a.id === appId ? response.data : a));
      // Auto-expand proof accordion so user sees screenshots & logs immediately!
      setExpandedProofs(prev => ({ ...prev, [appId]: true }));
      setActiveProofTab(prev => ({ ...prev, [appId]: 'screenshots' }));
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "Une erreur est survenue lors de l'exécution de l'agent web.";
      alert(errMsg);
    } finally {
      setActionLoading(prev => ({ ...prev, [appId]: null }));
    }
  };

  const handleRunAgent = async (appId) => {
    setActionLoading(prev => ({ ...prev, [appId]: 'run_agent' }));
    try {
      const response = await api.post(`/applications/${appId}/run-agent`);
      setApplications(apps => apps.map(a => a.id === appId ? response.data : a));
      setExpandedProofs(prev => ({ ...prev, [appId]: true }));
      setActiveProofTab(prev => ({ ...prev, [appId]: 'screenshots' }));
    } catch (err) {
      console.error(err);
      alert("Une erreur est survenue lors de l'exécution de l'agent web.");
    } finally {
      setActionLoading(prev => ({ ...prev, [appId]: null }));
    }
  };

  const handleReject = async (appId) => {
    const reason = rejectionReasons[appId] || '';
    setActionLoading(prev => ({ ...prev, [appId]: 'reject' }));
    try {
      const response = await api.post(`/applications/${appId}/reject`, {
        reason: reason.trim() || null
      });
      setApplications(apps => apps.map(a => a.id === appId ? response.data : a));
      setShowRejectForm(prev => ({ ...prev, [appId]: false }));
      setRejectionReasons(prev => ({ ...prev, [appId]: '' }));
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "Une erreur est survenue lors du rejet.";
      alert(errMsg);
    } finally {
      setActionLoading(prev => ({ ...prev, [appId]: null }));
    }
  };

  const toggleProofAccordion = (appId) => {
    setExpandedProofs(prev => ({ ...prev, [appId]: !prev[appId] }));
    if (!activeProofTab[appId]) {
      setActiveProofTab(prev => ({ ...prev, [appId]: 'screenshots' }));
    }
  };

  const handleCopyCoverLetter = (text, appId) => {
    navigator.clipboard.writeText(text);
    setCopiedAppId(appId);
    setTimeout(() => setCopiedAppId(null), 2000);
  };

  const filteredApps = applications.filter(app => {
    if (activeTab === 'ALL') return true;
    return app.status === activeTab;
  });

  const getStatusBadgeStyles = (status) => {
    switch (status) {
      case 'PENDING_VALIDATION':
        return { bg: 'rgba(245, 158, 11, 0.1)', text: 'var(--warning)', label: 'En attente' };
      case 'APPROVED':
        return { bg: 'rgba(108, 99, 255, 0.1)', text: 'var(--primary)', label: "Agent Web en cours..." };
      case 'SENT':
        return { bg: 'rgba(16, 185, 129, 0.1)', text: 'var(--success)', label: 'Traitée / Envoyée' };
      case 'FAILED':
        return { bg: 'rgba(239, 68, 68, 0.1)', text: 'var(--error)', label: 'Échouée' };
      case 'REJECTED':
        return { bg: 'rgba(255, 255, 255, 0.05)', text: 'var(--text-secondary)', label: 'Rejetée' };
      case 'MANUAL_REQUIRED':
        return { bg: 'rgba(245, 158, 11, 0.1)', text: 'var(--warning)', label: 'Action requise' };
      default:
        return { bg: 'rgba(255, 255, 255, 0.05)', text: 'var(--text-primary)', label: status };
    }
  };

  const getModeLabel = (mode) => {
    return mode === 'FULL_AUTO' ? 'Auto-apply' : 'Validation humaine';
  };

  return (
    <div>
      <Navbar />
      <main className="container">
        
        {/* Page Header */}
        <div style={{ marginBottom: '2.5rem', marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <h1 className="gradient-text" style={{ fontSize: '2.2rem', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Send size={28} style={{ color: 'var(--primary)' }} />
              Suivi des candidatures & Agent Web
            </h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              Consultez les actions autonomes de l'Agent Web (Playwright), examinez les captures d'écran et suivez vos candidatures.
            </p>
          </div>

          {/* Auto Apply Settings Box */}
          <div className="glass-card" style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '1.25rem 1.5rem',
            background: 'var(--bg-secondary)',
            border: '1px solid rgba(108, 99, 255, 0.15)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                background: settings.auto_apply_enabled ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                color: settings.auto_apply_enabled ? 'var(--success)' : 'var(--text-muted)',
                padding: '0.75rem',
                borderRadius: '10px',
                display: 'flex'
              }}>
                <Settings size={22} className={settingsLoading ? 'animate-spin' : ''} style={{ animation: settingsLoading ? 'spin 2s linear infinite' : 'none' }} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: '600' }}>Candidature Automatique (Auto-apply)</h4>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {settings.auto_apply_enabled 
                    ? "L'Agent Web Playwright s'exécute automatiquement dès que le score de matching dépasse le seuil configuré."
                    : "Chaque candidature générée reste en attente de votre approbation explicite avant lancement de l'Agent Web."
                  }
                </p>
              </div>
            </div>
            
            <button
              onClick={handleToggleAutoApply}
              disabled={settingsLoading}
              className={`btn ${settings.auto_apply_enabled ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                padding: '0.5rem 1.25rem',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                minWidth: '150px'
              }}
            >
              {settingsLoading ? (
                <Loader2 size={16} className="animate-spin" style={{ animation: 'spin 2s linear infinite' }} />
              ) : settings.auto_apply_enabled ? (
                <>
                  <Check size={16} />
                  Activé
                </>
              ) : (
                <>
                  <X size={16} />
                  Désactivé
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--error)',
            color: 'var(--error)',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '2rem'
          }}>
            {error}
          </div>
        )}

        {/* Tab Filters */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--border-color)',
          marginBottom: '2rem',
          overflowX: 'auto',
          paddingBottom: '0.5rem'
        }}>
          {[
            { id: 'ALL', label: 'Toutes' },
            { id: 'PENDING_VALIDATION', label: 'En attente' },
            { id: 'MANUAL_REQUIRED', label: 'Action requise' },
            { id: 'SENT', label: 'Traitées / Envoyées' },
            { id: 'FAILED', label: 'Échouées' },
            { id: 'REJECTED', label: 'Rejetées' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? 'var(--primary-glow)' : 'transparent',
                color: activeTab === tab.id ? 'var(--primary)' : 'var(--text-secondary)',
                border: 'none',
                padding: '0.6rem 1.2rem',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '0.9rem',
                whiteSpace: 'nowrap',
                transition: 'all var(--transition-fast)'
              }}
            >
              {tab.label}
              {applications.filter(a => tab.id === 'ALL' || a.status === tab.id).length > 0 && (
                <span style={{
                  marginLeft: '0.5rem',
                  fontSize: '0.75rem',
                  background: activeTab === tab.id ? 'var(--primary)' : 'var(--bg-tertiary)',
                  color: activeTab === tab.id ? '#fff' : 'var(--text-secondary)',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '10px'
                }}>
                  {applications.filter(a => tab.id === 'ALL' || a.status === tab.id).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Applications List */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--text-secondary)' }}>
            <Loader2 size={36} className="animate-spin" style={{ display: 'inline', animation: 'spin 2s linear infinite', marginBottom: '1rem' }} />
            <p>Chargement des candidatures...</p>
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Info size={40} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
            <h3>Aucune candidature trouvée</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              {activeTab === 'ALL' 
                ? "Vous n'avez pas encore généré de candidatures. Rendez-vous sur la page Matching IA pour postuler !"
                : `Aucune candidature dans la catégorie "${activeTab}".`
              }
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {filteredApps.map((app) => {
              const badge = getStatusBadgeStyles(app.status);
              const hasActions = app.status === 'PENDING_VALIDATION';
              const isLoadingApp = actionLoading[app.id];
              const isExpanded = expandedProofs[app.id] !== undefined ? expandedProofs[app.id] : (app.status === 'SENT' || app.status === 'MANUAL_REQUIRED' || app.status === 'FAILED');
              const proofTab = activeProofTab[app.id] || 'screenshots';
              const hasProofs = app.screenshots || app.execution_logs || app.cover_letter;
              
              return (
                <div 
                  key={app.id} 
                  className="glass-card"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem',
                    borderLeft: `4px solid ${badge.text}`,
                    transition: 'all 0.3s ease'
                  }}
                >
                  {/* Card Main Info */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ flex: 1, minWidth: '250px' }}>
                      <h3 style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>
                        {app.match_details?.job_title || 'Offre inconnue'}
                      </h3>
                      <p style={{ color: 'var(--accent)', fontWeight: '600', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                        {app.match_details?.company || 'Entreprise inconnue'}
                      </p>
                      
                      {/* Meta information tags */}
                      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Clock size={12} />
                          {new Date(app.created_at).toLocaleDateString('fr-FR', {
                            day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
                          })}
                        </span>
                        <span>•</span>
                        <span>Mode : {getModeLabel(app.mode)}</span>
                        <span>•</span>
                        <span>Lieu : {app.match_details?.location || 'Non précisé'}</span>
                      </div>
                    </div>

                    {/* Right side score, link & status */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                      {/* Direct Offer URL */}
                      {app.match_details?.source_url && (
                        <a
                          href={app.match_details.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                        >
                          Offre originale <ExternalLink size={12} />
                        </a>
                      )}

                      {/* Match Score */}
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block' }}>Compatibilité</span>
                        <strong style={{ fontSize: '1.15rem', color: 'var(--accent)' }}>
                          {app.match_details?.compatibility_score ? `${Math.round(app.match_details.compatibility_score)}%` : 'N/A'}
                        </strong>
                      </div>
                      
                      {/* Status Badge */}
                      <span style={{
                        background: badge.bg,
                        color: badge.text,
                        padding: '0.35rem 0.85rem',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        border: `1px solid rgba(255, 255, 255, 0.05)`
                      }}>
                        {badge.label}
                      </span>
                    </div>
                  </div>

                  {/* Actions & Alerts */}
                  {hasActions && (
                    <div style={{ 
                      borderTop: '1px solid var(--border-color)', 
                      paddingTop: '1rem', 
                      display: 'flex', 
                      flexDirection: 'column',
                      gap: '1rem' 
                    }}>
                      <div style={{ display: 'flex', gap: '1rem' }}>
                        <button
                          onClick={() => handleApprove(app.id)}
                          disabled={isLoadingApp !== undefined}
                          className="btn btn-primary"
                          style={{
                            padding: '0.5rem 1.25rem',
                            fontSize: '0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            background: 'linear-gradient(135deg, var(--primary) 0%, #4f46e5 100%)',
                            boxShadow: '0 4px 15px rgba(99, 102, 241, 0.3)'
                          }}
                        >
                          {isLoadingApp === 'approve' ? (
                            <>
                              <Loader2 size={16} className="animate-spin" style={{ animation: 'spin 2s linear infinite' }} />
                              Lancement de l'Agent Playwright...
                            </>
                          ) : (
                            <>
                              <Send size={16} />
                              Lancer l'Agent Web & Exécuter la Candidature
                            </>
                          )}
                        </button>
                        
                        <button
                          onClick={() => setShowRejectForm(prev => ({ ...prev, [app.id]: !prev[app.id] }))}
                          disabled={isLoadingApp !== undefined}
                          className="btn btn-secondary"
                          style={{
                            padding: '0.5rem 1.25rem',
                            fontSize: '0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem'
                          }}
                        >
                          <X size={16} />
                          Rejeter
                        </button>
                      </div>

                      {/* Rejection Form */}
                      {showRejectForm[app.id] && (
                        <div style={{
                          background: 'rgba(255, 255, 255, 0.02)',
                          border: '1px solid var(--border-color)',
                          padding: '1rem',
                          borderRadius: '8px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.75rem',
                          animation: 'fadeIn 0.2s ease'
                        }}>
                          <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            Motif du rejet (facultatif) :
                          </label>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <input
                              type="text"
                              className="form-input"
                              placeholder="Ex: Salaire insuffisant, trop loin..."
                              value={rejectionReasons[app.id] || ''}
                              onChange={(e) => setRejectionReasons(prev => ({ ...prev, [app.id]: e.target.value }))}
                              style={{ flex: 1, padding: '0.5rem 0.75rem', fontSize: '0.875rem' }}
                            />
                            <button
                              onClick={() => handleReject(app.id)}
                              disabled={isLoadingApp === 'reject'}
                              className="btn btn-primary"
                              style={{
                                padding: '0.5rem 1rem',
                                fontSize: '0.85rem',
                                background: 'linear-gradient(135deg, var(--error) 0%, #dc2626 100%)'
                              }}
                            >
                              {isLoadingApp === 'reject' ? (
                                <Loader2 size={14} className="animate-spin" style={{ animation: 'spin 2s linear infinite' }} />
                              ) : (
                                "Confirmer le rejet"
                              )}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Failure reason for FAILED status */}
                  {app.status === 'FAILED' && app.failure_reason && (
                    <div style={{
                      background: 'rgba(239, 68, 68, 0.05)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      color: 'var(--error)',
                      padding: '0.85rem 1rem',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.5rem'
                    }}>
                      <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong>Rapport d'échec :</strong> {app.failure_reason}
                      </div>
                    </div>
                  )}

                  {/* Warning banner for MANUAL_REQUIRED status */}
                  {app.status === 'MANUAL_REQUIRED' && app.failure_reason && (
                    <div style={{
                      background: 'rgba(245, 158, 11, 0.05)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      color: 'var(--warning)',
                      padding: '0.85rem 1rem',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.5rem'
                    }}>
                      <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong>Intervention requise :</strong> {app.failure_reason}
                      </div>
                    </div>
                  )}

                  {/* Proofs & Web Agent Accordion Section */}
                  <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
                    <button
                      onClick={() => toggleProofAccordion(app.id)}
                      className="btn btn-secondary"
                      style={{
                        width: '100%',
                        justifyContent: 'space-between',
                        padding: '0.5rem 1rem',
                        fontSize: '0.85rem',
                        background: 'rgba(255, 255, 255, 0.02)'
                      }}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Camera size={16} style={{ color: 'var(--accent)' }} />
                        Preuves & Rapport de l'Agent Web (Captures d'écran, Logs, Lettre IA)
                      </span>
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>

                    {/* Accordion Content */}
                    {isExpanded && (
                      <div style={{
                        marginTop: '0.75rem',
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '12px',
                        padding: '1.25rem',
                        animation: 'fadeIn 0.2s ease'
                      }}>
                        {/* Top bar with Re-run Agent button */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                          <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                            Rapport d'exécution de l'Agent Playwright
                          </span>
                          <button
                            onClick={() => handleRunAgent(app.id)}
                            disabled={isLoadingApp !== undefined}
                            className="btn btn-accent"
                            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                          >
                            {isLoadingApp === 'run_agent' ? (
                              <>
                                <Loader2 size={14} className="animate-spin" style={{ animation: 'spin 2s linear infinite' }} />
                                Exécution de Playwright...
                              </>
                            ) : (
                              <>
                                <Camera size={14} />
                                {hasProofs ? "Ré-exécuter l'Agent Web" : "Lancer l'Agent Web Playwright"}
                              </>
                            )}
                          </button>
                        </div>
                          {/* Inner Tabs */}
                          <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                            <button
                              onClick={() => setActiveProofTab(prev => ({ ...prev, [app.id]: 'screenshots' }))}
                              style={{
                                background: proofTab === 'screenshots' ? 'var(--primary-glow)' : 'transparent',
                                color: proofTab === 'screenshots' ? 'var(--primary)' : 'var(--text-secondary)',
                                border: 'none',
                                padding: '0.4rem 0.8rem',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.4rem'
                              }}
                            >
                              <Camera size={14} /> Captures d'écran ({app.screenshots ? Object.keys(app.screenshots).length : 0})
                            </button>

                            <button
                              onClick={() => setActiveProofTab(prev => ({ ...prev, [app.id]: 'logs' }))}
                              style={{
                                background: proofTab === 'logs' ? 'var(--primary-glow)' : 'transparent',
                                color: proofTab === 'logs' ? 'var(--primary)' : 'var(--text-secondary)',
                                border: 'none',
                                padding: '0.4rem 0.8rem',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.4rem'
                              }}
                            >
                              <Terminal size={14} /> Journal d'actions ({app.execution_logs ? app.execution_logs.length : 0})
                            </button>

                            <button
                              onClick={() => setActiveProofTab(prev => ({ ...prev, [app.id]: 'letter' }))}
                              style={{
                                background: proofTab === 'letter' ? 'var(--primary-glow)' : 'transparent',
                                color: proofTab === 'letter' ? 'var(--primary)' : 'var(--text-secondary)',
                                border: 'none',
                                padding: '0.4rem 0.8rem',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.4rem'
                              }}
                            >
                              <FileCheck size={14} /> Lettre de motivation IA
                            </button>
                          </div>

                          {/* Tab 1: Screenshots */}
                          {proofTab === 'screenshots' && (
                            <div>
                              {app.screenshots && Object.keys(app.screenshots).length > 0 ? (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                                  {Object.entries(app.screenshots).map(([stepKey, imgUrl]) => (
                                    <div key={stepKey} style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '0.5rem', border: '1px solid var(--border-color)' }}>
                                      <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: '600', display: 'block', marginBottom: '0.3rem' }}>
                                        {stepKey === 'step1_opened' ? '1. Page ouverte' : stepKey === 'step2_filled' ? '2. Formulaire rempli' : '3. Résultat final'}
                                      </span>
                                      <a href={imgUrl} target="_blank" rel="noopener noreferrer">
                                        <img
                                          src={imgUrl}
                                          alt={stepKey}
                                          style={{ width: '100%', height: '140px', objectFit: 'cover', borderRadius: '6px', cursor: 'zoom-in', border: '1px solid rgba(255,255,255,0.1)' }}
                                        />
                                      </a>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Aucune capture d'écran disponible pour le moment.</p>
                              )}
                            </div>
                          )}

                          {/* Tab 2: Execution Logs */}
                          {proofTab === 'logs' && (
                            <div style={{
                              background: '#0d0d1a',
                              borderRadius: '8px',
                              padding: '1rem',
                              fontFamily: 'monospace',
                              fontSize: '0.8rem',
                              maxHeight: '250px',
                              overflowY: 'auto',
                              border: '1px solid var(--border-color)'
                            }}>
                              {app.execution_logs && app.execution_logs.length > 0 ? (
                                app.execution_logs.map((log, i) => (
                                  <div key={i} style={{ marginBottom: '0.4rem', display: 'flex', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>[{log.timestamp}]</span>
                                    <span style={{
                                      color: log.status === 'SUCCESS' ? 'var(--success)' : log.status === 'ERROR' ? 'var(--error)' : log.status === 'WARNING' ? 'var(--warning)' : 'var(--accent)',
                                      fontWeight: '600'
                                    }}>
                                      [{log.step}]
                                    </span>
                                    <span style={{ color: 'var(--text-primary)' }}>{log.message}</span>
                                  </div>
                                ))
                              ) : (
                                <p style={{ color: 'var(--text-muted)' }}>Aucun journal d'exécution enregistré.</p>
                              )}
                            </div>
                          )}

                          {/* Tab 3: Cover Letter */}
                          {proofTab === 'letter' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Lettre rédigée sur-mesure par Groq LLM :</span>
                                <button
                                  onClick={() => handleCopyCoverLetter(app.cover_letter, app.id)}
                                  className="btn btn-secondary"
                                  style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                                >
                                  <Copy size={12} />
                                  {copiedAppId === app.id ? "Copié !" : "Copier le texte"}
                                </button>
                              </div>
                              <textarea
                                readOnly
                                value={app.cover_letter || "Aucune lettre de motivation générée."}
                                rows={8}
                                style={{
                                  background: 'rgba(0,0,0,0.3)',
                                  border: '1px solid var(--border-color)',
                                  borderRadius: '8px',
                                  padding: '0.75rem',
                                  color: 'var(--text-primary)',
                                  fontSize: '0.85rem',
                                  fontFamily: 'inherit',
                                  lineHeight: '1.5',
                                  resize: 'vertical'
                                }}
                              />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
      
      <style jsx global>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-5px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
