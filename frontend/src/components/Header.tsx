import React, { useState } from 'react';
import { ShoppingBag, Sparkles, Phone, ShieldCheck, Menu, X } from 'lucide-react';

interface HeaderProps {
  currentTab: 'vitrine' | 'contato' | 'admin';
  onTabChange: (tab: 'vitrine' | 'contato' | 'admin') => void;
  cartCount?: number;
  onOpenCart?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  cartCount = 0,
  onOpenCart,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNav = (tab: 'vitrine' | 'contato' | 'admin') => {
    onTabChange(tab);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-vintage-cream/95 backdrop-blur-md border-b border-vintage-sage/25 shadow-sm transition-all duration-200">
      {/* Top Banner Notice */}
      <div className="bg-vintage-sage text-white text-xs py-1.5 px-4 text-center tracking-wide font-medium flex items-center justify-center gap-2">
        <Sparkles className="w-3.5 h-3.5 text-vintage-terracotta-light" />
        <span>Todas as peças são únicas (1-of-1) • Frete Fixo R$ 15,00 para todo o Brasil • Pagamento Seguro PIX</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo & Brand Name */}
          <div
            onClick={() => handleNav('vitrine')}
            className="flex items-center gap-3.5 cursor-pointer group"
          >
            <div className="relative w-13 h-13 rounded-full overflow-hidden border-2 border-vintage-sage p-0.5 shadow-sm group-hover:scale-105 transition-transform duration-200">
              <img
                src="/logo.jpg"
                alt="Vintage Brechó"
                className="w-12 h-12 rounded-full object-cover"
              />
            </div>
            <div>
              <span className="font-serif font-bold text-2xl sm:text-3xl text-vintage-wood tracking-tight block leading-tight group-hover:text-vintage-terracotta transition-colors">
                Vintage Brechó
              </span>
              <span className="text-xs text-vintage-sage font-medium tracking-widest uppercase block">
                Moda Feminina & Peças 1-of-1
              </span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 font-medium">
            <button
              onClick={() => handleNav('vitrine')}
              className={`text-sm tracking-wide transition-colors duration-150 relative py-1 ${
                currentTab === 'vitrine'
                  ? 'text-vintage-terracotta font-semibold'
                  : 'text-vintage-text hover:text-vintage-wood'
              }`}
            >
              Vitrine Vintage
              {currentTab === 'vitrine' && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-vintage-terracotta rounded-full" />
              )}
            </button>

            <button
              onClick={() => handleNav('contato')}
              className={`text-sm tracking-wide transition-colors duration-150 relative py-1 flex items-center gap-1.5 ${
                currentTab === 'contato'
                  ? 'text-vintage-terracotta font-semibold'
                  : 'text-vintage-text hover:text-vintage-wood'
              }`}
            >
              <Phone className="w-3.5 h-3.5" />
              Contato
              {currentTab === 'contato' && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-vintage-terracotta rounded-full" />
              )}
            </button>

            <button
              onClick={() => handleNav('admin')}
              className={`text-xs px-3.5 py-1.5 rounded-full border border-vintage-sage/40 transition-all duration-150 flex items-center gap-1.5 ${
                currentTab === 'admin'
                  ? 'bg-vintage-wood text-white shadow-sm'
                  : 'text-vintage-wood hover:bg-vintage-sage/10'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5 text-vintage-sage" />
              Painel Lojista
            </button>

            {/* Sacola Action Button */}
            <button
              onClick={onOpenCart || (() => handleNav('vitrine'))}
              className="relative p-2.5 rounded-full text-vintage-wood hover:bg-vintage-sage/15 transition-colors"
              title="Sacola de Compras"
              aria-label="Sacola de Compras"
            >
              <ShoppingBag className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-vintage-terracotta text-white text-[10px] font-bold rounded-full flex items-center justify-center shadow-sm">
                  {cartCount}
                </span>
              )}
            </button>
          </nav>

          {/* Mobile Menu & Cart Buttons */}
          <div className="flex md:hidden items-center gap-3">
            <button
              onClick={onOpenCart || (() => handleNav('vitrine'))}
              className="relative p-2 rounded-full text-vintage-wood hover:bg-vintage-sage/15 transition-colors"
              aria-label="Sacola"
            >
              <ShoppingBag className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute top-0.5 right-0.5 w-4 h-4 bg-vintage-terracotta text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-vintage-wood hover:bg-vintage-sage/15 transition-colors"
              aria-label="Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-vintage-sage/20 bg-vintage-cream px-4 pt-3 pb-5 space-y-2 shadow-lg animate-fade-in">
          <button
            onClick={() => handleNav('vitrine')}
            className={`w-full text-left px-4 py-2.5 rounded-xl font-medium transition-colors ${
              currentTab === 'vitrine'
                ? 'bg-vintage-terracotta text-white font-semibold'
                : 'text-vintage-text hover:bg-vintage-sage/10'
            }`}
          >
            Vitrine Vintage
          </button>
          <button
            onClick={() => handleNav('contato')}
            className={`w-full text-left px-4 py-2.5 rounded-xl font-medium transition-colors flex items-center gap-2 ${
              currentTab === 'contato'
                ? 'bg-vintage-terracotta text-white font-semibold'
                : 'text-vintage-text hover:bg-vintage-sage/10'
            }`}
          >
            <Phone className="w-4 h-4" />
            Contato
          </button>
          <button
            onClick={() => handleNav('admin')}
            className={`w-full text-left px-4 py-2.5 rounded-xl font-medium transition-colors flex items-center gap-2 ${
              currentTab === 'admin'
                ? 'bg-vintage-wood text-white font-semibold'
                : 'text-vintage-wood hover:bg-vintage-sage/10 border border-vintage-sage/30'
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-vintage-sage" />
            Painel Lojista (Admin)
          </button>
        </div>
      )}
    </header>
  );
};
