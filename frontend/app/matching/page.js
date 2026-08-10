'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import api from '../../lib/api';
import Link from 'next/link';
import { Sparkles, FileText, CheckCircle, AlertTriangle, ChevronRight, Settings, Info, Loader2, Send } from 'lucide-react';

export default function MatchingPage() {
  const [cvs, setCvs] = useState([]);
  const [selectedCvId, setSelectedCvId] = useState('');
  const [config, setConfig] = useState({ threshold: 70, semantic_weight: 0.6, llm_weight: 0.4 });
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [error, setError] = useState('');
  const [selectedMatch, setSelectedMatch] = useState(null); // For details sidebar/modal
  const [computingMatchId, setComputingMatchId] = useState(null);
  const [applications, setApplications] = useState([]);
  const [applyingMatchId, setApplyingMatchId] = useState(null);

  // Fetch initial data
  useEffect(() => {
    async function initData() {
      try {
        const [cvRes, configRes, appsRes] = await Promise.all([
          api.get('/cv/'),
          api.get('/matching/config'),
          api.get('/applications/')
        ]);
        setCvs(cvRes.data);
        if (cvRes.data.length > 0) {
          setSelectedCvId(cvRes.data[0].id);
        }
        setConfig(configRes.data);
        setApplications(appsRes.data);
      } catch (err) {
        console.error(err);
        setError("Erreur d'initialisation du module de matching.");
      } finally {
        setLoadingConfig(false);
      }
    }
    initData();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await api.get('/applications/');
      setApplications(response.data);
    } catch (err) {
      console.error("Erreur lors de la récupération des candidatures:", err);
    }
  };

  const fetchMatches = async (cvId) => {
    if (!cvId) return;
    setLoading(true);
    setError('');
    setSelectedMatch(null);
    try {
      const [matchesRes, appsRes] = await Promise.all([
        api.get(`/matching/cv/${cvId}/best-matches?limit=10`),
        api.get('/applications/')
      ]);
      setMatches(matchesRes.data);
      setApplications(appsRes.data);
    } catch (err) {
      console.error(err);
      setError("Impossible de calculer les recommandations pour ce CV.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApplication = async (matchId) => {
    setApplyingMatchId(matchId);
    try {
      const response = await api.post(`/applications/from-match/${matchId}`);
      await fetchApplications();
      const app = response.data;
      if (app.status === 'PENDING_VALIDATION') {
        alert("Candidature créée avec succès et mise en attente de validation humaine.");
      } else if (app.status === 'SENT') {
        alert("Candidature automatique envoyée directement avec succès !");
      } else if (app.status === 'FAILED') {
        alert(`La candidature a été générée en mode Auto-apply mais l'envoi a échoué : ${app.failure_reason}`);
      } else {
        alert("Candidature créée avec succès !");
      }
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "Une erreur est survenue lors de la création de la candidature.";
      alert(errMsg);
    } finally {
      setApplyingMatchId(null);
    }
  };

  useEffect(() => {
    if (selectedCvId) {
      fetchMatches(selectedCvId);
    }
  }, [selectedCvId]);

  // Recalculate single match (call post compute_single_match)
  const handleRecalculateMatch = async (jobOfferId) => {
    setComputingMatchId(jobOfferId);
    try {
      const response = await api.post(`/matching/cv/${selectedCvId}/job/${jobOfferId}`);
      // Update local list
      setMatches(matches.map(m => m.job_offer?.id === jobOfferId ? { ...m, ...response.data } : m));
      // Update selection if open
      if (selectedMatch && selectedMatch.job_offer?.id === jobOfferId) {
        setSelectedMatch({ ...selectedMatch, ...response.data });
      }
    } catch (err) {
      console.error(err);
      alert("Une erreur est survenue lors de la réévaluation de l'IA.");
    } finally {
      setComputingMatchId(null);
    }
  };

  // Update config weights
  const handleWeightChange = async (semanticVal) => {
    const semantic_weight = parseFloat(semanticVal);
    const llm_weight = parseFloat((1.0 - semantic_weight).toFixed(2));
    
    // Optimistic UI update
    setConfig(prev => ({ ...prev, semantic_weight, llm_weight }));

    try {
      await api.put('/matching/config', { semantic_weight });
      // Reload matches with new weights
      if (selectedCvId) {
        fetchMatches(selectedCvId);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <Navbar />
      <main className="container" style={{ display: 'grid', gridTemplateColumns: selectedMatch ? '2fr 1.2fr' : '1fr', gap: '2rem', transition: 'all 0.3s ease' }}>
        
        {/* Left main area */}
        <div>
          {/* Header */}
          <div style={{ marginBottom: '2rem', marginTop: '1rem' }}>
            <h1 className="gradient-text" style={{ fontSize: '2.2rem', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Sparkles size={28} style={{ color: 'var(--accent)' }} />
              Matching Intelligent
            </h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              Découvrez la compatibilité de votre profil avec les offres du marché, propulsée par un calcul hybride vectoriel et LLM.
            </p>
          </div>

          {/* Config & selector card */}
          <div className="glass-card" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
            marginBottom: '2.5rem',
            alignItems: 'center'
          }}>
            {/* CV Selector */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" htmlFor="cv-select" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <FileText size={16} /> Sélectionner un CV
              </label>
              <select
                id="cv-select"
                value={selectedCvId}
                onChange={(e) => setSelectedCvId(e.target.value)}
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  color: 'var(--text-primary)',
                  outline: 'none',
                  cursor: 'pointer',
                  width: '100%',
                  fontSize: '0.95rem'
                }}
              >
                {cvs.map(cv => (
                  <option key={cv.id} value={cv.id} style={{ background: 'var(--bg-secondary)' }}>
                    {cv.filename || 'CV sans nom'} {cv.personal_info ? `(${cv.personal_info.full_name})` : ''}
                  </option>
                ))}
                {cvs.length === 0 && (
                  <option value="" style={{ background: 'var(--bg-secondary)' }}>Aucun CV trouvé, uploadez-en un d'abord</option>
                )}
              </select>
            </div>

            {/* Weights sliders */}
            {!loadingConfig && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: '600' }}>
                  <span style={{ color: 'var(--primary)' }}>Sémantique (Vectoriel) : {Math.round(config.semantic_weight * 100)}%</span>
                  <span style={{ color: 'var(--accent)' }}>IA / LLM (Groq) : {Math.round(config.llm_weight * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.1"
                  value={config.semantic_weight}
                  onChange={(e) => handleWeightChange(e.target.value)}
                  style={{
                    width: '100%',
                    accentColor: 'var(--primary)',
                    cursor: 'pointer'
                  }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  <Settings size={12} />
                  <span>La répartition des poids s'adapte en temps réel sur 1.0</span>
                </div>
                
                <div className="glass-card" style={{ 
                  marginTop: '1.25rem', 
                  padding: '1rem', 
                  fontSize: '0.8rem', 
                  borderRadius: '10px',
                  border: '1px solid var(--glass-border)',
                  background: 'rgba(255, 255, 255, 0.02)',
                  textAlign: 'left'
                }}>
                  <p style={{ margin: '0 0 0.5rem 0', fontWeight: '600', color: 'var(--text-primary)' }}>
                    Comment fonctionne le score hybride ?
                  </p>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <li>
                      <strong style={{ color: 'var(--primary)' }}>Sémantique (Vectoriel) :</strong> Mesure la similarité mathématique brute entre le texte de votre CV et l'offre d'emploi (embeddings de texte).
                    </li>
                    <li>
                      <strong style={{ color: 'var(--accent)' }}>IA / LLM (Groq) :</strong> Évalue l'adéquation de manière qualitative selon les forces et faiblesses identifiées par l'IA.
                    </li>
                  </ul>
                  <p style={{ margin: '0.75rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.75rem', fontStyle: 'italic' }}>
                    Déplacez le curseur pour équilibrer la précision de la recherche de mots-clés vectorielle et l'évaluation qualitative de l'IA.
                  </p>
                </div>
              </div>
            )}
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

          {/* Matches results list */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--text-secondary)' }}>
              Calcul de compatibilité hybride en cours...
            </div>
          ) : matches.length === 0 ? (
            <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
              <Info size={40} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
              <h3>Aucune correspondance</h3>
              <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Assurez-vous d'avoir indexé des offres d'emploi ou que le CV sélectionné contient des informations de profil complètes.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {matches.map((match) => (
                <div
                  key={match.id || match.job_offer?.id}
                  onClick={() => setSelectedMatch(match)}
                  className="glass-card"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    borderLeft: `4px solid ${match.compatibility_score >= 75 ? 'var(--success)' : match.compatibility_score >= 50 ? 'var(--warning)' : 'var(--error)'}`,
                    background: selectedMatch?.id === match.id ? 'rgba(108, 99, 255, 0.05)' : 'var(--glass-bg)',
                    borderColor: selectedMatch?.id === match.id ? 'rgba(108, 99, 255, 0.3)' : 'var(--glass-border)'
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0, paddingRight: '1rem' }}>
                    <h4 style={{ fontSize: '1.1rem', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {match.job_offer?.title}
                    </h4>
                    <p style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.85rem', margin: '0.2rem 0' }}>
                      {match.job_offer?.company}
                    </p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
                      Localisation : {match.job_offer?.location || 'Non précisé'}
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    {/* Compatibility Score Circle */}
                    <div style={{
                      width: '54px',
                      height: '54px',
                      borderRadius: '50%',
                      border: `3px solid ${match.compatibility_score >= 75 ? 'var(--success)' : match.compatibility_score >= 50 ? 'var(--warning)' : 'var(--error)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      fontSize: '1rem',
                      color: match.compatibility_score >= 75 ? 'var(--success)' : match.compatibility_score >= 50 ? 'var(--warning)' : 'var(--text-primary)',
                      background: 'rgba(0,0,0,0.2)'
                    }}>
                      {Math.round(match.compatibility_score)}%
                    </div>
                    <ChevronRight size={20} style={{ color: 'var(--text-muted)' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right side explanation Panel */}
        {selectedMatch && (
          <div className="glass-card" style={{
            position: 'sticky',
            top: '80px',
            height: 'calc(100vh - 120px)',
            overflowY: 'auto',
            borderLeft: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            padding: '2rem 1.5rem',
            background: 'var(--bg-secondary)'
          }}>
            {/* Header info */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Analyse Détaillée</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Offre : {selectedMatch.job_offer?.title}</p>
              </div>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => setSelectedMatch(null)}
              >
                Fermer
              </button>
            </div>

            {/* Score details breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', background: 'rgba(0,0,0,0.15)', padding: '1rem', borderRadius: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Score Global</span>
                <span style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--accent)' }}>{selectedMatch.compatibility_score}%</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Similarité Sémantique</span>
                  <span>{Math.round(selectedMatch.semantic_similarity * 100)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Score Évaluation LLM</span>
                  <span>{selectedMatch.llm_score}%</span>
                </div>
              </div>
            </div>

            {/* Candidature action/status section */}
            {(() => {
              const existingApp = applications.find(app => app.match_id === selectedMatch.id);
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)', margin: '0 0 0.25rem 0' }}>Candidature</h4>
                  {existingApp ? (
                    <div style={{
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-color)',
                      padding: '0.75rem 1rem',
                      borderRadius: '10px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.4rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Statut :</span>
                        <span style={{
                          background: existingApp.status === 'SENT' ? 'rgba(16, 185, 129, 0.1)' :
                                      existingApp.status === 'PENDING_VALIDATION' ? 'rgba(245, 158, 11, 0.1)' :
                                      existingApp.status === 'FAILED' ? 'rgba(239, 68, 68, 0.1)' :
                                      existingApp.status === 'REJECTED' ? 'rgba(255,255,255,0.05)' : 'rgba(108,99,255,0.1)',
                          color: existingApp.status === 'SENT' ? 'var(--success)' :
                                 existingApp.status === 'PENDING_VALIDATION' ? 'var(--warning)' :
                                 existingApp.status === 'FAILED' ? 'var(--error)' :
                                 existingApp.status === 'REJECTED' ? 'var(--text-secondary)' : 'var(--primary)',
                          padding: '0.2rem 0.6rem',
                          borderRadius: '15px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}>
                          {existingApp.status === 'PENDING_VALIDATION' ? 'En attente' :
                           existingApp.status === 'SENT' ? 'Envoyée' :
                           existingApp.status === 'FAILED' ? 'Échouée' :
                           existingApp.status === 'REJECTED' ? 'Rejetée' : existingApp.status}
                        </span>
                      </div>
                      {existingApp.failure_reason && (
                        <p style={{ fontSize: '0.8rem', color: existingApp.status === 'REJECTED' ? 'var(--text-secondary)' : 'var(--error)', margin: '0.2rem 0 0 0' }}>
                          <strong>{existingApp.status === 'REJECTED' ? 'Motif rejet :' : 'Échec technique :'}</strong> {existingApp.failure_reason}
                        </p>
                      )}
                      <Link 
                        href="/applications"
                        style={{
                          fontSize: '0.8rem',
                          color: 'var(--accent)',
                          fontWeight: '600',
                          alignSelf: 'flex-end',
                          marginTop: '0.25rem'
                        }}
                      >
                        Gérer dans mes candidatures →
                      </Link>
                    </div>
                  ) : (
                    <button
                      className="btn btn-accent"
                      style={{
                        width: '100%',
                        padding: '0.65rem',
                        fontSize: '0.875rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.4rem'
                      }}
                      disabled={applyingMatchId === selectedMatch.id}
                      onClick={() => handleCreateApplication(selectedMatch.id)}
                    >
                      {applyingMatchId === selectedMatch.id ? (
                        <>
                          <Loader2 size={14} className="animate-spin" />
                          Traitement...
                        </>
                      ) : (
                        <>
                          <Send size={14} />
                          Postuler à cette offre
                        </>
                      )}
                    </button>
                  )}
                </div>
              );
            })()}

            {/* Action button: recalculate match using LLM */}
            <button
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '0.65rem',
                fontSize: '0.875rem'
              }}
              disabled={computingMatchId === selectedMatch.job_offer?.id}
              onClick={() => handleRecalculateMatch(selectedMatch.job_offer?.id)}
            >
              {computingMatchId === selectedMatch.job_offer?.id ? (
                <>
                  <Loader2 size={14} className="animate-spin" style={{ animation: 'spin 2s linear infinite' }} />
                  Analyse qualitative...
                </>
              ) : (
                "Réévaluer via Groq / Llama-3"
              )}
            </button>

            {/* Summary */}
            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Synthèse IA</h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: '1.5', whiteSpace: 'pre-line' }}>
                {selectedMatch.summary || "Aucune analyse qualitative générée pour le moment. Cliquez sur le bouton de réévaluation ci-dessus pour lancer l'IA."}
              </p>
            </div>

            {/* Strengths points */}
            {selectedMatch.matching_points && selectedMatch.matching_points.length > 0 && (
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--success)' }}>Points Forts (Matches)</h4>
                <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', paddingLeft: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {selectedMatch.matching_points.map((pt, idx) => (
                    <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem' }}>
                      <CheckCircle size={14} style={{ color: 'var(--success)', flexShrink: 0, marginTop: '2px' }} />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Gaps points */}
            {selectedMatch.gap_points && selectedMatch.gap_points.length > 0 && (
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--warning)' }}>Lacunes ou Différences</h4>
                <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', paddingLeft: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {selectedMatch.gap_points.map((pt, idx) => (
                    <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem' }}>
                      <AlertTriangle size={14} style={{ color: 'var(--warning)', flexShrink: 0, marginTop: '2px' }} />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
