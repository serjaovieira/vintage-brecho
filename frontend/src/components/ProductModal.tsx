import React, { useEffect } from 'react';
import { X, QrCode, Truck, Sparkles, CheckCircle, Ruler } from 'lucide-react';
import { Product } from '../services/api';

interface ProductModalProps {
  product: Product | null;
  onClose: () => void;
  onBuyNow: (product: Product) => void;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  product,
  onClose,
  onBuyNow,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!product) return null;

  const formattedPrice = Number(product.price).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-vintage-wood/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 animate-fade-in">
      <div
        className="relative bg-vintage-cream w-full max-w-3xl rounded-3xl border border-vintage-sage/30 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col md:flex-row"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 rounded-full bg-white/80 hover:bg-white text-vintage-wood transition-colors shadow-sm"
          aria-label="Fechar modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Product Image Column */}
        <div className="w-full md:w-1/2 bg-vintage-cream-light relative flex items-center justify-center overflow-hidden">
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-72 md:h-full object-cover"
          />
          <div className="absolute top-4 left-4 bg-vintage-wood/90 text-vintage-cream text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full flex items-center gap-1.5 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-vintage-terracotta" />
            Peça Única 1-of-1
          </div>
          <div className="absolute bottom-4 left-4 bg-vintage-sage text-white text-xs font-bold px-3 py-1 rounded-full shadow-sm">
            Tamanho {product.size}
          </div>
        </div>

        {/* Product Details Column */}
        <div className="w-full md:w-1/2 p-6 sm:p-8 flex flex-col justify-between overflow-y-auto">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-vintage-sage tracking-widest uppercase">
                {product.category}
              </span>
            </div>

            <h2 className="font-serif text-2xl sm:text-3xl font-bold text-vintage-wood leading-tight">
              {product.title}
            </h2>

            {/* Price Row */}
            <div className="mt-3 flex items-baseline gap-3">
              <span className="font-serif text-3xl font-extrabold text-vintage-terracotta">
                {formattedPrice}
              </span>
              <span className="text-xs text-vintage-text/60">
                + R$ 15,00 de envio fixo
              </span>
            </div>

            {/* Description & Specs */}
            <div className="mt-6 space-y-4 text-sm text-vintage-text leading-relaxed">
              <div className="bg-white/80 rounded-2xl p-4 border border-vintage-sage/20 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-vintage-wood uppercase tracking-wide">
                  <Ruler className="w-4 h-4 text-vintage-terracotta" />
                  <span>Medidas & Especificações</span>
                </div>
                <p className="text-xs sm:text-sm text-vintage-text/90 whitespace-pre-line">
                  {product.description ||
                    'Peça vintage selecionada com curadoria minuciosa. Tecido de alta durabilidade e caimento impecável.'}
                </p>
              </div>

              {/* Guarantees */}
              <div className="space-y-2 text-xs text-vintage-wood/80">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-vintage-sage" />
                  <span>Peça única higienizada e pronta para uso</span>
                </div>
                <div className="flex items-center gap-2">
                  <Truck className="w-4 h-4 text-vintage-sage" />
                  <span>Envio seguro com código de rastreamento</span>
                </div>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-vintage-terracotta" />
                  <span>Trava de 10 minutos assegurada no checkout PIX</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="mt-8 pt-4 border-t border-vintage-sage/20 space-y-2">
            <button
              onClick={() => {
                onClose();
                onBuyNow(product);
              }}
              className="w-full py-4 px-6 rounded-2xl bg-vintage-terracotta hover:bg-vintage-terracotta-dark text-white font-bold text-base shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 transform active:scale-98"
            >
              <QrCode className="w-5 h-5" />
              <span>Comprar Agora com PIX</span>
            </button>
            <p className="text-[11px] text-center text-vintage-text/60">
              Pagamento instantâneo via Mercado Pago • Reserva exclusiva por 10 minutos
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
