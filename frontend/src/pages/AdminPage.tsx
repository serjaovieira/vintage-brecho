import React, { useState, useEffect } from 'react';
import {
  Camera,
  Upload,
  PackagePlus,
  Truck,
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles,
  MessageCircle,
  RefreshCw,
  Tag,
} from 'lucide-react';
import { api, AdminOrder } from '../services/api';
import { compressImage, uploadToSupabaseStorage, CompressionResult } from '../services/imageCompression';

const PRESET_SIZES = ['PP', 'P', 'M', 'G', 'GG', '36', '38', '40', '42', '44', 'Único'];

export const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'novo' | 'despacho'>('novo');

  // Product Form State
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Vestidos');
  const [customCategory, setCustomCategory] = useState('');
  const [isCustomCategory, setIsCustomCategory] = useState(false);
  const [categoriesList, setCategoriesList] = useState<string[]>([]);
  const [size, setSize] = useState('M');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');

  // Image & Compression State
  const [compressionResult, setCompressionResult] = useState<CompressionResult | null>(null);
  const [isCompressing, setIsCompressing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Orders State
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);

  // Load existing categories
  useEffect(() => {
    const fetchCats = async () => {
      try {
        const cats = await api.getCategories();
        if (cats.length > 0) {
          setCategoriesList(cats);
          if (!category) setCategory(cats[0]);
        } else {
          setCategoriesList(['Vestidos', 'Blusas', 'Casacos & Jaquetas', 'Calças & Saias', 'Acessórios']);
        }
      } catch (e) {
        console.warn('Erro ao carregar categorias:', e);
        setCategoriesList(['Vestidos', 'Blusas', 'Casacos & Jaquetas', 'Calças & Saias', 'Acessórios']);
      }
    };
    fetchCats();
  }, [category]);

  // Load orders when switching to despacho tab
  const loadOrders = async () => {
    setIsLoadingOrders(true);
    try {
      const data = await api.getAdminOrders();
      setOrders(data);
    } catch (err) {
      console.warn('Erro ao buscar pedidos:', err);
    } finally {
      setIsLoadingOrders(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'despacho') {
      loadOrders();
    }
  }, [activeTab]);

  // Handle Photo Capture or Upload
  const handleImageFile = async (file: File) => {
    setIsCompressing(true);
    setErrorMessage(null);
    try {
      const result = await compressImage(file, 1200, 0.8);
      setCompressionResult(result);
    } catch (err: unknown) {
      console.error('Falha na compressão da imagem:', err);
      setErrorMessage('Erro ao comprimir imagem. Tente tirar outra foto.');
    } finally {
      setIsCompressing(false);
    }
  };

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageFile(file);
    }
  };

  const handleCategorySelect = (value: string) => {
    if (value === '__custom__') {
      setIsCustomCategory(true);
      setCategory('');
    } else {
      setIsCustomCategory(false);
      setCategory(value);
    }
  };

  // Submit Product
  const handleSubmitProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!compressionResult) {
      setErrorMessage('Por favor, tire ou selecione a foto da peça.');
      return;
    }

    const finalCategory = isCustomCategory ? customCategory.trim() : category;
    if (!finalCategory) {
      setErrorMessage('Por favor, defina a categoria da peça.');
      return;
    }

    const parsedPrice = parseFloat(price.replace(',', '.'));
    if (isNaN(parsedPrice) || parsedPrice <= 0) {
      setErrorMessage('Por favor, insira um preço válido maior que zero.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      // 1. Upload compressed photo to Supabase Storage
      const publicUrl = await uploadToSupabaseStorage(
        compressionResult.blob,
        `peca_${Date.now()}.jpg`
      );

      // 2. Call backend to create product
      await api.createProduct({
        title,
        category: finalCategory,
        description,
        size,
        price: parsedPrice,
        image_url: publicUrl,
      });

      // 3. Reset form and notify
      setSuccessToast(`Peça "${title}" cadastrada com sucesso na vitrine!`);
      setTitle('');
      setPrice('');
      setDescription('');
      setCompressionResult(null);
      setCustomCategory('');
      setIsCustomCategory(false);

      // Update local categories list
      if (!categoriesList.includes(finalCategory)) {
        setCategoriesList((prev) => [...prev, finalCategory]);
      }

      setTimeout(() => setSuccessToast(null), 5000);
    } catch (err: unknown) {
      console.error('Erro ao cadastrar peça:', err);
      setErrorMessage('Falha ao cadastrar a peça. Verifique os dados e tente novamente.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="min-h-screen py-8 px-4 sm:px-6 max-w-xl mx-auto space-y-6">
      {/* Title & Tabs */}
      <div className="text-center space-y-2">
        <span className="text-xs font-bold text-vintage-sage uppercase tracking-wider">
          Painel do Lojista
        </span>
        <h1 className="font-serif text-2xl sm:text-3xl font-extrabold text-vintage-wood">
          Gestão Mobile do Brechó
        </h1>
      </div>

      {/* Segmented Control Tabs */}
      <div className="bg-vintage-cream-light p-1 rounded-2xl border border-vintage-sage/30 grid grid-cols-2 gap-1 shadow-xs">
        <button
          onClick={() => setActiveTab('novo')}
          className={`py-3 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all ${
            activeTab === 'novo'
              ? 'bg-vintage-wood text-white shadow-sm'
              : 'text-vintage-wood/70 hover:text-vintage-wood'
          }`}
        >
          <PackagePlus className="w-4 h-4" />
          <span>Nova Peça 1-of-1</span>
        </button>

        <button
          onClick={() => setActiveTab('despacho')}
          className={`py-3 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all ${
            activeTab === 'despacho'
              ? 'bg-vintage-wood text-white shadow-sm'
              : 'text-vintage-wood/70 hover:text-vintage-wood'
          }`}
        >
          <Truck className="w-4 h-4" />
          <span>Pedidos & Despacho</span>
        </button>
      </div>

      {/* Success Toast */}
      {successToast && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs sm:text-sm flex items-center gap-3 animate-fade-in shadow-sm">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs sm:text-sm flex items-start gap-3 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* TAB 1: CADASTRO RÁPIDO DE PRODUTO */}
      {activeTab === 'novo' && (
        <form onSubmit={handleSubmitProduct} className="space-y-6">
          {/* CAMERA CAPTURE SECTION */}
          <div className="bg-white rounded-3xl p-5 sm:p-6 border border-vintage-sage/30 shadow-vintage-soft space-y-4">
            <label className="block text-xs font-bold text-vintage-wood uppercase tracking-wider">
              1. Fotografia da Peça
            </label>

            {/* Native Mobile Camera Input */}
            <input
              type="file"
              accept="image/*"
              capture="environment"
              id="camera-input"
              className="hidden"
              onChange={onFileInputChange}
            />

            {/* Gallery Upload Input */}
            <input
              type="file"
              accept="image/*"
              id="gallery-input"
              className="hidden"
              onChange={onFileInputChange}
            />

            {/* Camera Button */}
            <label
              htmlFor="camera-input"
              className="w-full flex items-center justify-center gap-2 bg-vintage-sage hover:bg-vintage-sage-dark text-white py-4 px-6 rounded-2xl font-bold cursor-pointer shadow-md transition-all active:scale-98"
            >
              <Camera className="w-6 h-6" />
              <span className="text-sm sm:text-base">📸 Tirar Foto da Peça</span>
            </label>

            <div className="flex items-center justify-center gap-2">
              <label
                htmlFor="gallery-input"
                className="text-xs text-vintage-wood/70 hover:text-vintage-terracotta cursor-pointer underline flex items-center gap-1"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Ou selecionar da galeria de fotos</span>
              </label>
            </div>

            {/* Loading Compression Indicator */}
            {isCompressing && (
              <div className="py-4 text-center text-xs text-vintage-sage flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Otimizando imagem no navegador (Canvas)...</span>
              </div>
            )}

            {/* Image Preview & Compression Metrics */}
            {compressionResult && (
              <div className="mt-4 pt-4 border-t border-vintage-sage/20 space-y-3">
                <div className="relative w-full aspect-4/3 rounded-2xl overflow-hidden bg-vintage-cream-light border border-vintage-sage/30 shadow-inner">
                  <img
                    src={compressionResult.dataUrl}
                    alt="Pré-visualização da Peça"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-2 left-2 bg-black/70 backdrop-blur-xs text-white text-[11px] px-2.5 py-1 rounded-lg">
                    {compressionResult.width}x{compressionResult.height}px
                  </div>
                </div>

                {/* Compression Metrics Tag */}
                <div className="p-3 bg-vintage-sage-light rounded-xl border border-vintage-sage/30 text-xs text-vintage-wood space-y-1">
                  <div className="flex items-center justify-between font-semibold">
                    <span>Compressão Canvas:</span>
                    <span className="text-emerald-700">
                      {(
                        ((compressionResult.originalSizeKB - compressionResult.compressedSizeKB) /
                          compressionResult.originalSizeKB) *
                        100
                      ).toFixed(0)}
                      % reduzido
                    </span>
                  </div>
                  <div className="text-[11px] text-vintage-text/75 flex justify-between">
                    <span>Original: {compressionResult.originalSizeKB} KB</span>
                    <span>Final para Upload: ~{compressionResult.compressedSizeKB} KB</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* PRODUCT DETAILS SECTION */}
          <div className="bg-white rounded-3xl p-5 sm:p-6 border border-vintage-sage/30 shadow-vintage-soft space-y-4">
            <label className="block text-xs font-bold text-vintage-wood uppercase tracking-wider">
              2. Informações da Peça
            </label>

            <div>
              <label className="block text-xs font-semibold text-vintage-text mb-1">
                Nome da Peça *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ex: Blazer Vintage Linho Italiano"
                className="w-full px-4 py-3 rounded-xl border border-vintage-sage/40 bg-vintage-cream-light/40 text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
              />
            </div>

            {/* Smart Category Dropdown + Dynamic Custom Category */}
            <div>
              <label className="block text-xs font-semibold text-vintage-text mb-1 flex items-center justify-between">
                <span>Categoria *</span>
                <span className="text-[11px] text-vintage-sage">Atualiza a vitrine</span>
              </label>

              <select
                value={isCustomCategory ? '__custom__' : category}
                onChange={(e) => handleCategorySelect(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-vintage-sage/40 bg-vintage-cream-light/40 text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
              >
                {categoriesList.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
                <option value="__custom__">+ Outra Categoria...</option>
              </select>

              {/* Free Text Input for New Category */}
              {isCustomCategory && (
                <div className="mt-2 animate-fade-in space-y-1">
                  <div className="flex items-center gap-1.5 text-xs text-vintage-wood font-medium">
                    <Tag className="w-3.5 h-3.5 text-vintage-terracotta" />
                    <span>Digite o nome da nova categoria:</span>
                  </div>
                  <input
                    type="text"
                    required
                    value={customCategory}
                    onChange={(e) => setCustomCategory(e.target.value)}
                    placeholder="Ex: Coletes & Trench Coats"
                    className="w-full px-4 py-2.5 rounded-xl border border-vintage-terracotta/60 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                  />
                </div>
              )}
            </div>

            {/* Quick Touch Size Selector Chips */}
            <div>
              <label className="block text-xs font-semibold text-vintage-text mb-1.5">
                Tamanho da Peça (Seletor Touch) *
              </label>
              <div className="flex flex-wrap gap-2">
                {PRESET_SIZES.map((sz) => (
                  <button
                    type="button"
                    key={sz}
                    onClick={() => setSize(sz)}
                    className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all border ${
                      size === sz
                        ? 'bg-vintage-sage text-white border-vintage-sage shadow-xs scale-105'
                        : 'bg-vintage-cream-light text-vintage-wood border-vintage-sage/30 hover:border-vintage-sage'
                    }`}
                  >
                    {sz}
                  </button>
                ))}
              </div>
            </div>

            {/* Price (R$) */}
            <div>
              <label className="block text-xs font-semibold text-vintage-text mb-1">
                Preço Unitário (R$) *
              </label>
              <div className="relative">
                <span className="absolute left-4 top-3 text-sm font-bold text-vintage-wood">
                  R$
                </span>
                <input
                  type="text"
                  required
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="89,90"
                  className="w-full pl-12 pr-4 py-3 rounded-xl border border-vintage-sage/40 bg-vintage-cream-light/40 text-sm font-bold text-vintage-terracotta focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                />
              </div>
            </div>

            {/* Measurements & Description */}
            <div>
              <label className="block text-xs font-semibold text-vintage-text mb-1">
                Medidas, Composição e Estado de Conservação
              </label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Busto: 92cm | Cintura: 74cm | Comprimento: 105cm. Tecido: 100% Algodão Puro. Condição excelente."
                className="w-full px-4 py-3 rounded-xl border border-vintage-sage/40 bg-vintage-cream-light/40 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSaving || isCompressing || !compressionResult}
            className="w-full py-4 rounded-2xl bg-vintage-terracotta hover:bg-vintage-terracotta-dark text-white font-bold text-base shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Enviando para Supabase e Publicando...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Publicar Peça na Vitrine</span>
              </>
            )}
          </button>
        </form>
      )}

      {/* TAB 2: PEDIDOS & DESPACHO */}
      {activeTab === 'despacho' && (
        <section aria-label="Pedidos e Despacho" className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-vintage-wood">
              {orders.length} pedidos registrados
            </span>
            <button
              onClick={loadOrders}
              disabled={isLoadingOrders}
              className="p-2 rounded-xl border border-vintage-sage/30 hover:bg-white text-vintage-wood text-xs flex items-center gap-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingOrders ? 'animate-spin' : ''}`} />
              <span>Atualizar</span>
            </button>
          </div>

          {isLoadingOrders && (
            <div className="py-12 text-center text-vintage-sage flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-xs">Carregando pedidos de despacho...</span>
            </div>
          )}

          {!isLoadingOrders && orders.length === 0 && (
            <div className="bg-white rounded-3xl p-8 border border-vintage-sage/30 text-center space-y-3">
              <Truck className="w-10 h-10 mx-auto text-vintage-sage/50" />
              <h3 className="font-serif font-bold text-vintage-wood">Nenhum pedido aprovado</h3>
              <p className="text-xs text-vintage-text/70">
                Assim que um cliente pagar o PIX, os dados de entrega e WhatsApp aparecerão aqui para etiquetagem.
              </p>
            </div>
          )}

          {!isLoadingOrders && orders.length > 0 && (
            <div className="space-y-4">
              {orders.map((ord) => {
                const cleanPhone = ord.customer_phone?.replace(/\D/g, '') || '';
                const whatsappMessage = encodeURIComponent(
                  `Olá ${ord.customer_name || 'Cliente'}! Confirmamos o pagamento da peça *${ord.product_title}* no Vintage Brechó. Já estamos preparando o seu envio para o endereço: ${ord.customer_address || ''}!`
                );
                const whatsappLink = `https://wa.me/55${cleanPhone}?text=${whatsappMessage}`;

                return (
                  <div
                    key={ord.order_id}
                    className="bg-white rounded-2xl p-5 border border-vintage-sage/30 shadow-vintage-soft space-y-3"
                  >
                    <div className="flex items-start justify-between gap-2 border-b border-vintage-sage/15 pb-2">
                      <div>
                        <span className="text-[10px] font-mono text-vintage-text/60 uppercase block">
                          ID: {ord.order_id.slice(0, 8)}...
                        </span>
                        <h4 className="font-serif font-bold text-sm text-vintage-wood">
                          {ord.product_title}
                        </h4>
                      </div>

                      <span
                        className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase ${
                          ord.payment_status === 'approved'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {ord.payment_status === 'approved' ? 'Pago' : ord.payment_status}
                      </span>
                    </div>

                    <div className="text-xs space-y-1 text-vintage-text">
                      <p>
                        <strong>Cliente:</strong> {ord.customer_name || 'Não informado'}
                      </p>
                      <p>
                        <strong>E-mail:</strong> {ord.customer_email || 'Não informado'}
                      </p>
                      <p>
                        <strong>WhatsApp:</strong> {ord.customer_phone || 'Não informado'}
                      </p>
                      <p className="bg-vintage-cream-light p-2.5 rounded-xl border border-vintage-sage/20 text-vintage-wood text-[11px] leading-relaxed">
                        <strong>Endereço de Envio:</strong> <br />
                        {ord.customer_address || 'Endereço não cadastrado'}
                      </p>
                      <p className="text-right font-serif font-bold text-vintage-terracotta text-sm">
                        Total Recebido: R$ {Number(ord.total_amount).toFixed(2)}
                      </p>
                    </div>

                    {cleanPhone && (
                      <div className="pt-2">
                        <a
                          href={whatsappLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full py-2.5 px-4 rounded-xl bg-[#25D366] hover:bg-[#20ba59] text-white font-bold text-xs flex items-center justify-center gap-2 shadow-xs transition-colors"
                        >
                          <MessageCircle className="w-4 h-4 fill-white" />
                          <span>Chamar Cliente no WhatsApp</span>
                        </a>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}
    </main>
  );
};
