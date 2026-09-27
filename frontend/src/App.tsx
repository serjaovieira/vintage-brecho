import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ShowcasePage } from './pages/ShowcasePage';
import { ContactPage } from './pages/ContactPage';
import { AdminPage } from './pages/AdminPage';
import { WhatsAppButton } from './components/WhatsAppButton';
import { Heart, Sparkles, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'vitrine' | 'contato' | 'admin'>('vitrine');

  // Handle URL navigation (support both hash routing and pathname)
  useEffect(() => {
    const handleUrlChange = () => {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();

      if (path.includes('/admin') || hash === '#/admin' || hash === '#admin') {
        setCurrentTab('admin');
      } else if (path.includes('/contato') || hash === '#/contato' || hash === '#contato') {
        setCurrentTab('contato');
      } else {
        setCurrentTab('vitrine');
      }
    };

    handleUrlChange();
    window.addEventListener('popstate', handleUrlChange);
    window.addEventListener('hashchange', handleUrlChange);

    return () => {
      window.removeEventListener('popstate', handleUrlChange);
      window.removeEventListener('hashchange', handleUrlChange);
    };
  }, []);

  const handleTabChange = (tab: 'vitrine' | 'contato' | 'admin') => {
    setCurrentTab(tab);
    if (tab === 'admin') {
      window.history.pushState(null, '', '/admin');
    } else if (tab === 'contato') {
      window.history.pushState(null, '', '/contato');
    } else {
      window.history.pushState(null, '', '/');
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-vintage-cream flex flex-col justify-between selection:bg-vintage-terracotta/20 selection:text-vintage-wood">
      {/* Header */}
      <Header currentTab={currentTab} onTabChange={handleTabChange} />

      {/* Main Content View */}
      <div className="grow">
        {currentTab === 'vitrine' && <ShowcasePage />}
        {currentTab === 'contato' && <ContactPage />}
        {currentTab === 'admin' && <AdminPage />}
      </div>

      {/* Floating WhatsApp Action Button */}
      <WhatsAppButton />

      {/* Footer */}
      <footer className="bg-vintage-wood text-vintage-cream border-t-4 border-vintage-sage mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-8 border-b border-vintage-sage/20 text-xs sm:text-sm">
            {/* Store Bio */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <img
                  src="/logo.jpg"
                  alt="Vintage Brechó"
                  className="w-8 h-8 rounded-full object-cover border border-vintage-sage"
                />
                <h4 className="font-serif font-bold text-lg text-vintage-cream">
                  Vintage Brechó
                </h4>
              </div>
              <p className="text-vintage-cream/70 font-light leading-relaxed">
                Moda feminina circular com curadoria apaixonada por peças exclusivas unitárias (1-of-1).
                Beleza, história e sustentabilidade em cada detalhe.
              </p>
            </div>

            {/* Quick Links */}
            <div className="space-y-2">
              <h5 className="font-serif font-bold text-sm text-vintage-terracotta uppercase tracking-wider">
                Navegação
              </h5>
              <ul className="space-y-1.5 text-vintage-cream/80">
                <li>
                  <button
                    onClick={() => handleTabChange('vitrine')}
                    className="hover:text-vintage-cream hover:underline"
                  >
                    Vitrine de Peças
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleTabChange('contato')}
                    className="hover:text-vintage-cream hover:underline"
                  >
                    Contato & WhatsApp
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleTabChange('admin')}
                    className="hover:text-vintage-cream hover:underline"
                  >
                    Acesso Lojista (Painel Admin)
                  </button>
                </li>
              </ul>
            </div>

            {/* Trust Badges */}
            <div className="space-y-2">
              <h5 className="font-serif font-bold text-sm text-vintage-sage-light uppercase tracking-wider">
                Garantias do Brechó
              </h5>
              <div className="space-y-2 text-vintage-cream/70 text-xs">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-vintage-sage shrink-0" />
                  <span>Pagamentos instantâneos e seguros via PIX</span>
                </div>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-vintage-terracotta shrink-0" />
                  <span>Trava temporária de 10 minutos para compras sem disputa</span>
                </div>
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4 text-vintage-sage shrink-0" />
                  <span>Atendimento carinhoso via WhatsApp (17) 98166-8413</span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-vintage-cream/60 gap-4">
            <p>© {new Date().getFullYear()} Vintage Brechó. Todos os direitos reservados.</p>
            <p className="flex items-center gap-1">
              Desenvolvido com carinho para a moda circular sustentável.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
