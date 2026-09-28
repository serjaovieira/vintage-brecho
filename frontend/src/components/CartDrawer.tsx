import React, { useEffect } from 'react';
import { X, Trash2, ShoppingBag, Truck, QrCode, Sparkles, ArrowRight } from 'lucide-react';
import { Product } from '../services/api';

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  cart: Product[];
  onRemoveFromCart: (productId: number) => void;
  onCheckout: () => void;
}

export const CartDrawer: React.FC<CartDrawerProps> = ({
  isOpen,
  onClose,
  cart,
  onRemoveFromCart,
  onCheckout,
}) => {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const shippingCost = 15.0;
  const subtotal = cart.reduce((acc, p) => acc + Number(p.price), 0);
  const total = subtotal > 0 ? subtotal + shippingCost : 0;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden animate-fade-in">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-vintage-wood/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-vintage-cream border-l border-vintage-sage/30 shadow-2xl flex flex-col justify-between overflow-hidden">
          {/* Drawer Header */}
          <div className="sticky top-0 z-10 bg-vintage-cream px-6 py-5 border-b border-vintage-sage/20 flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-vintage-sage/15 text-vintage-sage">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-serif text-lg font-bold text-vintage-wood">Sua Sacola</h3>
                <span className="text-xs text-vintage-text/70 block">
                  {cart.length === 1 ? '1 peça única' : `${cart.length} peças únicas`}
                </span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-vintage-sage/15 text-vintage-wood/80 hover:text-vintage-wood transition-colors bg-white/60 shadow-xs"
              aria-label="Fechar sacola"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Content Body */}
          <div className="grow overflow-y-auto p-6 space-y-4">
            {cart.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center py-16 px-4 space-y-4">
                <div className="w-20 h-20 rounded-full bg-vintage-sage/10 text-vintage-sage flex items-center justify-center">
                  <ShoppingBag className="w-10 h-10 stroke-1" />
                </div>
                <h4 className="font-serif text-xl font-bold text-vintage-wood">
                  Sua sacola está vazia
                </h4>
                <p className="text-xs sm:text-sm text-vintage-text/75 max-w-xs leading-relaxed">
                  Explore nosso catálogo vintage com peças femininas exclusivas 1-of-1 e adicione suas favoritas!
                </p>
                <button
                  onClick={onClose}
                  className="mt-4 px-6 py-3 rounded-2xl bg-vintage-wood text-white font-bold text-xs uppercase tracking-wider hover:bg-vintage-wood/90 transition-all shadow-sm"
                >
                  Explorar Vitrine
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-vintage-sage/10 border border-vintage-sage/25 rounded-2xl p-3 text-xs text-vintage-wood flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-vintage-terracotta shrink-0" />
                  <span>
                    Peças 1-of-1: a reserva exclusiva de 10 min inicia ao avançar para o checkout.
                  </span>
                </div>

                <div className="divide-y divide-vintage-sage/15 space-y-3 pt-1">
                  {cart.map((item) => (
                    <div
                      key={item.id}
                      className="pt-3 first:pt-0 flex items-center gap-3.5 bg-white p-3.5 rounded-2xl border border-vintage-sage/20 shadow-xs"
                    >
                      <img
                        src={item.image_url}
                        alt={item.title}
                        className="w-16 h-20 rounded-xl object-cover border border-vintage-sage/30 shrink-0"
                      />

                      <div className="grow min-w-0">
                        <span className="text-[10px] font-bold text-vintage-sage uppercase tracking-wider block">
                          {item.category}
                        </span>
                        <h4 className="font-serif font-bold text-sm text-vintage-wood truncate">
                          {item.title}
                        </h4>
                        <span className="text-xs text-vintage-text/70 block mt-0.5">
                          Tamanho: <strong className="text-vintage-wood">{item.size}</strong>
                        </span>
                        <span className="font-serif text-sm font-bold text-vintage-terracotta block mt-1">
                          R$ {Number(item.price).toFixed(2)}
                        </span>
                      </div>

                      <button
                        onClick={() => onRemoveFromCart(item.id)}
                        className="p-2 text-vintage-wood/50 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors shrink-0"
                        title="Remover peça da sacola"
                        aria-label={`Remover ${item.title}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Drawer Footer / Checkout Summary */}
          {cart.length > 0 && (
            <div className="sticky bottom-0 bg-white p-6 border-t border-vintage-sage/20 space-y-4 shadow-lg shrink-0">
              <div className="space-y-2 text-xs text-vintage-text/80">
                <div className="flex justify-between">
                  <span>Subtotal das peças ({cart.length})</span>
                  <span className="font-bold text-vintage-wood">R$ {subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center text-vintage-sage font-medium">
                  <span className="flex items-center gap-1.5">
                    <Truck className="w-3.5 h-3.5" />
                    <span>Frete Fixo (Todo o Brasil)</span>
                  </span>
                  <span>R$ {shippingCost.toFixed(2)}</span>
                </div>
                <div className="pt-2 border-t border-vintage-sage/20 flex justify-between items-baseline">
                  <span className="font-serif text-base font-bold text-vintage-wood">Total Consolidado</span>
                  <span className="font-serif text-2xl font-extrabold text-vintage-terracotta">
                    R$ {total.toFixed(2)}
                  </span>
                </div>
              </div>

              <button
                onClick={() => {
                  onClose();
                  onCheckout();
                }}
                className="w-full py-4 px-6 rounded-2xl bg-vintage-terracotta hover:bg-vintage-terracotta-dark text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 transform active:scale-98"
              >
                <QrCode className="w-5 h-5" />
                <span>Finalizar Pedido com PIX</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
