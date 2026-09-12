'use client';

import { Table, OrderType, Customer } from '@prisma/client';
import { useCart } from '@/hooks/useCart';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Minus, Plus, Trash2, Edit } from 'lucide-react';
import Image from 'next/image';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useState } from 'react';
import { createOrder } from '@/lib/actions/order.actions';
import { useToast } from '@/components/ui/use-toast';
import { useRouter } from 'next/navigation';
import PaymentDialog from './PaymentDialog';
import { Combobox } from '@/components/ui/combobox'; // A new reusable component

export default function Cart({ tables, customers }: { tables: Table[]; customers: Customer[] }) {
  const { cart, updateQuantity, removeItem, clearCart, calculateTotals } = useCart();
  const { subtotal, total } = calculateTotals();
  const { toast } = useToast();
  const router = useRouter();

  const [orderType, setOrderType] = useState<OrderType>(OrderType.DINE_IN);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaymentDialogOpen, setIsPaymentDialogOpen] = useState(false);
  const [pendingOrder, setPendingOrder] = useState<{orderId: string, totalAmount: number} | null>(null);

  const handlePlaceOrder = async () => {
    if (cart.length === 0) {
      toast({
        title: 'Cart is empty',
        description: 'Please add items to the cart before checking out.',
        variant: 'destructive',
      });
      return;
    }

    if (orderType === OrderType.DINE_IN && !selectedTable) {
      toast({
        title: 'Table not selected',
        description: 'Please select a table for dine-in orders.',
        variant: 'destructive',
      });
      return;
    }

    setIsProcessing(true);

    const orderItems = cart.map((item) => ({
      productId: item.product.id,
      name: item.product.name,
      quantity: item.quantity,
      unitPrice: item.product.price, // Base price, customization costs are in itemTotal
      customizations: item.customizations,
      itemTotal: item.itemTotal,
    }));

    const result = await createOrder(
      orderItems,
      orderType,
      selectedTable,
      selectedCustomer, // Pass customer ID
      total
    );

    if (result.success) {
      toast({
        title: 'Order Placed!',
        description: `Proceed to payment for order #${result.orderId}.`,
      });
      setPendingOrder({ orderId: result.orderId!, totalAmount: result.totalAmount! });
      setIsPaymentDialogOpen(true);
      setSelectedCustomer(null);
    } else {
      toast({
        title: 'Order Failed',
        description: result.message,
        variant: 'destructive',
      });
    }
    setIsProcessing(false);
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 pr-4">
        {cart.length === 0 ? (
          <p className="text-center text-gray-500 dark:text-gray-400 mt-8">Cart is empty.</p>
        ) : (
          <div className="space-y-4">
            {cart.map((item) => (
              <div key={item.id} className="flex items-center space-x-3 border-b pb-3 last:border-b-0">
                <div className="relative w-16 h-16 flex-shrink-0">
                  <Image
                    src={item.product.image || '/placeholder.svg'}
                    alt={item.product.name}
                    fill
                    className="rounded-md object-cover"
                  />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-sm">{item.product.name}</h4>
                  {item.customizations && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {Object.entries(item.customizations)
                        .filter(([, value]) => value && (Array.isArray(value) ? value.length > 0 : true))
                        .map(([key, value]) => (
                          <span key={key} className="mr-1">
                            {key}: {Array.isArray(value) ? value.join(', ') : value}
                          </span>
                        ))}
                    </p>
                  )}
                  <p className="text-sm font-bold text-gray-700 dark:text-gray-300">${item.itemTotal.toFixed(2)}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                  >
                    <Minus className="h-3 w-3" />
                  </Button>
                  <span className="text-sm font-medium w-5 text-center">{item.quantity}</span>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                  >
                    <Plus className="h-3 w-3" />
                  </Button>
                  {/* <Button variant="ghost" size="icon" className="h-7 w-7">
                    <Edit className="h-3 w-3" />
                  </Button> */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-red-500"
                    onClick={() => removeItem(item.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      <div className="mt-4 space-y-4">
        {/* Order Type */}
        <div>
          <Label className="text-base">Order Type</Label>
          <RadioGroup
            value={orderType}
            onValueChange={(value: OrderType) => {
              setOrderType(value);
              if (value !== OrderType.DINE_IN) setSelectedTable(null);
            }}
            className="grid grid-cols-3 gap-2 mt-2"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={OrderType.DINE_IN} id="order-type-dinein" />
              <Label htmlFor="order-type-dinein">Dine-in</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={OrderType.TAKEAWAY} id="order-type-takeaway" />
              <Label htmlFor="order-type-takeaway">Takeaway</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={OrderType.DELIVERY} id="order-type-delivery" />
              <Label htmlFor="order-type-delivery">Delivery</Label>
            </div>
          </RadioGroup>
        </div>

        {/* Table Selection (only for Dine-in) */}
        {orderType === OrderType.DINE_IN && (
          <div>
            <Label className="text-base">Select Table</Label>
            <Select onValueChange={setSelectedTable} value={selectedTable || ''}>
              <SelectTrigger className="w-full mt-2">
                <SelectValue placeholder="Select a table" />
              </SelectTrigger>
              <SelectContent>
                {tables.map((table) => (
                  <SelectItem key={table.id} value={table.id}>
                    {table.name} (Capacity: {table.capacity})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Customer Selection */}
        <div>
          <Label className="text-base">Customer (Optional)</Label>
          <Combobox
            items={customers.map(c => ({ value: c.id, label: `${c.name} - ${c.phone || c.email}` }))}
            value={selectedCustomer}
            onChange={setSelectedCustomer}
            placeholder="Search customer..."
            searchPlaceholder="Search by name, phone, or email..."
            noResultsText="No customer found."
          />
        </div>


        {/* Totals */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>Subtotal:</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Discount:</span>
            <span>$0.00</span> {/* Placeholder */}
          </div>
          <div className="flex justify-between text-sm">
            <span>Tax:</span>
            <span>$0.00</span> {/* Placeholder */}
          </div>
          <div className="flex justify-between text-lg font-bold">
            <span>Grand Total:</span>
            <span>${total.toFixed(2)}</span>
          </div>
        </div>

        <Button className="w-full" onClick={handlePlaceOrder} disabled={isProcessing}>
          {isProcessing ? 'Placing Order...' : 'Proceed to Payment'}
        </Button>
      </div>
      {pendingOrder && (
        <PaymentDialog
          isOpen={isPaymentDialogOpen}
          onOpenChange={setIsPaymentDialogOpen}
          orderId={pendingOrder.orderId}
          totalAmount={pendingOrder.totalAmount}
        />
      )}
    </div>
  );
}