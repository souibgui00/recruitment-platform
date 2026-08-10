'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import api from '../../lib/api';
import Link from 'next/link';
import { 
  Bell, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  ArrowRight,
  Info,
  Loader2
} from 'lucide-react';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchNotifications() {
      try {
        const response = await api.get('/notifications/');
        // Sort by date descending (should be returned sorted from backend, but double check)
        const sorted = response.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setNotifications(sorted);
      } catch (err) {
        console.error(err);
        setError("Impossible de charger l'historique des notifications.");
      } finally {
        setLoading(false);
      }
    }
    fetchNotifications();
  }, []);

  const formatDateTime = (dateStr) => {
    return new Date(dateStr).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div>
      <Navbar />
      <main className="container" style={{ maxWidth: '800px' }}>
        
        {/* Header */}
        <div style={{ marginBottom: '2.5rem', marginTop: '1rem' }}>
          <h1 className="gradient-text" style={{ fontSize: '2.2rem', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Bell size={28} style={{ color: 'var(--primary)' }} />
            Journal d'activité
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Suivez en temps réel l'envoi de vos candidatures et les événements système.
          </p>
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

        {/* Content */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--text-secondary)' }}>
            <Loader2 size={36} className="animate-spin" style={{ display: 'inline', animation: 'spin 2s linear infinite', marginBottom: '1rem' }} />
            <p>Chargement du journal d'activité...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Info size={40} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
            <h3>Aucune notification</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              Les événements liés aux envois automatiques ou manuels apparaîtront ici.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {notifications.map((notif) => {
              const isSuccess = notif.type === 'APPLICATION_SENT';
              
              return (
                <div 
                  key={notif.id}
                  className="glass-card"
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    background: 'var(--bg-secondary)',
                    borderLeft: `3px solid ${isSuccess ? 'var(--success)' : 'var(--error)'}`,
                    padding: '1.25rem',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {/* Icon indicator */}
                  <div style={{
                    background: isSuccess ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: isSuccess ? 'var(--success)' : 'var(--error)',
                    padding: '0.5rem',
                    borderRadius: '8px',
                    display: 'flex',
                    flexShrink: 0
                  }}>
                    {isSuccess ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                  </div>

                  {/* Message and details */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        color: isSuccess ? 'var(--success)' : 'var(--error)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em'
                      }}>
                        {isSuccess ? 'Envoi Réussi' : 'Échec d\'envoi'}
                      </span>
                      
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <Clock size={12} />
                        {formatDateTime(notif.created_at)}
                      </span>
                    </div>

                    <p style={{ 
                      fontSize: '0.925rem', 
                      color: 'var(--text-primary)', 
                      margin: '0.5rem 0',
                      lineHeight: '1.4'
                    }}>
                      {notif.message}
                    </p>

                    {/* Action link to applications if present */}
                    {notif.related_application_id && (
                      <Link 
                        href="/applications"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          fontSize: '0.8rem',
                          color: 'var(--accent)',
                          fontWeight: '600',
                          marginTop: '0.25rem'
                        }}
                      >
                        Voir la candidature
                        <ArrowRight size={12} />
                      </Link>
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
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
