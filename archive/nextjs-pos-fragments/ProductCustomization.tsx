'use client';

import { Product } from '@prisma/client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Plus, Minus } from 'lucide-react';

interface ProductCustomizationProps {
  product: Product;
  onAddToCart: (item: {
    product: Product;
    quantity: number;
    customizations: any;
    itemTotal: number;
  }) => void;
}

// Hardcoded options for now - will be dynamic later
const sizes = [
  { name: 'Small', price: 0 },
  { name: 'Medium', price: 0.5 },
  { name: 'Large', price: 1.0 },
];

const milkOptions = [
  { name: 'Regular Milk', price: 0 },
  { name: 'Soy Milk', price: 0.75 },
  { name: 'Almond Milk', price: 0.75 },
  { name: 'Oat Milk', price: 0.75 },
];

const sugarOptions = [
  { name: 'None', price: 0 },
  { name: 'Normal', price: 0 },
  { name: 'Extra', price: 0.25 },
];

const addOns = [
  { name: 'Extra Shot', price: 1.0 },
  { name: 'Whipped Cream', price: 0.5 },
  { name: 'Caramel Drizzle', price: 0.75 },
];

export default function ProductCustomization({ product, onAddToCart }: ProductCustomizationProps) {
  const [quantity, setQuantity] = useState(1);
  const [selectedSize, setSelectedSize] = useState(sizes[0]);
  const [selectedMilk, setSelectedMilk] = useState(milkOptions[0]);
  const [selectedSugar, setSelectedSugar] = useState(sugarOptions[0]);
  const [selectedAddOns, setSelectedAddOns] = useState<typeof addOns>([]);

  const calculateItemPrice = () => {
    let price = product.price;
    price += selectedSize.price;
    price += selectedMilk.price;
    price += selectedSugar.price;
    selectedAddOns.forEach((addon) => (price += addon.price));
    return price;
  };

  const itemPrice = calculateItemPrice();
  const totalItemPrice = itemPrice * quantity;

  const handleAddOnToggle = (addon: typeof addOns[0]) => {
    setSelectedAddOns((prev) =>
      prev.some((a) => a.name === addon.name)
        ? prev.filter((a) => a.name !== addon.name)
        : [...prev, addon]
    );
  };

  const customizations = {
    size: selectedSize.name,
    milk: selectedMilk.name,
    sugar: selectedSugar.name,
    addOns: selectedAddOns.map((a) => a.name),
  };

  return (
    <div className="space-y-4">
      {/* Quantity */}
      <div>
        <Label className="text-base">Quantity</Label>
        <div className="flex items-center space-x-2 mt-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setQuantity((prev) => Math.max(1, prev - 1))}
          >
            <Minus className="h-4 w-4" />
          </Button>
          <span className="w-8 text-center font-semibold">{quantity}</span>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setQuantity((prev) => prev + 1)}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Size */}
      <div>
        <Label className="text-base">Size</Label>
        <RadioGroup
          value={selectedSize.name}
          onValueChange={(value) => setSelectedSize(sizes.find((s) => s.name === value)!)}
          className="grid grid-cols-3 gap-2 mt-2"
        >
          {sizes.map((size) => (
            <div key={size.name} className="flex items-center space-x-2">
              <RadioGroupItem value={size.name} id={`size-${size.name}`} />
              <Label htmlFor={`size-${size.name}`}>
                {size.name} {size.price > 0 && `(+$${size.price.toFixed(2)})`}
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      {/* Milk */}
      <div>
        <Label className="text-base">Milk</Label>
        <RadioGroup
          value={selectedMilk.name}
          onValueChange={(value) => setSelectedMilk(milkOptions.find((m) => m.name === value)!)}
          className="grid grid-cols-2 gap-2 mt-2"
        >
          {milkOptions.map((milk) => (
            <div key={milk.name} className="flex items-center space-x-2">
              <RadioGroupItem value={milk.name} id={`milk-${milk.name}`} />
              <Label htmlFor={`milk-${milk.name}`}>
                {milk.name} {milk.price > 0 && `(+$${milk.price.toFixed(2)})`}
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      {/* Sugar */}
      <div>
        <Label className="text-base">Sugar</Label>
        <RadioGroup
          value={selectedSugar.name}
          onValueChange={(value) => setSelectedSugar(sugarOptions.find((s) => s.name === value)!)}
          className="grid grid-cols-3 gap-2 mt-2"
        >
          {sugarOptions.map((sugar) => (
            <div key={sugar.name} className="flex items-center space-x-2">
              <RadioGroupItem value={sugar.name} id={`sugar-${sugar.name}`} />
              <Label htmlFor={`sugar-${sugar.name}`}>
                {sugar.name} {sugar.price > 0 && `(+$${sugar.price.toFixed(2)})`}
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      {/* Add-ons */}
      <div>
        <Label className="text-base">Add-ons</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {addOns.map((addon) => (
            <Button
              key={addon.name}
              variant={selectedAddOns.some((a) => a.name === addon.name) ? 'default' : 'outline'}
              onClick={() => handleAddOnToggle(addon)}
            >
              {addon.name} (+$${addon.price.toFixed(2)})
            </Button>
          ))}
        </div>
      </div>

      <div className="flex justify-between items-center pt-4 border-t">
        <span className="text-lg font-bold">Total: ${totalItemPrice.toFixed(2)}</span>
        <Button
          onClick={() =>
            onAddToCart({
              product,
              quantity,
              customizations,
              itemTotal: totalItemPrice,
            })
          }
        >
          Add to Cart
        </Button>
      </div>
    </div>
  );
}