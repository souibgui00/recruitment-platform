'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import { useAuth } from '../../context/AuthContext';
import Link from 'next/link';
import api from '../../lib/api';
import { FileText, Briefcase, Sparkles, Plus, TrendingUp } from 'lucide-react';

export default function DashboardPage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [stats, setStats] = useState({ cvCount: 0, jobsCount: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [cvRes, jobsRes] = await Promise.all([
          api.get('/cv/'),
          api.get('/jobs/offers?limit=1000&offset=0')
        ]);
        setStats({
          cvCount: cvRes.data.length || 0,
          jobsCount: jobsRes.data.length || 0
        });
      } catch (err) {
        console.error("Erreur lors de la récupération des stats", err);
      } finally {
        setLoading(false);
      }
    }
    if (!authLoading && isAuthenticated) {
      fetchStats();
    } else if (!authLoading) {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated]);

  return (
    <div>
      <Navbar />
      <main className="container">
        {/* Welcome Section */}
        <div style={{ marginBottom: '3rem', marginTop: '1rem' }}>
          <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>
            Ravi de vous revoir !
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
            Gérez vos CVs et découvrez vos compatibilités d'emploi en un clic grâce à notre IA.
          </p>
        </div>

        {/* Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
          marginBottom: '3rem'
        }}>
          <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              background: 'rgba(108, 99, 255, 0.1)',
              color: 'var(--primary)',
              padding: '1rem',
              borderRadius: '12px',
              display: 'flex',
            }}>
              <FileText size={32} />
            </div>
            <div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Mes CVs analysés</p>
              <h3 style={{ fontSize: '1.8rem', margin: 0 }}>
                {loading ? '...' : stats.cvCount}
              </h3>
            </div>
          </div>

          <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              background: 'rgba(0, 212, 255, 0.1)',
              color: 'var(--accent)',
              padding: '1rem',
              borderRadius: '12px',
              display: 'flex',
            }}>
              <Briefcase size={32} />
            </div>
            <div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Offres indexées</p>
              <h3 style={{ fontSize: '1.8rem', margin: 0 }}>
                {loading ? '...' : stats.jobsCount}
              </h3>
            </div>
          </div>

          <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              color: 'var(--success)',
              padding: '1rem',
              borderRadius: '12px',
              display: 'flex',
            }}>
              <TrendingUp size={32} />
            </div>
            <div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Précision de l'IA</p>
              <h3 style={{ fontSize: '1.8rem', margin: 0 }}>94.2%</h3>
            </div>
          </div>
        </div>

        {/* Quick Actions / Navigation Cards */}
        <h2 style={{ fontSize: '1.6rem', marginBottom: '1.5rem' }}>Que voulez-vous faire aujourd'hui ?</h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '2rem'
        }}>
          {/* Action 1: Upload CV */}
          <div className="glass-card" style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            height: '220px'
          }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={20} className="text-secondary" />
                  Analyser un nouveau CV
                </h3>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                Déposez votre CV au format PDF. Notre moteur d'extraction structurera vos compétences et expériences.
              </p>
            </div>
            <Link href="/cv/upload" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
              <Plus size={16} />
              Uploader mon CV
            </Link>
          </div>

          {/* Action 2: Matching */}
          <div className="glass-card" style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            height: '220px',
            borderColor: 'rgba(0, 212, 255, 0.15)'
          }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Sparkles size={20} style={{ color: 'var(--accent)' }} />
                  Lancer le Matching IA
                </h3>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                Comparez instantanément votre profil avec toutes les offres d'emploi indexées et obtenez une analyse détaillée par LLM.
              </p>
            </div>
            <Link href="/matching" className="btn btn-accent" style={{ alignSelf: 'flex-start' }}>
              Découvrir les offres
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
