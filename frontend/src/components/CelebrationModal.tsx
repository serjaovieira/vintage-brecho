import React, { useEffect } from 'react';
import confetti from 'canvas-confetti';
import { Sparkles, CheckCircle2, MessageCircle, ArrowRight } from 'lucide-react';
import { Product } from '../services/api';

interface CelebrationModalProps {
  orderId: string;
  product: Product;
  onClose: () => void;
}

export const CelebrationModal: React.FC<CelebrationModalProps> = ({
  orderId,
  product,
  onClose,
}) => {
  useEffect(() => {
    // Fire confetti celebration
    try {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#CE724A', '#638875', '#5C3D2E', '#F6F1E7'],
      });
    } catch (e) {
      console.warn('Confetti error:', e);
    }
  }, []);

  const storePhone = '17981668413';
  const whatsappMessage = encodeURIComponent(
    `Olá! Acabei de realizar o pagamento da peça *${product.title}* (Pedido: ${orderId}) no Vintage Brechó. Gostaria de acompanhar o envio!`
  );
  const whatsappUrl = `https://wa.me/55${storePhone}?text=${whatsappMessage}`;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-vintage-wood/75 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 animate-fade-in">
      <div
        className="relative bg-vintage-cream w-full max-w-lg rounded-3xl border border-vintage-sage/40 shadow-2xl p-6 sm:p-8 text-center space-y-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Celebration Badge */}
        <div className="w-20 h-20 mx-auto rounded-full bg-vintage-sage/20 border-2 border-vintage-sage flex items-center justify-center text-vintage-sage animate-bounce">
          <CheckCircle2 className="w-12 h-12" />
        </div>

        <div>
          <span className="text-xs font-bold text-vintage-sage uppercase tracking-widest block mb-1">
            Pagamento Aprovado com Sucesso!
          </span>
          <h2 className="font-serif text-2xl sm:text-3xl font-extrabold text-vintage-wood leading-tight">
            Esta Peça Única Agora é Sua! 🎉
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-vintage-text/80 leading-relaxed">
            O status da peça foi atualizado e ela foi retirada definitivamente da vitrine. Estamos preparando sua embalagem com carinho e aroma vintage.
          </p>
        </div>

        {/* Order Card Preview */}
        <div className="bg-white rounded-2xl p-4 border border-vintage-sage/25 text-left flex items-center gap-3">
          <img
            src={product.image_url}
            alt={product.title}
            className="w-16 h-16 rounded-xl object-cover border border-vintage-sage/30 shrink-0"
          />
          <div className="overflow-hidden">
            <h4 className="font-serif font-bold text-sm text-vintage-wood truncate">
              {product.title}
            </h4>
            <span className="text-xs text-vintage-sage font-medium block">
              Tamanho {product.size} • 1-of-1
            </span>
            <span className="text-[11px] text-vintage-text/60 font-mono block truncate">
              ID do Pedido: {orderId}
            </span>
          </div>
        </div>

        {/* Next Steps & Support */}
        <div className="space-y-3 pt-2">
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full py-3.5 px-4 rounded-xl bg-vintage-sage hover:bg-vintage-sage-dark text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2"
          >
            <MessageCircle className="w-4 h-4" />
            <span>Falar com o Brechó no WhatsApp</span>
          </a>

          <button
            onClick={onClose}
            className="w-full py-3.5 px-4 rounded-xl bg-vintage-wood hover:bg-vintage-wood/90 text-white font-bold text-sm shadow-sm transition-all flex items-center justify-center gap-2"
          >
            <span>Continuar Navegando na Vitrine</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-center gap-1.5 text-[11px] text-vintage-wood/60">
          <Sparkles className="w-3.5 h-3.5 text-vintage-terracotta" />
          <span>Obrigada por apoiar a moda circular e sustentável!</span>
        </div>
      </div>
    </div>
  );
};
