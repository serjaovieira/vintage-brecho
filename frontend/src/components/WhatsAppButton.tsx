import React from 'react';
import { MessageCircle } from 'lucide-react';

export const WhatsAppButton: React.FC = () => {
  const storePhone = '17981668413';
  const message = encodeURIComponent(
    'Olá! Gostaria de tirar uma dúvida sobre as peças do Vintage Brechó.'
  );
  const whatsappUrl = `https://wa.me/55${storePhone}?text=${message}`;

  return (
    <aside aria-label="Atendimento via WhatsApp" className="fixed bottom-6 right-6 z-40">
      <a
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Fale Conosco no WhatsApp (17) 98166-8413"
        className="group relative flex items-center justify-center w-14 h-14 bg-[#25D366] hover:bg-[#20ba59] text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-[#25D366]/30"
      >
        <MessageCircle className="w-7 h-7 fill-white" />

        {/* Pulse effect */}
        <span className="absolute -inset-1 rounded-full bg-[#25D366] opacity-30 group-hover:opacity-50 animate-ping pointer-events-none" />

        {/* Tooltip on Desktop hover */}
        <span className="absolute right-16 px-3 py-1.5 bg-vintage-wood text-white text-xs font-medium rounded-xl whitespace-nowrap shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          Dúvidas? Fale no WhatsApp!
        </span>
      </a>
    </aside>
  );
};
