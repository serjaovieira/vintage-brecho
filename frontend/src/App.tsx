import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ShowcasePage } from './pages/ShowcasePage';
import { ContactPage } from './pages/ContactPage';
import { AdminPage } from './pages/AdminPage';
import { WhatsAppButton } from './components/WhatsAppButton';
import { CartDrawer } from './components/CartDrawer';
import { PixCheckoutModal } from './components/PixCheckoutModal';
import { CelebrationModal } from './components/CelebrationModal';
import { Product } from './services/api';
import { Heart, Sparkles, ShieldCheck, Lock } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'vitrine' | 'contato' | 'admin'>('vitrine');

  // Carrinho de Compras 1-of-1 persistido no localStorage
  const [cart, setCart] = useState<Product[]>(() => {
    try {
      const saved = localStorage.getItem('vintage_brecho_cart');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [cartCheckoutOpen, setCartCheckoutOpen] = useState(false);
  const [cartApprovedOrder, setCartApprovedOrder] = useState<{ orderId: string; items: Product[] } | null>(null);

  // Sincronizar carrinho com localStorage
  useEffect(() => {
    try {
      localStorage.setItem('vintage_brecho_cart', JSON.stringify(cart));
    } catch (e) {
      console.warn('Erro ao sincronizar carrinho com localStorage:', e);
    }
  }, [cart]);

  const handleAddToCart = (product: Product) => {
    setCart((prev) => {
      // 1-of-1: impede duplicatas da mesma peça
      if (prev.some((p) => p.id === product.id)) return prev;
      return [...prev, product];
    });
    setIsCartOpen(true);
  };

  const handleRemoveFromCart = (productId: number) => {
    setCart((prev) => prev.filter((p) => p.id !== productId));
  };

  const handleClearCart = () => {
    setCart([]);
    try {
      localStorage.removeItem('vintage_brecho_cart');
    } catch {
      // ignore
    }
  };

  const handleCartCheckout = () => {
    setIsCartOpen(false);
    setCartCheckoutOpen(true);
  };

  const handleCartPaymentApproved = (orderId: string, items: Product[]) => {
    setCartCheckoutOpen(false);
    setCartApprovedOrder({ orderId, items });
    handleClearCart();
  };
  
  // Controle de autenticação do Admin
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState<boolean>(() => {
    return sessionStorage.getItem('admin_auth') === 'true';
  });
  const [passwordInput, setPasswordInput] = useState('');
  const [authError, setAuthError] = useState(false);

  // Defina sua senha aqui
  const ADMIN_PASSWORD = 'admin123';

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

  const handleAdminLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordInput === ADMIN_PASSWORD) {
      setIsAdminAuthenticated(true);
      sessionStorage.setItem('admin_auth', 'true');
      setAuthError(false);
      setPasswordInput('');
    } else {
      setAuthError(true);
    }
  };

  const handleAdminLogout = () => {
    setIsAdminAuthenticated(false);
    sessionStorage.removeItem('admin_auth');
    handleTabChange('vitrine');
  };

  return (
    <div className="min-h-screen bg-vintage-cream flex flex-col justify-between selection:bg-vintage-terracotta/20 selection:text-vintage-wood">
      {/* Header */}
      <Header
        currentTab={currentTab}
        onTabChange={handleTabChange}
        cartCount={cart.length}
        onOpenCart={() => setIsCartOpen(true)}
      />

      {/* Main Content View */}
      <div className="grow">
        {currentTab === 'vitrine' && (
          <ShowcasePage
            onAddToCart={handleAddToCart}
            cartProductIds={cart.map((p) => p.id)}
          />
        )}
        {currentTab === 'contato' && <ContactPage />}
        
        {currentTab === 'admin' && (
          !isAdminAuthenticated ? (
            <div className="min-h-[60vh] flex items-center justify-center p-4">
              <form 
                onSubmit={handleAdminLogin} 
                className="bg-white p-8 rounded-2xl shadow-sm border border-vintage-sage/30 max-w-sm w-full space-y-4 text-center"
              >
                <div className="w-12 h-12 bg-vintage-terracotta/10 text-vintage-terracotta rounded-full flex items-center justify-center mx-auto mb-2">
                  <Lock className="w-6 h-6" />
                </div>
                <h3 className="font-serif font-bold text-xl text-vintage-wood">Área Restrita</h3>
                <p className="text-xs text-vintage-wood/60">Digite a senha para acessar o painel de cadastro de peças.</p>
                
                <input 
                  type="password"
                  placeholder="Senha de acesso"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  className="w-full px-4 py-2 text-sm border border-vintage-sage/40 rounded-lg focus:outline-none focus:ring-2 focus:ring-vintage-terracotta bg-vintage-cream/30 text-vintage-wood"
                  autoFocus
                />

                {authError && (
                  <p className="text-xs text-red-500 font-medium">Senha incorreta. Tente novamente.</p>
                )}

                <button 
                  type="submit"
                  className="w-full py-2 bg-vintage-wood text-vintage-cream rounded-lg text-sm font-medium hover:bg-black transition duration-200"
                >
                  Entrar no Painel
                </button>
              </form>
            </div>
          ) : (
            <div>
              <div className="bg-vintage-wood text-vintage-cream/80 px-4 py-2 flex justify-between items-center text-xs">
                <span className="font-mono">Modo Administrador Ativo</span>
                <button 
                  onClick={handleAdminLogout}
                  className="hover:text-vintage-terracotta underline font-medium"
                >
                  Sair do Admin
                </button>
              </div>
              <AdminPage />
            </div>
          )
        )}
      </div>

      {/* Cart Drawer */}
      <CartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cart={cart}
        onRemoveFromCart={handleRemoveFromCart}
        onCheckout={handleCartCheckout}
      />

      {/* Cart Multi-Item PIX Checkout Modal */}
      {cartCheckoutOpen && cart.length > 0 && (
        <PixCheckoutModal
          items={cart}
          onClose={() => setCartCheckoutOpen(false)}
          onPaymentApproved={handleCartPaymentApproved}
        />
      )}

      {/* Cart Approved Order Celebration */}
      {cartApprovedOrder && (
        <CelebrationModal
          orderId={cartApprovedOrder.orderId}
          items={cartApprovedOrder.items}
          onClose={() => setCartApprovedOrder(null)}
        />
      )}

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