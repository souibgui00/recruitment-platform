import './globals.css';
import { AuthProvider } from '../context/AuthContext';

export const metadata = {
  title: 'Plateforme de Recrutement IA - Stage OneTech',
  description: 'Trouvez les meilleures offres d\'emploi grâce au matching hybride IA sémantique et LLM.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}