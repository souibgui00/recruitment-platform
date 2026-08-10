'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Link from 'next/link';
import api from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { FileText, Plus, Calendar, User, Eye, Trash2 } from 'lucide-react';

export default function CVPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [cvList, setCvList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCVs = async () => {
    try {
      const response = await api.get('/cv/');
      setCvList(response.data);
    } catch (err) {
      console.error(err);
      setError("Impossible de charger les CVs.");
    } finally {
      setLoading(false);
    }
  };

  // Wait for auth to be resolved before fetching
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchCVs();
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated]);

  const handleDelete = async (id, e) => {
    e.preventDefault();
    if (!confirm("Voulez-vous vraiment supprimer ce CV ?")) return;

    try {
      await api.delete(`/cv/${id}`);
      setCvList(cvList.filter(cv => cv.id !== id));
    } catch (err) {
      console.error(err);
      alert("Une erreur est survenue lors de la suppression.");
    }
  };

  return (
    <div>
      <Navbar />
      <main className="container">
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
          marginTop: '1rem'
        }}>
          <div>
            <h1 className="gradient-text" style={{ fontSize: '2.2rem', marginBottom: '0.25rem' }}>Mes CVs</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Gérez vos CVs analysés par l'intelligence artificielle</p>
          </div>
          <Link href="/cv/upload" className="btn btn-primary">
            <Plus size={16} />
            Analyser un CV
          </Link>
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

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
            Chargement de vos documents...
          </div>
        ) : cvList.length === 0 ? (
          <div className="glass-card" style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1.5rem'
          }}>
            <FileText size={48} style={{ color: 'var(--text-muted)' }} />
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Aucun CV pour le moment</h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto' }}>
                Uploadez votre premier CV au format PDF pour que notre IA puisse extraire vos compétences et trouver des offres correspondantes.
              </p>
            </div>
            <Link href="/cv/upload" className="btn btn-primary">
              Uploader mon premier CV
            </Link>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '1.5rem'
          }}>
            {cvList.map((cv) => (
              <div key={cv.id} className="glass-card" style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '180px'
              }}>
                <div>
                  <h3 style={{
                    fontSize: '1.15rem',
                    marginBottom: '0.75rem',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {cv.filename}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <User size={14} />
                      <span>{cv.full_name || 'Nom non extrait'}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Calendar size={14} />
                      <span>Analysé le {new Date(cv.parsed_at).toLocaleDateString('fr-FR')}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                  <Link href={`/cv/${cv.id}`} className="btn btn-secondary" style={{
                    flex: 1,
                    padding: '0.5rem',
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.35rem'
                  }}>
                    <Eye size={14} />
                    Aperçu
                  </Link>
                  <button
                    onClick={(e) => handleDelete(cv.id, e)}
                    className="btn btn-secondary"
                    style={{
                      padding: '0.5rem',
                      borderColor: 'rgba(239, 68, 68, 0.2)',
                      color: 'var(--error)'
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
