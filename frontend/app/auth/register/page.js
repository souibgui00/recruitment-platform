'use client';

import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const { register, loading } = useAuth();
  const router = useRouter();

  // Password strength validation
  const getPasswordStrength = (pwd) => {
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (pwd.length >= 12) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/[a-z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength++;
    return strength;
  };

  const passwordStrength = getPasswordStrength(password);
  const getStrengthColor = (strength) => {
    if (strength <= 2) return '#ef4444'; // rouge
    if (strength <= 4) return '#f59e0b'; // orange
    return '#10b981'; // vert
  };

  const getStrengthLabel = (strength) => {
    if (strength <= 2) return 'Faible';
    if (strength <= 4) return 'Moyen';
    return 'Fort';
  };

  // Password requirements checklist
  const passwordRequirements = [
    { id: 'length', label: 'Au moins 8 caractères', check: password.length >= 8 },
    { id: 'uppercase', label: 'Au moins une majuscule (A-Z)', check: /[A-Z]/.test(password) },
    { id: 'lowercase', label: 'Au moins une minuscule (a-z)', check: /[a-z]/.test(password) },
    { id: 'number', label: 'Au moins un chiffre (0-9)', check: /\d/.test(password) },
    { id: 'special', label: 'Au moins un caractère spécial (!@#$%^&*(),.?":{}|<>)', check: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
  ];

  // Email validation
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  const isEmailValid = emailRegex.test(email);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!isEmailValid) {
      setErrorMsg("Veuillez entrer une adresse email valide.");
      return;
    }

    // Check all password requirements are met
    const allRequirementsMet = passwordRequirements.every(req => req.check);
    if (!allRequirementsMet) {
      setErrorMsg("Votre mot de passe ne respecte pas tous les critères de sécurité requis.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg("Les mots de passe ne correspondent pas.");
      return;
    }

    const result = await register(email, password);
    if (result.success) {
      setSuccessMsg("Compte créé avec succès ! Redirection vers la page de connexion...");
      setTimeout(() => {
        router.push('/auth/login');
      }, 2000);
    } else {
      setErrorMsg(result.error);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      padding: '1.5rem',
      background: 'radial-gradient(circle at center, #131224 0%, #0b0a16 100%)'
    }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '420px', padding: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 className="gradient-text" style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Inscription</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Rejoignez la plateforme et trouvez l'offre parfaite
          </p>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--error)',
            color: 'var(--error)',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            fontSize: '0.9rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
              ⚠️ Erreur lors de l'inscription
            </div>
            <div>{errorMsg}</div>
          </div>
        )}

        {successMsg && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid var(--success)',
            color: 'var(--success)',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            fontSize: '0.9rem',
            marginBottom: '1.5rem'
          }}>
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Adresse Email
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                *
              </span>
            </label>
            <input
              type="email"
              id="email"
              className="form-input"
              placeholder="nom@exemple.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                borderColor: email && !isEmailValid ? 'var(--error)' : undefined
              }}
            />
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
              Ex: jean.dupont@email.com
            </p>
            {email && !isEmailValid && (
              <p style={{ color: 'var(--error)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Format d'email invalide
              </p>
            )}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Mot de passe
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                *
              </span>
            </label>
            <input
              type="password"
              id="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            
            {/* Password strength indicator */}
            {password && (
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  marginBottom: '0.25rem'
                }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Force du mot de passe
                  </span>
                  <span style={{ 
                    fontSize: '0.8rem', 
                    fontWeight: '600',
                    color: getStrengthColor(passwordStrength)
                  }}>
                    {getStrengthLabel(passwordStrength)}
                  </span>
                </div>
                <div style={{ 
                  height: '4px', 
                  background: 'rgba(255,255,255,0.1)', 
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    height: '100%', 
                    width: `${(passwordStrength / 6) * 100}%`,
                    background: getStrengthColor(passwordStrength),
                    transition: 'width 0.3s ease, background 0.3s ease'
                  }} />
                </div>
              </div>
            )}

            {/* Password requirements checklist */}
            {password && (
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: '600' }}>
                  Critères de sécurité :
                </p>
                {passwordRequirements.map((req) => (
                  <div key={req.id} style={{ display: 'flex', alignItems: 'center', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                    <span style={{ 
                      marginRight: '0.5rem', 
                      color: req.check ? 'var(--success)' : 'var(--text-secondary)',
                      fontSize: '0.9rem'
                    }}>
                      {req.check ? '✓' : '○'}
                    </span>
                    <span style={{ color: req.check ? 'var(--success)' : 'var(--text-secondary)' }}>
                      {req.label}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: '2rem' }}>
            <label className="form-label" htmlFor="confirmPassword">
              Confirmer le mot de passe
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                *
              </span>
            </label>
            <input
              type="password"
              id="confirmPassword"
              className="form-input"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={{
                borderColor: confirmPassword && confirmPassword !== password ? 'var(--error)' : 
                          confirmPassword && confirmPassword === password ? 'var(--success)' : undefined
              }}
            />
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
              Doit être identique au mot de passe ci-dessus
            </p>
            {confirmPassword && confirmPassword !== password && (
              <p style={{ color: 'var(--error)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Les mots de passe ne correspondent pas
              </p>
            )}
            {confirmPassword && confirmPassword === password && (
              <p style={{ color: 'var(--success)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                ✓ Les mots de passe correspondent
              </p>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.85rem' }}
            disabled={loading || !isEmailValid || !passwordRequirements.every(req => req.check) || !confirmPassword || confirmPassword !== password}
          >
            {loading ? 'Inscription...' : "S'inscrire"}
          </button>
          
          {!isEmailValid && email && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '1rem', textAlign: 'center' }}>
              Veuillez corriger l'email avant de continuer
            </p>
          )}
          {email && isEmailValid && !passwordRequirements.every(req => req.check) && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '1rem', textAlign: 'center' }}>
              Veuillez respecter tous les critères de sécurité du mot de passe
            </p>
          )}
          {email && isEmailValid && passwordRequirements.every(req => req.check) && confirmPassword && confirmPassword !== password && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '1rem', textAlign: 'center' }}>
              Les mots de passe doivent correspondre
            </p>
          )}
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Déjà inscrit ? </span>
          <Link href="/auth/login" style={{ fontWeight: '600' }}>Se connecter</Link>
        </div>
      </div>
    </div>
  );
}
