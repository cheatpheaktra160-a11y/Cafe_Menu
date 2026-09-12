'use client';

import { Product, Category } from '@prisma/client';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useState } from 'react';
import ProductCustomization from './ProductCustomization';
import { useCart } from '@/hooks/useCart'; // We'll create this hook

interface ProductWithCategory extends Product {
  category: Category;
}

export default function ProductGrid({ products }: { products: ProductWithCategory[] }) {
  const searchParams = useSearchParams();
  const selectedCategory = searchParams.get('category');
  const [selectedProduct, setSelectedProduct] = useState<ProductWithCategory | null>(null);
  const [isCustomizationOpen, setIsCustomizationOpen] = useState(false);
  const { addItem } = useCart();

  const filteredProducts = selectedCategory
    ? products.filter((product) => product.categoryId === selectedCategory)
    : products;

  const handleProductClick = (product: ProductWithCategory) => {
    setSelectedProduct(product);
    setIsCustomizationOpen(true);
  };

  const handleAddToCart = (item: {
    product: ProductWithCategory;
    quantity: number;
    customizations: any;
    itemTotal: number;
  }) => {
    addItem(item);
    setIsCustomizationOpen(false);
    setSelectedProduct(null);
  };

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredProducts.map((product) => (
          <Card
            key={product.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => handleProductClick(product)}
          >
            <CardContent className="p-3">
              <div className="relative w-full h-32 mb-2">
                <Image
                  src={product.image || '/placeholder.svg'}
                  alt={product.name}
                  fill
                  className="rounded-md object-cover"
                />
              </div>
              <h3 className="font-semibold text-sm truncate">{product.name}</h3>
              <p className="text-gray-600 dark:text-gray-400 text-xs">{product.category.name}</p>
              <p className="font-bold text-lg text-orange-600 dark:text-orange-400">
                ${product.price.toFixed(2)}
              </p>
              {!product.isAvailable && (
                <span className="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  Unavailable
                </span>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {selectedProduct && (
        <Dialog open={isCustomizationOpen} onOpenChange={setIsCustomizationOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Customize {selectedProduct.name}</DialogTitle>
            </DialogHeader>
            <ProductCustomization product={selectedProduct} onAddToCart={handleAddToCart} />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}