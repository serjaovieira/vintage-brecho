import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, RefreshCw, ShoppingBag, Heart, ShieldCheck } from 'lucide-react';
import { api, Product } from '../services/api';
import { CategoryFilter } from '../components/CategoryFilter';
import { ProductCard } from '../components/ProductCard';
import { ProductModal } from '../components/ProductModal';
import { PixCheckoutModal } from '../components/PixCheckoutModal';
import { CelebrationModal } from '../components/CelebrationModal';

export const ShowcasePage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('Todas as Peças');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [checkoutProduct, setCheckoutProduct] = useState<Product | null>(null);
  const [approvedOrder, setApprovedOrder] = useState<{ orderId: string; product: Product } | null>(
    null
  );

  // Fetch categories
  const loadCategories = useCallback(async () => {
    try {
      const cats = await api.getCategories();
      setCategories(cats);
    } catch (err) {
      console.warn('Erro ao carregar categorias dinâmicas:', err);
    }
  }, []);

  // Fetch products
  const loadProducts = useCallback(
    async (showSpinner = true) => {
      if (showSpinner) setIsLoading(true);
      setError(null);
      try {
        const data = await api.getProducts(selectedCategory);
        setProducts(data);
      } catch (err: unknown) {
        console.error('Erro ao buscar produtos:', err);
        setError('Não foi possível carregar as peças da vitrine. Verifique a conexão com o servidor.');
      } finally {
        if (showSpinner) setIsLoading(false);
      }
    },
    [selectedCategory]
  );

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadProducts(true);
  }, [loadProducts]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([loadCategories(), loadProducts(false)]);
    setIsRefreshing(false);
  };

  const handlePaymentApproved = (orderId: string, product: Product) => {
    setCheckoutProduct(null);
    setSelectedProduct(null);
    setApprovedOrder({ orderId, product });
    // Refresh showcase so the sold item disappears immediately
    handleRefresh();
  };

  return (
    <main className="min-h-screen pb-24">
      {/* Hero Vintage Section */}
      <section className="relative overflow-hidden bg-vintage-wood text-vintage-cream py-12 sm:py-16 px-4 sm:px-6 lg:px-8 border-b-4 border-vintage-sage">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#F6F1E7_1px,transparent_1px)] [background-size:16px_16px]" />

        <div className="relative max-w-5xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-vintage-sage/30 text-vintage-sage-light text-xs font-semibold tracking-wider uppercase border border-vintage-sage/40">
            <Sparkles className="w-3.5 h-3.5 text-vintage-terracotta-light" />
            <span>Curadoria Exclusiva • Peças Únicas Unitárias</span>
          </div>

          <h1 className="font-serif text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-vintage-cream leading-tight">
            Moda Feminina Autêntica, <br />
            <span className="text-vintage-terracotta italic font-normal">
              Histórias que Permanecem.
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-sm sm:text-base text-vintage-cream/80 font-light leading-relaxed">
            Cada vestido, casaco e acessório em nosso catálogo é 1-of-1: uma única unidade disponível.
            Ao escolher comprar com PIX, você ganha 10 minutos de reserva exclusiva.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-6 text-xs text-vintage-cream/70 font-medium">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-vintage-sage" /> Reserva Atômica 10 min
            </span>
            <span className="flex items-center gap-1.5">
              <ShoppingBag className="w-4 h-4 text-vintage-sage" /> Frete Fixo R$ 15,00
            </span>
            <span className="flex items-center gap-1.5">
              <Heart className="w-4 h-4 text-vintage-terracotta" /> Peças Higienizadas
            </span>
          </div>
        </div>
      </section>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Dynamic Category Filter & Refresh Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-vintage-sage/20 pb-2">
          <CategoryFilter
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={(cat) => setSelectedCategory(cat)}
            isLoading={isLoading}
          />

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="self-end sm:self-center px-3.5 py-2 rounded-xl border border-vintage-sage/30 hover:border-vintage-sage bg-white text-xs font-medium text-vintage-wood flex items-center gap-1.5 transition-colors shadow-xs"
            title="Atualizar Vitrine"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>

        {/* Loading Skeleton Grid */}
        {isLoading && (
          <div className="mt-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
              <div
                key={n}
                className="bg-white/80 rounded-2xl p-4 border border-vintage-sage/20 animate-pulse space-y-3"
              >
                <div className="w-full aspect-3/4 bg-vintage-sage/10 rounded-xl" />
                <div className="h-4 bg-vintage-sage/15 rounded-md w-3/4" />
                <div className="h-3 bg-vintage-sage/10 rounded-md w-1/2" />
                <div className="h-6 bg-vintage-terracotta/20 rounded-md w-1/3 pt-2" />
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <div className="mt-12 text-center py-12 px-4 bg-white/70 rounded-3xl border border-rose-200 max-w-xl mx-auto space-y-4">
            <p className="text-sm text-rose-800 font-medium">{error}</p>
            <button
              onClick={() => loadProducts(true)}
              className="px-5 py-2.5 rounded-xl bg-vintage-wood text-white text-xs font-bold shadow-sm hover:bg-vintage-wood/90 transition-colors"
            >
              Tentar Novamente
            </button>
          </div>
        )}

        {/* Empty Catalog State */}
        {!isLoading && !error && products.length === 0 && (
          <div className="mt-12 text-center py-16 px-4 bg-white/60 rounded-3xl border border-vintage-sage/25 max-w-lg mx-auto space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-vintage-sage/15 flex items-center justify-center text-vintage-sage">
              <ShoppingBag className="w-8 h-8" />
            </div>
            <h3 className="font-serif text-xl font-bold text-vintage-wood">
              Nenhuma peça encontrada
            </h3>
            <p className="text-xs sm:text-sm text-vintage-text/75 leading-relaxed">
              Não há peças disponíveis nesta categoria no momento. As peças vintage exclusivas são
              removidas assim que o pagamento é aprovado.
            </p>
            <button
              onClick={() => setSelectedCategory('Todas as Peças')}
              className="px-4 py-2 rounded-xl bg-vintage-sage text-white text-xs font-bold hover:bg-vintage-sage-dark transition-colors"
            >
              Ver Todas as Peças
            </button>
          </div>
        )}

        {/* Product Grid */}
        {!isLoading && !error && products.length > 0 && (
          <div className="mt-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onViewDetails={(p) => setSelectedProduct(p)}
                onBuyNow={(p) => setCheckoutProduct(p)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onBuyNow={(p) => {
            setSelectedProduct(null);
            setCheckoutProduct(p);
          }}
        />
      )}

      {checkoutProduct && (
        <PixCheckoutModal
          product={checkoutProduct}
          onClose={() => setCheckoutProduct(null)}
          onPaymentApproved={handlePaymentApproved}
        />
      )}

      {approvedOrder && (
        <CelebrationModal
          orderId={approvedOrder.orderId}
          product={approvedOrder.product}
          onClose={() => setApprovedOrder(null)}
        />
      )}
    </main>
  );
};
