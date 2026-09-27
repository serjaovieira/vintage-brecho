import React from 'react';
import { Tag } from 'lucide-react';

interface CategoryFilterProps {
  categories: string[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  isLoading?: boolean;
}

export const CategoryFilter: React.FC<CategoryFilterProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  isLoading = false,
}) => {
  const allOptions = ['Todas as Peças', ...categories];

  return (
    <div className="py-4">
      <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-vintage-wood tracking-wider uppercase">
        <Tag className="w-3.5 h-3.5 text-vintage-sage" />
        <span>Categorias em Destaque</span>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none no-scrollbar">
        {allOptions.map((cat) => {
          const isSelected = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => onSelectCategory(cat)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-200 border ${
                isSelected
                  ? 'bg-vintage-wood text-white border-vintage-wood shadow-vintage-card scale-[1.02]'
                  : 'bg-vintage-cream-light text-vintage-text border-vintage-sage/30 hover:border-vintage-sage hover:bg-vintage-sage/10'
              }`}
            >
              {cat}
            </button>
          );
        })}

        {isLoading && (
          <div className="h-8 w-24 bg-vintage-sage/15 animate-pulse rounded-full" />
        )}
      </div>
    </div>
  );
};
