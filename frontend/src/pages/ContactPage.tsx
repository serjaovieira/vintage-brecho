import React from 'react';
import { Phone, MapPin, Clock, Truck, ShieldCheck, MessageCircle, Mail } from 'lucide-react';

export const ContactPage: React.FC = () => {
  const storePhone = '17981668413';
  const phoneDisplay = '(17) 98166-8413';
  const whatsappUrl = `https://wa.me/55${storePhone}?text=Ol%C3%A1!%20Gostaria%20de%20tirar%20uma%20d%C3%BAvida%20sobre%20as%20pe%C3%A7as%20do%20Vintage%20Brech%C3%B3.`;

  return (
    <main className="min-h-screen py-10 sm:py-16 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-12">
      {/* Page Title */}
      <div className="text-center space-y-3">
        <span className="text-xs font-bold text-vintage-sage uppercase tracking-widest block">
          Atendimento & Informações
        </span>
        <h1 className="font-serif text-3xl sm:text-5xl font-extrabold text-vintage-wood">
          Contato & Sobre o Brechó
        </h1>
        <p className="max-w-xl mx-auto text-sm text-vintage-text/80 leading-relaxed font-light">
          Estamos à disposição para tirar dúvidas sobre medidas de peças, tecidos, estado de
          conservação ou prazos de envio.
        </p>
      </div>

      {/* Main Contact Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* WhatsApp & Telefone Card */}
        <div className="bg-white/90 rounded-3xl p-6 sm:p-8 border border-vintage-sage/30 shadow-vintage-soft space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-vintage-sage/15 flex items-center justify-center text-vintage-sage">
            <Phone className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-serif text-xl font-bold text-vintage-wood">
              WhatsApp Oficial
            </h2>
            <p className="text-xs text-vintage-text/70 mt-1">
              Atendimento rápido para dúvidas e pós-venda.
            </p>
          </div>

          <div className="pt-2">
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-[#25D366] hover:bg-[#20ba59] text-white font-bold text-sm shadow-md transition-all duration-200"
            >
              <MessageCircle className="w-5 h-5 fill-white" />
              <span>Chamar no WhatsApp {phoneDisplay}</span>
            </a>
          </div>

          <div className="pt-2 text-xs text-vintage-text/60 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>Segunda a Sábado, das 09h às 19h</span>
          </div>
        </div>

        {/* Localização & Envio */}
        <div className="bg-white/90 rounded-3xl p-6 sm:p-8 border border-vintage-sage/30 shadow-vintage-soft space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-vintage-terracotta/15 flex items-center justify-center text-vintage-terracotta">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-serif text-xl font-bold text-vintage-wood">
              Envio Fixo em Todo o Brasil
            </h2>
            <p className="text-xs text-vintage-text/70 mt-1">
              Taxa única de <strong>R$ 15,00</strong> para qualquer estado brasileiro.
            </p>
          </div>

          <div className="space-y-2 text-xs text-vintage-text/80 leading-relaxed pt-2">
            <div className="flex items-start gap-2">
              <MapPin className="w-4 h-4 text-vintage-sage shrink-0 mt-0.5" />
              <span>Despachado de São José do Rio Preto / SP com código de rastreamento dos Correios / Transportadora.</span>
            </div>
            <div className="flex items-start gap-2">
              <Mail className="w-4 h-4 text-vintage-sage shrink-0 mt-0.5" />
              <span>Você recebe notificações de rastreamento por e-mail e WhatsApp.</span>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <section className="bg-vintage-cream-light rounded-3xl p-6 sm:p-10 border border-vintage-sage/25 space-y-6">
        <h2 className="font-serif text-2xl font-bold text-vintage-wood text-center">
          Dúvidas Frequentes sobre Nossas Peças
        </h2>

        <div className="space-y-4 text-xs sm:text-sm text-vintage-text">
          <div className="bg-white/80 rounded-2xl p-4 sm:p-5 border border-vintage-sage/20 space-y-1.5">
            <h3 className="font-bold text-vintage-wood flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-vintage-terracotta shrink-0" />
              Como funciona o estoque unitário (1-of-1)?
            </h3>
            <p className="text-vintage-text/80 leading-relaxed">
              Trabalhamos exclusivamente com moda circular vintage. Isso significa que cada peça é única no mundo (não temos grade de tamanhos repetidos). Quando uma cliente compra, a peça é marcada como vendida e sai imediatamente da vitrine.
            </p>
          </div>

          <div className="bg-white/80 rounded-2xl p-4 sm:p-5 border border-vintage-sage/20 space-y-1.5">
            <h3 className="font-bold text-vintage-wood flex items-center gap-2">
              <Clock className="w-4 h-4 text-vintage-sage shrink-0" />
              O que é a Trava Atômica de 10 Minutos?
            </h3>
            <p className="text-vintage-text/80 leading-relaxed">
              Ao clicar em comprar e gerar o QR Code PIX, a peça fica bloqueada exclusivamente para você durante 10:00 minutos. Nenhuma outra cliente consegue comprá-la nesse intervalo. Se o pagamento não for realizado no tempo limite, ela volta automaticamente à vitrine.
            </p>
          </div>

          <div className="bg-white/80 rounded-2xl p-4 sm:p-5 border border-vintage-sage/20 space-y-1.5">
            <h3 className="font-bold text-vintage-wood flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-vintage-sage shrink-0" />
              As peças vintage são higienizadas?
            </h3>
            <p className="text-vintage-text/80 leading-relaxed">
              Sim! Todas as peças passam por rigorosa curadoria, higienização profissional e inspeção de costuras, botões e zíperes antes de serem fotografadas e disponibilizadas.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
};
