import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Copy,
  Check,
  Clock,
  QrCode,
  Truck,
  AlertTriangle,
  Loader2,
  Lock,
  ShoppingBag,
} from 'lucide-react';
import { api, Product, CheckoutResponse, ApiError } from '../services/api';

interface PixCheckoutModalProps {
  product?: Product | null;
  items?: Product[];
  onClose: () => void;
  onPaymentApproved: (orderId: string, items: Product[]) => void;
}

export const PixCheckoutModal: React.FC<PixCheckoutModalProps> = ({
  product,
  items,
  onClose,
  onPaymentApproved,
}) => {
  // Resolve items to purchase (either from multi-item array or single product)
  const activeItems: Product[] = (items && items.length > 0) 
    ? items 
    : (product ? [product] : []);

  // Step 1: Form; Step 2: PIX Display
  const [step, setStep] = useState<'form' | 'pix'>('form');

  // Customer form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [cep, setCep] = useState('');
  const [address, setAddress] = useState('');
  const [number, setNumber] = useState('');
  const [cityState, setCityState] = useState('');

  // Checkout response & state
  const [checkoutData, setCheckoutData] = useState<CheckoutResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Timer & Toast & Polling
  const [timeLeft, setTimeLeft] = useState<number>(600); // 10 minutes in seconds
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fixed shipping
  const shippingCost = 15.0;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // 10:00 countdown timer
  useEffect(() => {
    if (step !== 'pix' || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [step, timeLeft]);

  // Polling order status every 3000ms
  useEffect(() => {
    if (step !== 'pix' || !checkoutData?.order_id) return;

    const checkStatus = async () => {
      try {
        const statusRes = await api.getOrderStatus(checkoutData.order_id);
        if (statusRes.is_paid || statusRes.payment_status === 'approved') {
          if (pollingRef.current) clearInterval(pollingRef.current);
          onPaymentApproved(checkoutData.order_id, activeItems);
        }
      } catch (err) {
        console.warn('Erro no polling de status:', err);
      }
    };

    pollingRef.current = setInterval(checkStatus, 3000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [step, checkoutData, activeItems, onPaymentApproved]);

  if (activeItems.length === 0) return null;

  const itemsSubtotal = activeItems.reduce((acc, p) => acc + Number(p.price), 0);
  const totalAmount = itemsSubtotal + shippingCost;

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setErrorMessage('Por favor, informe seu e-mail para receber a confirmação.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const fullAddress = `${address}, nº ${number} - CEP: ${cep} - ${cityState}`.trim();

    try {
      const response = await api.checkoutPix({
        product_ids: activeItems.map((p) => p.id),
        product_id: activeItems[0]?.id,
        customer_name: name || 'Cliente Vintage',
        customer_email: email,
        customer_phone: phone,
        customer_address: fullAddress,
      });

      setCheckoutData(response);
      setTimeLeft(response.expires_in || 600);
      setStep('pix');
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 409) {
        setErrorMessage(
          err.detail ||
            'Uma ou mais peças exclusivas já estão reservadas por outro cliente. Caso o pagamento não seja concluído em 10 minutos, elas voltarão a ficar disponíveis.'
        );
      } else if (err instanceof ApiError) {
        setErrorMessage(err.detail || 'Ocorreu um erro ao processar o checkout PIX.');
      } else {
        setErrorMessage('Falha ao conectar com o serviço de pagamento.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyPix = () => {
    if (!checkoutData?.qr_code) return;
    navigator.clipboard.writeText(checkoutData.qr_code);
    setCopied(true);
    setToastMessage('Chave PIX copiada com sucesso! Cole no app do seu banco.');
    setTimeout(() => {
      setCopied(false);
      setToastMessage(null);
    }, 4000);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-vintage-wood/75 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 animate-fade-in">
      <div
        className="relative bg-vintage-cream w-full max-w-lg rounded-3xl border border-vintage-sage/40 shadow-2xl max-h-[90dvh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Fixed & Sticky Header with solid opaque background and z-20 */}
        <div className="sticky top-0 z-20 bg-vintage-cream px-6 py-4 border-b border-vintage-sage/20 flex items-center justify-between shadow-xs shrink-0">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-vintage-sage" />
            <h3 className="font-serif text-lg font-bold text-vintage-wood">
              {step === 'form' ? 'Checkout Seguro PIX' : 'Aguardando Pagamento PIX'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full bg-white/80 hover:bg-white text-vintage-wood/80 hover:text-vintage-wood transition-colors shadow-xs"
            aria-label="Fechar modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toast Notification Banner */}
        {toastMessage && (
          <div className="bg-vintage-sage text-white text-xs font-semibold px-4 py-2.5 text-center flex items-center justify-center gap-2 animate-fade-in shadow-inner shrink-0">
            <Check className="w-4 h-4" />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Scrollable Content Body */}
        <div className="p-6 overflow-y-auto grow space-y-6">
          {/* Order Summary Mini Bar */}
          {activeItems.length === 1 ? (
            <div className="bg-white rounded-2xl p-4 border border-vintage-sage/20 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <img
                  src={activeItems[0].image_url}
                  alt={activeItems[0].title}
                  className="w-14 h-14 rounded-xl object-cover border border-vintage-sage/30"
                />
                <div>
                  <h4 className="font-serif font-bold text-sm text-vintage-wood line-clamp-1">
                    {activeItems[0].title}
                  </h4>
                  <span className="text-xs text-vintage-sage font-medium block">
                    Tam {activeItems[0].size} • Peça Única 1-of-1
                  </span>
                  <span className="text-xs text-vintage-text/70 block">
                    Peça: R$ {Number(activeItems[0].price).toFixed(2)} + Frete: R$ {shippingCost.toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[10px] text-vintage-text/60 uppercase block">Total</span>
                <span className="font-serif text-lg font-bold text-vintage-terracotta">
                  R$ {totalAmount.toFixed(2)}
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-4 border border-vintage-sage/20 space-y-3">
              <div className="flex items-center justify-between border-b border-vintage-sage/15 pb-2">
                <div className="flex items-center gap-2">
                  <ShoppingBag className="w-4 h-4 text-vintage-sage" />
                  <span className="font-serif font-bold text-sm text-vintage-wood">
                    Pacote ({activeItems.length} peças exclusivas)
                  </span>
                </div>
                <div className="text-right">
                  <span className="font-serif text-lg font-bold text-vintage-terracotta">
                    R$ {totalAmount.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Thumbnails preview */}
              <div className="max-h-36 overflow-y-auto space-y-2 pr-1 divide-y divide-vintage-sage/10">
                {activeItems.map((it) => (
                  <div key={it.id} className="pt-2 first:pt-0 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <img
                        src={it.image_url}
                        alt={it.title}
                        className="w-9 h-9 rounded-lg object-cover border border-vintage-sage/20 shrink-0"
                      />
                      <div className="truncate">
                        <p className="font-medium text-vintage-wood truncate">{it.title}</p>
                        <span className="text-[10px] text-vintage-sage font-semibold">Tam {it.size}</span>
                      </div>
                    </div>
                    <span className="font-bold text-vintage-wood shrink-0">
                      R$ {Number(it.price).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-vintage-sage/15 flex justify-between text-xs text-vintage-text/70">
                <span>Subtotal ({activeItems.length} peças): R$ {itemsSubtotal.toFixed(2)}</span>
                <span>Frete fixo único: R$ {shippingCost.toFixed(2)}</span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs sm:text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <strong className="block font-bold">Aviso Importante:</strong>
                <span>{errorMessage}</span>
              </div>
            </div>
          )}

          {/* STEP 1: Customer & Delivery Address Form */}
          {step === 'form' && (
            <form onSubmit={handleStartCheckout} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-vintage-wood uppercase tracking-wide mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Maria Eduarda Silva"
                  className="w-full px-4 py-3 rounded-xl border border-vintage-sage/40 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-vintage-wood uppercase tracking-wide mb-1">
                    E-mail (Receber Confirmação) *
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="maria@exemplo.com"
                    className="w-full px-4 py-3 rounded-xl border border-vintage-sage/40 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-vintage-wood uppercase tracking-wide mb-1">
                    WhatsApp / Telefone *
                  </label>
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="(17) 99999-9999"
                    className="w-full px-4 py-3 rounded-xl border border-vintage-sage/40 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                  />
                </div>
              </div>

              {/* Delivery Address Details */}
              <div className="pt-2 border-t border-vintage-sage/15 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-vintage-sage uppercase tracking-wider">
                  <Truck className="w-4 h-4" />
                  <span>Endereço de Entrega (Frete Fixo R$ 15,00)</span>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2">
                    <input
                      type="text"
                      required
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      placeholder="Rua / Avenida e Bairro"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-vintage-sage/40 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                    />
                  </div>
                  <div>
                    <input
                      type="text"
                      required
                      value={number}
                      onChange={(e) => setNumber(e.target.value)}
                      placeholder="Número"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-vintage-sage/40 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    required
                    value={cep}
                    onChange={(e) => setCep(e.target.value)}
                    placeholder="CEP: 00000-000"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-vintage-sage/40 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                  />
                  <input
                    type="text"
                    required
                    value={cityState}
                    onChange={(e) => setCityState(e.target.value)}
                    placeholder="Cidade - UF"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-vintage-sage/40 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-vintage-terracotta/40"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-4 py-4 rounded-2xl bg-vintage-terracotta hover:bg-vintage-terracotta-dark text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Iniciando Trava de 10 min & Gerando PIX...</span>
                  </>
                ) : (
                  <>
                    <QrCode className="w-5 h-5" />
                    <span>Gerar Código PIX e Reservar {activeItems.length > 1 ? `${activeItems.length} Peças` : 'Peça'}</span>
                  </>
                )}
              </button>
            </form>
          )}

          {/* STEP 2: PIX QR Code & Copia e Cola */}
          {step === 'pix' && checkoutData && (
            <div className="space-y-6 text-center animate-fade-in">
              {/* Countdown Timer Bar */}
              <div
                className={`py-3 px-4 rounded-2xl flex items-center justify-center gap-2 border font-medium ${
                  timeLeft < 120
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-vintage-sage/15 text-vintage-wood border-vintage-sage/30'
                }`}
              >
                <Clock className="w-4 h-4 shrink-0 text-vintage-terracotta animate-pulse" />
                <span className="text-xs sm:text-sm">
                  Tempo restante de reserva exclusiva:{' '}
                  <strong className="font-mono text-base font-bold text-vintage-terracotta">
                    {formatTimer(timeLeft)}
                  </strong>
                </span>
              </div>

              {timeLeft === 0 ? (
                <div className="p-4 rounded-2xl bg-red-50 text-red-700 border border-red-200 text-xs">
                  O tempo de reserva exclusiva expirou. As peças voltaram para a vitrine.
                </div>
              ) : (
                <>
                  {/* QR Code Container */}
                  <div className="flex flex-col items-center justify-center">
                    <div className="bg-white p-4 rounded-2xl border-2 border-vintage-sage/30 shadow-md inline-block">
                      {checkoutData.qr_code_base64 ? (
                        <img
                          src={`data:image/png;base64,${checkoutData.qr_code_base64}`}
                          alt="QR Code PIX Mercado Pago"
                          className="w-48 h-48 sm:w-56 sm:h-56 object-contain"
                        />
                      ) : (
                        <div className="w-48 h-48 sm:w-56 sm:h-56 bg-vintage-cream-light flex flex-col items-center justify-center p-4 text-center">
                          <QrCode className="w-12 h-12 text-vintage-sage mb-2" />
                          <span className="text-xs text-vintage-wood">
                            Escaneie o código com o aplicativo do seu banco
                          </span>
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-vintage-text/60 mt-2">
                      Abra o aplicativo do seu banco e aponte a câmera
                    </span>
                  </div>

                  {/* Copia e Cola Key Box */}
                  <div className="space-y-2 text-left">
                    <label className="block text-xs font-bold text-vintage-wood uppercase tracking-wider text-center">
                      Ou pague via PIX Copia e Cola no celular:
                    </label>
                    <div className="relative">
                      <textarea
                        readOnly
                        value={checkoutData.qr_code}
                        rows={3}
                        className="w-full px-3 py-2 text-xs font-mono bg-white border border-vintage-sage/40 rounded-xl resize-none focus:outline-none"
                      />
                    </div>

                    <button
                      onClick={handleCopyPix}
                      className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm shadow-sm transition-all flex items-center justify-center gap-2 ${
                        copied
                          ? 'bg-vintage-sage text-white'
                          : 'bg-vintage-wood hover:bg-vintage-wood/90 text-white'
                      }`}
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4" />
                          <span>Código PIX Copiado!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 text-vintage-terracotta" />
                          <span>Copiar Chave PIX</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Polling Liveness Indicator */}
                  <div className="pt-2 flex items-center justify-center gap-2 text-xs text-vintage-sage">
                    <span className="w-2.5 h-2.5 bg-vintage-sage rounded-full animate-ping" />
                    <span>Aguardando confirmação bancária em tempo real...</span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
