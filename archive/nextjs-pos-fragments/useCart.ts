import { create } from 'zustand';
import { Product } from '@prisma/client';
import { v4 as uuidv4 } from 'uuid';

interface CartItem {
  id: string; // Unique ID for this cart item instance
  product: Product;
  quantity: number;
  customizations: any; // JSON object for selected options/addons
  itemTotal: number; // Total price for this specific item instance (unit price * quantity + customization costs)
}

interface CartState {
  cart: CartItem[];
  addItem: (item: { product: Product; quantity: number; customizations: any; itemTotal: number }) => void;
  updateQuantity: (id: string, newQuantity: number) => void;
  removeItem: (id: string) => void;
  clearCart: () => void;
  calculateTotals: () => { subtotal: number; total: number; discount: number; tax: number; serviceCharge: number };
}

export const useCart = create<CartState>((set, get) => ({
  cart: [],
  addItem: (newItem) => {
    set((state) => {
      // For simplicity, if a product with the exact same customizations is added,
      // we'll just increase its quantity. Otherwise, it's a new cart item.
      const existingItemIndex = state.cart.findIndex(
        (item) =>
          item.product.id === newItem.product.id &&
          JSON.stringify(item.customizations) === JSON.stringify(newItem.customizations)
      );

      if (existingItemIndex > -1) {
        const updatedCart = [...state.cart];
        const existingItem = updatedCart[existingItemIndex];
        existingItem.quantity += newItem.quantity;
        existingItem.itemTotal = (newItem.product.price + getPriceFromCustomizations(newItem.customizations)) * existingItem.quantity;
        return { cart: updatedCart };
      } else {
        return {
          cart: [
            ...state.cart,
            {
              id: uuidv4(), // Assign a unique ID to this cart item instance
              ...newItem,
            },
          ],
        };
      }
    });
  },
  updateQuantity: (id, newQuantity) => {
    set((state) => ({
      cart: state.cart
        .map((item) => {
          if (item.id === id) {
            const basePrice = item.product.price + getPriceFromCustomizations(item.customizations);
            return {
              ...item,
              quantity: Math.max(1, newQuantity),
              itemTotal: basePrice * Math.max(1, newQuantity),
            };
          }
          return item;
        })
        .filter((item) => item.quantity > 0), // Remove if quantity becomes 0
    }));
  },
  removeItem: (id) => {
    set((state) => ({
      cart: state.cart.filter((item) => item.id !== id),
    }));
  },
  clearCart: () => set({ cart: [] }),
  calculateTotals: () => {
    const cart = get().cart;
    let subtotal = 0;
    let discount = 0; // To be implemented
    let tax = 0; // To be implemented
    let serviceCharge = 0; // To be implemented

    cart.forEach((item) => {
      subtotal += item.itemTotal;
    });

    const total = subtotal - discount + tax + serviceCharge;

    return { subtotal, total, discount, tax, serviceCharge };
  },
}));

// Helper function to calculate price from customizations (matching ProductCustomization.tsx logic)
function getPriceFromCustomizations(customizations: any): number {
  let additionalPrice = 0;
  const { size, milk, sugar, addOns } = customizations;

  // These hardcoded options should eventually come from the database
  const sizes = [{ name: 'Small', price: 0 }, { name: 'Medium', price: 0.5 }, { name: 'Large', price: 1.0 }];
  const milkOptions = [{ name: 'Regular Milk', price: 0 }, { name: 'Soy Milk', price: 0.75 }, { name: 'Almond Milk', price: 0.75 }, { name: 'Oat Milk', price: 0.75 }];
  const sugarOptions = [{ name: 'None', price: 0 }, { name: 'Normal', price: 0 }, { name: 'Extra', price: 0.25 }];
  const addOnsList = [{ name: 'Extra Shot', price: 1.0 }, { name: 'Whipped Cream', price: 0.5 }, { name: 'Caramel Drizzle', price: 0.75 }];

  additionalPrice += sizes.find(s => s.name === size)?.price || 0;
  additionalPrice += milkOptions.find(m => m.name === milk)?.price || 0;
  additionalPrice += sugarOptions.find(s => s.name === sugar)?.price || 0;
  
  if (Array.isArray(addOns)) {
    addOns.forEach((addonName: string) => {
      additionalPrice += addOnsList.find(a => a.name === addonName)?.price || 0;
    });
  }

  return additionalPrice;
}