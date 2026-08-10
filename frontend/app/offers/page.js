'use client';

import { useState, useEffect, useCallback } from 'react';
import Navbar from '../../components/Navbar';
import api from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import {
  Briefcase, MapPin, Calendar, Clock, Search,
  Filter, Play, RefreshCw, Loader2, ChevronLeft, ChevronRight
} from 'lucide-react';

export default function OffersPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [offers, setOffers] = useState([]);
  const [loadingOffers, setLoadingOffers] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [contractType, setContractType] = useState('');
  const [limit] = useState(15);
  const [offset, setOffset] = useState(0);

  const [collecting, setCollecting] = useState(false);
  const [collectMessage, setCollectMessage] = useState('');
  const [keywords, setKeywords] = useState('developer python react');

  // Fetch offers from backend
  const fetchOffers = useCallback(async (silent = false) => {
    if (!silent) setLoadingOffers(true);
    setError('');
    try {
      let url = `/jobs/offers?limit=${limit}&offset=${offset}`;
      if (contractType) url += `&contract_type=${contractType}`;
      const res = await api.get(url);
      setOffers(res.data);
    } catch (err) {
      console.error(err);
      if (!silent) setError("Impossible de charger les offres d'emploi.");
    } finally {
      if (!silent) setLoadingOffers(false);
    }
  }, [limit, offset, contractType]);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchOffers();
    } else if (!authLoading) {
      setLoadingOffers(false);
    }
  }, [authLoading, isAuthenticated, fetchOffers]);

  // Trigger manual collection on demand
  const handleCollect = async () => {
    setCollecting(true);
    setCollectMessage('');
    try {
      // Fetch active sources first
      const sourcesRes = await api.get('/jobs/sources');
      const sources = sourcesRes.data || [];
      
      if (sources.length === 0) {
        setCollectMessage("Aucune source active disponible.");
        setCollecting(false);
        return;
      }

      // Trigger collection for all active sources
      await Promise.allSettled(
        sources.map(s => api.post(`/jobs/sources/${s.id}/collect?keywords=${encodeURIComponent(keywords)}`))
      );

      setCollectMessage("Collecte lancée en arrière-plan ! L'agent autonome récupère les offres...");
      
      // Periodically refresh offers list to pick up newly collected jobs
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        await fetchOffers(true);
        if (attempts >= 6) {
          clearInterval(interval);
          setCollecting(false);
        }
      }, 3000);

    } catch (err) {
      console.error(err);
      setCollectMessage("Erreur lors du lancement de la collecte.");
      setCollecting(false);
    }
  };

  // Client-side search filter
  const filteredOffers = offers.filter(o => {
    const q = search.toLowerCase();
    return (
      o.title.toLowerCase().includes(q) ||
      o.company.toLowerCase().includes(q) ||
      (o.description && o.description.toLowerCase().includes(q))
    );
  });

  return (
    <div>
      <Navbar />
      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>

      <main className="container">
        {/* Header */}
        <div style={{ marginBottom: '2rem', marginTop: '1rem' }}>
          <h1 className="gradient-text" style={{ fontSize: '2.2rem', marginBottom: '0.25rem' }}>
            Offres d'Emploi & Sourcing
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Explorez les opportunités indexées en continu par notre agent autonome.
          </p>
        </div>

        {/* Action / Collect Panel */}
        <div className="glass-card" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'rgba(108, 99, 255, 0.05)', border: '1px solid rgba(108, 99, 255, 0.2)' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Play size={18} style={{ color: 'var(--primary)' }} />
            Lancer une collecte d'offres manuelle
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem' }}>
            L'agent collecte automatiquement les offres toutes les 6 heures. Vous pouvez aussi forcer une collecte immédiate avec vos mots-clés ci-dessous :
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <input
              type="text"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              placeholder="Ex: python, developer, react..."
              style={{
                flex: 1, minWidth: '220px', padding: '0.65rem 1rem',
                background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)',
                borderRadius: '8px', color: 'var(--text-primary)', outline: 'none'
              }}
            />
            <button
              onClick={handleCollect}
              disabled={collecting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1.75rem',
                background: 'linear-gradient(135deg, #6c63ff 0%, #00d4ff 100%)',
                color: '#ffffff',
                fontWeight: '700',
                fontSize: '1rem',
                border: 'none',
                borderRadius: '10px',
                cursor: collecting ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 15px rgba(108, 99, 255, 0.4)',
                transition: 'all 0.2s ease'
              }}
            >
              {collecting ? (
                <>
                  <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                  Collecte en cours...
                </>
              ) : (
                <>
                  <Play size={18} fill="#ffffff" />
                  Démarrer la collecte
                </>
              )}
            </button>
            <button
              onClick={() => fetchOffers()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.75rem 1.25rem',
                background: 'rgba(255, 255, 255, 0.08)',
                color: 'var(--text-primary)',
                fontWeight: '600',
                fontSize: '0.95rem',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                cursor: 'pointer'
              }}
            >
              <RefreshCw size={16} />
              Actualiser
            </button>
          </div>

          {collectMessage && (
            <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--accent)', fontWeight: '500' }}>
              {collectMessage}
            </p>
          )}
        </div>

        {/* Filter Bar */}
        <div className="glass-card" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginBottom: '2rem', padding: '1rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '240px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.4rem 0.8rem' }}>
            <Search size={18} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Filtrer les offres affichées..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', width: '100%', fontSize: '0.95rem' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '180px' }}>
            <Filter size={18} style={{ color: 'var(--text-muted)' }} />
            <select
              value={contractType}
              onChange={e => { setContractType(e.target.value); setOffset(0); }}
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.5rem 1rem', color: 'var(--text-primary)', outline: 'none', cursor: 'pointer', width: '100%' }}
            >
              <option value="" style={{ background: 'var(--bg-secondary)' }}>Tous les contrats</option>
              <option value="CDI" style={{ background: 'var(--bg-secondary)' }}>CDI</option>
              <option value="CDD" style={{ background: 'var(--bg-secondary)' }}>CDD</option>
              <option value="STAGE" style={{ background: 'var(--bg-secondary)' }}>Stage</option>
              <option value="FREELANCE" style={{ background: 'var(--bg-secondary)' }}>Freelance</option>
            </select>
          </div>
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid var(--error)', color: 'var(--error)', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
            {error}
          </div>
        )}

        {/* Offers List */}
        {loadingOffers ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
            <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', marginBottom: '1rem', color: 'var(--primary)' }} />
            <p>Chargement des offres d'emploi...</p>
          </div>
        ) : filteredOffers.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Briefcase size={48} style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.4rem' }}>Aucune offre en base de données</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
              Le catalogue est vide. Cliquez sur le bouton ci-dessous pour que nos robots collectent les offres d'emploi en direct.
            </p>
            <button
              onClick={handleCollect}
              disabled={collecting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.6rem',
                padding: '0.85rem 2rem',
                background: 'linear-gradient(135deg, #6c63ff 0%, #00d4ff 100%)',
                color: '#ffffff',
                fontWeight: '700',
                fontSize: '1.05rem',
                border: 'none',
                borderRadius: '12px',
                cursor: collecting ? 'not-allowed' : 'pointer',
                boxShadow: '0 6px 25px rgba(108, 99, 255, 0.4)'
              }}
            >
              {collecting ? (
                <>
                  <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
                  Collecte en cours...
                </>
              ) : (
                <>
                  <Play size={20} fill="#ffffff" />
                  Démarrer la collecte maintenant
                </>
              )}
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {filteredOffers.map(offer => (
              <div key={offer.id} className="glass-card" style={{ padding: '1.5rem 2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: '700', margin: 0 }}>{offer.title}</h3>
                      {offer.compatibility_score !== null && offer.compatibility_score !== undefined && (
                        <span style={{
                          padding: '0.2rem 0.6rem', borderRadius: '20px', fontSize: '0.72rem', fontWeight: '700',
                          background: offer.compatibility_score >= 75 ? 'rgba(16,185,129,0.15)' : offer.compatibility_score >= 50 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                          color: offer.compatibility_score >= 75 ? 'var(--success)' : offer.compatibility_score >= 50 ? 'var(--warning)' : 'var(--error)',
                          border: `1px solid ${offer.compatibility_score >= 75 ? 'var(--success)' : offer.compatibility_score >= 50 ? 'var(--warning)' : 'var(--error)'}33`
                        }}>
                          ★ {Math.round(offer.compatibility_score)}% compatible (IA)
                        </span>
                      )}
                    </div>
                    <p style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.95rem', marginBottom: '0.75rem' }}>{offer.company}</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <MapPin size={13} />{offer.location || 'Distanciel / Non précisé'}
                      </div>
                      {offer.contract_type && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          <Clock size={13} />
                          <span style={{ background: 'rgba(0,212,255,0.1)', color: 'var(--accent)', padding: '0.1rem 0.5rem', borderRadius: '4px', fontWeight: '600' }}>
                            {offer.contract_type}
                          </span>
                        </div>
                      )}
                      {offer.posted_at && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          <Calendar size={13} />
                          Publiée le {new Date(offer.posted_at).toLocaleDateString('fr-FR')}
                        </div>
                      )}
                    </div>
                  </div>
                  {offer.source_url && (
                    <a href={offer.source_url} target="_blank" rel="noopener noreferrer"
                      className="btn btn-secondary"
                      style={{ fontSize: '0.85rem', padding: '0.5rem 1rem', whiteSpace: 'nowrap' }}>
                      Postuler →
                    </a>
                  )}
                </div>
                {offer.description && (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6', marginTop: '1rem', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {offer.description.replace(/<[^>]*>/g, '')}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {offers.length > 0 && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '2.5rem' }}>
            <button className="btn btn-secondary" disabled={offset === 0 || loadingOffers} onClick={() => setOffset(Math.max(0, offset - limit))} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <ChevronLeft size={16} /> Précédent
            </button>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              Page {Math.floor(offset / limit) + 1}
            </span>
            <button className="btn btn-secondary" disabled={offers.length < limit || loadingOffers} onClick={() => setOffset(offset + limit)} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              Suivant <ChevronRight size={16} />
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
