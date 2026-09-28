import React, { useState } from 'react';
import { Eye, QrCode, Sparkles, ShoppingBag, Check } from 'lucide-react';
import { Product } from '../services/api';

interface ProductCardProps {
  product: Product;
  onViewDetails: (product: Product) => void;
  onBuyNow: (product: Product) => void;
  onAddToCart?: (product: Product) => void;
  isInCart?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onViewDetails,
  onBuyNow,
  onAddToCart,
  isInCart = false,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const formattedPrice = Number(product.price).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });

  return (
    <article className="group relative bg-white/90 backdrop-blur-xs rounded-2xl border border-vintage-sage/25 overflow-hidden shadow-vintage-soft hover:shadow-vintage-hover hover:border-vintage-sage/60 transition-all duration-300 flex flex-col justify-between">
      {/* Top Image Container */}
      <div
        onClick={() => onViewDetails(product)}
        className="relative w-full aspect-3/4 overflow-hidden bg-vintage-cream-light cursor-pointer"
      >
        {/* Placeholder / Skeleton while loading */}
        {!imageLoaded && (
          <div className="absolute inset-0 bg-vintage-sage/10 animate-pulse flex items-center justify-center text-vintage-wood/40">
            <Sparkles className="w-8 h-8 opacity-40" />
          </div>
        )}

        <img
          src={product.image_url}
          alt={product.title}
          loading="lazy"
          onLoad={() => setImageLoaded(true)}
          className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out ${
            imageLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* 1-of-1 Exclusivity Badge */}
        <div className="absolute top-3 left-3 bg-vintage-wood/90 backdrop-blur-xs text-vintage-cream text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full shadow-sm flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-vintage-terracotta" />
          <span>Peça 1-of-1</span>
        </div>

        {/* Size Badge */}
        <div className="absolute top-3 right-3 bg-vintage-sage text-white text-xs font-bold px-3 py-1 rounded-full shadow-sm">
          Tam {product.size}
        </div>

        {/* Quick View Overlay on Hover */}
        <div className="absolute inset-0 bg-vintage-wood/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
          <span className="bg-white/95 text-vintage-wood text-xs font-semibold px-4 py-2 rounded-full shadow-md flex items-center gap-1.5 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
            <Eye className="w-3.5 h-3.5 text-vintage-terracotta" />
            Ver Medidas & Detalhes
          </span>
        </div>
      </div>

      {/* Product Content Details */}
      <div className="p-4 sm:p-5 flex flex-col grow justify-between">
        <div>
          <span className="text-[11px] font-semibold text-vintage-sage tracking-wider uppercase block mb-1">
            {product.category}
          </span>

          <h3
            onClick={() => onViewDetails(product)}
            className="font-serif text-lg font-bold text-vintage-wood hover:text-vintage-terracotta transition-colors line-clamp-1 cursor-pointer leading-snug"
            title={product.title}
          >
            {product.title}
          </h3>

          {product.description && (
            <p className="mt-1 text-xs text-vintage-text/75 line-clamp-2 leading-relaxed">
              {product.description}
            </p>
          )}
        </div>

        {/* Price & Action Row */}
        <div className="mt-4 pt-3 border-t border-vintage-sage/15 flex items-center justify-between gap-2">
          <div>
            <span className="text-[10px] text-vintage-text/60 uppercase tracking-wider block">
              Valor da Peça
            </span>
            <span className="font-serif text-xl sm:text-2xl font-bold text-vintage-terracotta">
              {formattedPrice}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {onAddToCart && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToCart(product);
                }}
                className={`p-2 sm:px-3 sm:py-2 rounded-xl border text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  isInCart
                    ? 'bg-vintage-sage/20 border-vintage-sage text-vintage-sage'
                    : 'border-vintage-sage/40 hover:border-vintage-sage bg-white text-vintage-wood hover:bg-vintage-sage/10'
                }`}
                title={isInCart ? 'Peça já está na sacola' : 'Adicionar à Sacola'}
                aria-label={isInCart ? 'Peça já está na sacola' : 'Adicionar à Sacola'}
              >
                {isInCart ? <Check className="w-4 h-4 text-vintage-sage" /> : <ShoppingBag className="w-4 h-4" />}
                <span className="hidden sm:inline">{isInCart ? 'Na Sacola' : 'Sacola'}</span>
              </button>
            )}

            <button
              onClick={() => onBuyNow(product)}
              className="px-3.5 py-2 rounded-xl bg-vintage-terracotta hover:bg-vintage-terracotta-dark text-white text-xs font-bold shadow-sm transition-colors flex items-center gap-1.5"
              title="Comprar com PIX"
            >
              <QrCode className="w-4 h-4" />
              <span>PIX</span>
            </button>
          </div>
        </div>
      </div>
    </article>
  );
};
