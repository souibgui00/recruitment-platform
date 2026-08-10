'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileText, Briefcase, Sparkles, LogOut, User as UserIcon, Send, Bell } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  const navItems = [
    { name: 'Tableau de bord', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Mon CV', path: '/cv', icon: FileText },
    { name: 'Offres d\'emploi', path: '/offers', icon: Briefcase },
    { name: 'Matching IA', path: '/matching', icon: Sparkles },
    { name: 'Candidatures', path: '/applications', icon: Send },
    { name: 'Notifications', path: '/notifications', icon: Bell },
  ];

  return (
    <nav style={{
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(10px)',
    }}>
      <div className="container" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem 1.5rem',
      }}>
        {/* Logo / Brand */}
        <Link href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="gradient-text" style={{
            fontSize: '1.4rem',
            fontWeight: 800,
            letterSpacing: '-0.03em',
          }}>
            Recrute.IA
          </span>
        </Link>

        {/* Desktop Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                href={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  fontSize: '0.925rem',
                  fontWeight: 500,
                  color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  background: isActive ? 'var(--primary-glow)' : 'transparent',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <Icon size={16} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>

        {/* User profile & logout */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {user && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.9rem',
              color: 'var(--text-primary)',
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '0.4rem 0.8rem',
              borderRadius: '20px',
              border: '1px solid var(--border-color)',
            }}>
              <UserIcon size={14} className="text-secondary" />
              <span>{user.email.split('@')[0]}</span>
            </div>
          )}
          
          <button
            onClick={logout}
            className="btn btn-secondary"
            style={{
              padding: '0.4rem 0.8rem',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <LogOut size={14} />
            <span>Quitter</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
