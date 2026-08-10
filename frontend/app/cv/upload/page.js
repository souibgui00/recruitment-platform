'use client';

import { useState } from 'react';
import Navbar from '../../../components/Navbar';
import { useRouter } from 'next/navigation';
import api from '../../../lib/api';
import { UploadCloud, FileText, ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function CVUploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        setFile(droppedFile);
        setError('');
      } else {
        setError("Seuls les fichiers PDF sont acceptés.");
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === "application/pdf") {
        setFile(selectedFile);
        setError('');
      } else {
        setError("Seuls les fichiers PDF sont acceptés.");
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/cv/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000 // Avoir un timeout généreux pour l'extraction de l'IA (60s)
      });
      // Redirect to newly parsed CV page
      router.push(`/cv/${response.data.id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Une erreur est survenue pendant le parsing de votre CV par l'IA.");
      setUploading(false);
    }
  };

  return (
    <div>
      <Navbar />
      <main className="container" style={{ maxWidth: '800px' }}>
        <div style={{ marginBottom: '2rem', marginTop: '1rem' }}>
          <Link href="/cv" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            <ArrowLeft size={16} />
            Retour à mes CVs
          </Link>
          <h1 className="gradient-text" style={{ fontSize: '2.2rem', marginBottom: '0.25rem' }}>Ajouter un CV</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Uploadez votre CV en format PDF pour que l'IA puisse le structurer sémantiquement.</p>
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

        {uploading ? (
          <div className="glass-card" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '5rem 2rem',
            textAlign: 'center',
            gap: '1.5rem'
          }}>
            <Loader2 size={48} className="animate-spin" style={{ color: 'var(--primary)', animation: 'spin 2s linear infinite' }} />
            <div>
              <h3 style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>Analyse de votre CV par l'IA...</h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '450px' }}>
                Cela peut prendre jusqu'à 15 secondes. Notre modèle extrait vos expériences, vos formations et normalise vos compétences clés.
              </p>
            </div>
            {/* Simple CSS animation style inside react for spin */}
            <style jsx global>{`
              @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              style={{
                border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border-color)'}`,
                borderRadius: '16px',
                padding: '4rem 2rem',
                textAlign: 'center',
                background: dragActive ? 'rgba(108, 99, 255, 0.05)' : 'rgba(255, 255, 255, 0.01)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                marginBottom: '2rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '1rem'
              }}
              onClick={() => document.getElementById('file-upload').click()}
            >
              <UploadCloud size={48} style={{ color: dragActive ? 'var(--primary)' : 'var(--text-muted)' }} />
              <div>
                <p style={{ fontWeight: '600', marginBottom: '0.25rem' }}>Glissez-déposez votre CV ici</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>ou cliquez pour parcourir vos fichiers</p>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Uniquement les fichiers PDF (Max. 10Mo)</p>
              <input
                id="file-upload"
                type="file"
                style={{ display: 'none' }}
                accept=".pdf"
                onChange={handleChange}
              />
            </div>

            {file && (
              <div className="glass-card" style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '1rem',
                marginBottom: '2rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <FileText style={{ color: 'var(--primary)' }} />
                  <div>
                    <p style={{ fontWeight: '500', fontSize: '0.95rem' }}>{file.name}</p>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{(file.size / (1024 * 1024)).toFixed(2)} Mo</p>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                >
                  Retirer
                </button>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.85rem' }}
              disabled={!file}
            >
              Lancer l'analyse intelligente
            </button>
          </form>
        )}
      </main>
    </div>
  );
}
