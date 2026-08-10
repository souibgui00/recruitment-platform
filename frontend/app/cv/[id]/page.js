'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../../components/Navbar';
import api from '../../../lib/api';
import Link from 'next/link';
import { useAuth } from '../../../context/AuthContext';
import { 
  ArrowLeft, User, Mail, Phone, Calendar, Briefcase, GraduationCap, 
  CheckCircle, Edit2, Save, X, Link2, DollarSign, Github, MapPin 
} from 'lucide-react';

export default function CVDetailPage({ params }) {
  const { id } = params;
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [cv, setCv] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Edit mode states
  const [isEditing, setIsEditing] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    linkedin_url: '',
    github_url: '',
    salary_expectation: ''
  });

  useEffect(() => {
    async function fetchCVDetails() {
      try {
        const response = await api.get(`/cv/${id}`);
        setCv(response.data);
      } catch (err) {
        console.error(err);
        setError("Impossible de récupérer les détails de ce CV.");
      } finally {
        setLoading(false);
      }
    }
    if (!authLoading && isAuthenticated && id) {
      fetchCVDetails();
    } else if (!authLoading) {
      setLoading(false);
    }
  }, [id, authLoading, isAuthenticated]);

  const startEditing = () => {
    if (cv && cv.personal_info) {
      setFormData({
        full_name: cv.personal_info.full_name || '',
        email: cv.personal_info.email || '',
        phone: cv.personal_info.phone || '',
        location: cv.personal_info.location || '',
        linkedin_url: cv.personal_info.linkedin_url || '',
        github_url: cv.personal_info.github_url || '',
        salary_expectation: cv.personal_info.salary_expectation || ''
      });
      setIsEditing(true);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const savePersonalInfo = async () => {
    setSaveLoading(true);
    try {
      const response = await api.put(`/cv/${id}/personal-info`, formData);
      setCv(prev => ({
        ...prev,
        personal_info: {
          ...prev.personal_info,
          ...response.data
        }
      }));
      setIsEditing(false);
    } catch (err) {
      console.error(err);
      alert("Erreur lors de l'enregistrement des coordonnées.");
    } finally {
      setSaveLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--text-secondary)' }}>
          Chargement du CV analysé...
        </div>
      </div>
    );
  }

  if (error || !cv) {
    return (
      <div>
        <Navbar />
        <div className="container" style={{ maxWidth: '800px', textAlign: 'center', padding: '5rem' }}>
          <p style={{ color: 'var(--error)', marginBottom: '1.5rem' }}>{error || "CV non trouvé."}</p>
          <Link href="/cv" className="btn btn-secondary">
            Retour à la liste
          </Link>
        </div>
      </div>
    );
  }

  // Shortcut helpers for nested data
  const info = cv.personal_info;
  const experiences = cv.experiences || [];
  const educations = cv.educations || [];
  const skills = cv.skills || [];

  return (
    <div>
      <Navbar />
      <main className="container" style={{ maxWidth: '900px' }}>
        <div style={{ marginBottom: '2rem', marginTop: '1rem' }}>
          <Link href="/cv" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.1rem' }}>
            <ArrowLeft size={16} />
            Retour à mes CVs
          </Link>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '0.25rem' }}>
                {info?.full_name || cv.filename || 'CV Parsé'}
              </h1>
              <p style={{ color: 'var(--text-secondary)' }}>
                Fichier d'origine : {cv.filename || 'Inconnu'}
                {cv.status && (
                  <span style={{
                    marginLeft: '1rem',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '20px',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    background: cv.status === 'PARSED' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                    color: cv.status === 'PARSED' ? 'var(--success)' : 'var(--error)'
                  }}>
                    {cv.status}
                  </span>
                )}
              </p>
            </div>
            <Link href={`/matching`} className="btn btn-accent" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>Lancer le Matching IA</span>
            </Link>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>

          {/* Personal Info */}
          <div className="glass-card" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', margin: 0 }}>
                Coordonnées Personnelles
              </h3>
              {info && !isEditing && (
                <button 
                  onClick={startEditing} 
                  className="btn btn-secondary" 
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                >
                  <Edit2 size={14} />
                  Modifier
                </button>
              )}
            </div>

            {info ? (
              isEditing ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Nom Complet</label>
                    <input 
                      type="text" 
                      name="full_name" 
                      value={formData.full_name} 
                      onChange={handleInputChange} 
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Adresse Email</label>
                    <input 
                      type="email" 
                      name="email" 
                      value={formData.email} 
                      onChange={handleInputChange} 
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Téléphone</label>
                    <input 
                      type="text" 
                      name="phone" 
                      value={formData.phone} 
                      onChange={handleInputChange} 
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Localisation</label>
                    <input 
                      type="text" 
                      name="location" 
                      value={formData.location} 
                      onChange={handleInputChange} 
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      <Link2 size={12} /> URL LinkedIn
                    </label>
                    <input 
                      type="url" 
                      name="linkedin_url" 
                      value={formData.linkedin_url} 
                      onChange={handleInputChange} 
                      placeholder="https://linkedin.com/in/nom"
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      <Github size={12} /> URL GitHub / Portfolio
                    </label>
                    <input 
                      type="url" 
                      name="github_url" 
                      value={formData.github_url} 
                      onChange={handleInputChange} 
                      placeholder="https://github.com/nom"
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      <DollarSign size={12} /> Prétentions Salariales
                    </label>
                    <input 
                      type="text" 
                      name="salary_expectation" 
                      value={formData.salary_expectation} 
                      onChange={handleInputChange} 
                      placeholder="e.g. 50 000 EUR / an"
                      style={{ padding: '0.5rem', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
                    <button 
                      onClick={savePersonalInfo} 
                      disabled={saveLoading}
                      className="btn btn-accent" 
                      style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.5rem 1rem' }}
                    >
                      <Save size={14} />
                      {saveLoading ? 'Enregistrement...' : 'Enregistrer'}
                    </button>
                    <button 
                      onClick={() => setIsEditing(false)} 
                      disabled={saveLoading}
                      className="btn btn-secondary" 
                      style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.5rem 1rem' }}
                    >
                      <X size={14} />
                      Annuler
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><User size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Nom Complet</p>
                      <p style={{ fontWeight: '500' }}>{info.full_name || 'Non spécifié'}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><Mail size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Adresse Email</p>
                      <p style={{ fontWeight: '500' }}>{info.email || 'Non spécifiée'}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><Phone size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Téléphone</p>
                      <p style={{ fontWeight: '500' }}>{info.phone || 'Non spécifié'}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><MapPin size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Localisation</p>
                      <p style={{ fontWeight: '500' }}>{info.location || 'Non spécifiée'}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><Link2 size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>LinkedIn</p>
                      <p style={{ fontWeight: '500' }}>
                        {info.linkedin_url ? (
                          <a href={info.linkedin_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
                            Voir le profil
                          </a>
                        ) : 'Non spécifié'}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><Github size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>GitHub / Portfolio</p>
                      <p style={{ fontWeight: '500' }}>
                        {info.github_url ? (
                          <a href={info.github_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
                            Voir le dépôt
                          </a>
                        ) : 'Non spécifié'}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)', display: 'flex' }}><DollarSign size={18} /></div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Prétentions Salariales</p>
                      <p style={{ fontWeight: '500' }}>{info.salary_expectation || 'Non spécifiées'}</p>
                    </div>
                  </div>
                </div>
              )
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                {cv.status === 'PARSED' ? 'Aucune information personnelle extraite.' : 'CV pas encore analysé.'}
              </p>
            )}
          </div>

          {/* Skills */}
          <div className="glass-card">
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
              Compétences Extraites
            </h3>
            {skills.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {skills.map((skill) => (
                  <span key={skill.id} style={{
                    background: 'var(--primary-glow)',
                    color: 'var(--text-primary)',
                    border: '1px solid rgba(108, 99, 255, 0.3)',
                    padding: '0.35rem 0.85rem',
                    borderRadius: '20px',
                    fontSize: '0.85rem',
                    fontWeight: '500',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem'
                  }}>
                    <CheckCircle size={12} style={{ color: 'var(--primary)' }} />
                    {skill.canonical_name}
                  </span>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Aucune compétence détectée.</p>
            )}
          </div>

          {/* Experiences */}
          <div className="glass-card">
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Briefcase size={20} className="text-secondary" />
              Expériences Professionnelles
            </h3>
            {experiences.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {experiences.map((exp) => (
                  <div key={exp.id} style={{ borderLeft: '2px solid var(--primary)', paddingLeft: '1.25rem', position: 'relative' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--primary)', position: 'absolute', left: '-6px', top: '6px' }}></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                      <h4 style={{ fontSize: '1.1rem', fontWeight: '600', margin: 0 }}>
                        {exp.title} <span style={{ color: 'var(--primary)' }}>chez {exp.company}</span>
                      </h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        <Calendar size={14} />
                        <span>
                          {exp.start_date ? new Date(exp.start_date).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' }) : '?'}
                          {' — '}
                          {exp.is_current ? 'Présent' : (exp.end_date ? new Date(exp.end_date).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' }) : 'Présent')}
                        </span>
                      </div>
                    </div>
                    {exp.description && (
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', whiteSpace: 'pre-line' }}>
                        {exp.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Aucune expérience listée.</p>
            )}
          </div>

          {/* Education */}
          <div className="glass-card">
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <GraduationCap size={20} className="text-secondary" />
              Cursus Académique
            </h3>
            {educations.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {educations.map((edu) => (
                  <div key={edu.id} style={{ borderLeft: '2px solid var(--accent)', paddingLeft: '1.25rem', position: 'relative' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent)', position: 'absolute', left: '-6px', top: '6px' }}></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: '0.25rem' }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: '600', margin: 0 }}>
                        {edu.degree}{edu.field ? ` — ${edu.field}` : ''}
                      </h4>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        {edu.end_date ? new Date(edu.end_date).getFullYear() : (edu.start_date ? new Date(edu.start_date).getFullYear() : '?')}
                      </span>
                    </div>
                    <p style={{ color: 'var(--accent)', fontSize: '0.9rem', fontWeight: '500' }}>
                      {edu.institution}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Aucun diplôme listé.</p>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}
