'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    async function loadUserFromLocalStorage() {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await api.get('/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error("Session expirée ou invalide", error);
          logout();
        }
      }
      setLoading(false);
    }
    loadUserFromLocalStorage();
  }, []);

  // Protect client side routes
  useEffect(() => {
    if (!loading) {
      const publicRoutes = ['/auth/login', '/auth/register'];
      const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));

      if (!user && !isPublicRoute) {
        router.push('/auth/login');
      } else if (user && isPublicRoute) {
        router.push('/dashboard');
      }
    }
  }, [user, loading, pathname, router]);

  const login = async (email, password) => {
    setLoading(true);
    try {
      // API expects form URL encoded parameters or standard JSON depending on implementation.
      // Usually OAuth2 password flow expects a form body or JSON. Let's send JSON first, 
      // or standard Form Data as per OAuth2 spec.
      // In FastAPI, OAuth2PasswordRequestForm expects form-data.
      const formData = new URLSearchParams();
      formData.append('username', email); // FastAPI OAuth2 uses 'username' field for email
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        }
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
      router.push('/dashboard');
      return { success: true };
    } catch (error) {
      console.error(error);
      let message = "Erreur de connexion. Veuillez vérifier vos identifiants.";
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle rate limiting errors
        if (error.response?.status === 429) {
          message = "Trop de tentatives de connexion. Réessayez dans 1 minute.";
        } else if (errorData.detail) {
          message = errorData.detail;
        }
      }
      
      // Ensure message is always a string
      if (typeof message !== 'string') {
        message = "Erreur de connexion. Veuillez réessayer.";
      }
      
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password) => {
    setLoading(true);
    try {
      await api.post('/auth/register', { email, password });
      return { success: true };
    } catch (error) {
      console.error(error);
      // Extract user-friendly error message from Pydantic validation errors
      let message = "Une erreur est survenue lors de l'inscription. Veuillez réessayer.";
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle Pydantic validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          // Pydantic validation errors come as array of objects
          const firstError = errorData.detail[0];
          if (firstError.msg) {
            message = firstError.msg;
          } else if (firstError.type === 'value_error') {
            message = firstError.input 
              ? `Valeur invalide pour "${firstError.loc[1]}": ${firstError.msg}`
              : firstError.msg;
          }
        } else if (errorData.detail) {
          // Simple string error
          message = errorData.detail;
        }
      }
      
      // Ensure message is always a string, not an object
      if (typeof message !== 'string') {
        message = "Format de données invalide. Vérifiez vos informations.";
      }
      
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    router.push('/auth/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
