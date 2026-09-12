'use client';

import { Category } from '@prisma/client';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

export default function CategoryFilter({ categories }: { categories: Category[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selectedCategory = searchParams.get('category');

  const handleCategoryClick = (categoryId: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (categoryId) {
      params.set('category', categoryId);
    } else {
      params.delete('category');
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <ScrollArea className="h-full pr-4">
      <Button
        variant={!selectedCategory ? 'default' : 'ghost'}
        className={cn('w-full justify-start mb-2', {
          'bg-orange-100 text-orange-600 dark:bg-orange-900/50 dark:text-orange-400': !selectedCategory,
        })}
        onClick={() => handleCategoryClick(null)}
      >
        All Products
      </Button>
      {categories.map((category) => (
        <Button
          key={category.id}
          variant={selectedCategory === category.id ? 'default' : 'ghost'}
          className={cn('w-full justify-start mb-2', {
            'bg-orange-100 text-orange-600 dark:bg-orange-900/50 dark:text-orange-400': selectedCategory === category.id,
          })}
          onClick={() => handleCategoryClick(category.id)}
        >
          {category.name}
        </Button>
      ))}
    </ScrollArea>
  );
}