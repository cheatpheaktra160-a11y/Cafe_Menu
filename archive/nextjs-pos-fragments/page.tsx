'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useReactToPrint } from 'react-to-print';
import { getOrderForReceipt } from '@/lib/actions/order.actions';
import { Order, OrderItem, Product, User, Table as DbTable, Payment } from '@prisma/client';
import { Button } from '@/components/ui/button';
import { Loader2, Printer } from 'lucide-react';

type OrderDetails = Order & {
  items: (OrderItem & { product: Product })[];
  cashier: User;
  table: DbTable | null;
  payments: Payment[];
};

export default function ReceiptPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.orderId as string;
  const [order, setOrder] = useState<OrderDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const receiptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (orderId) {
      const fetchOrder = async () => {
        setLoading(true);
        const orderData = await getOrderForReceipt(orderId);
        setOrder(orderData as OrderDetails);
        setLoading(false);
      };
      fetchOrder();
    }
  }, [orderId]);

  const handlePrint = useReactToPrint({
    content: () => receiptRef.current,
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="flex flex-col justify-center items-center h-screen text-center">
        <h1 className="text-2xl font-bold mb-4">Order Not Found</h1>
        <p>The requested order could not be found.</p>
        <Button onClick={() => router.push('/pos')} className="mt-4">
          Back to POS
        </Button>
      </div>
    );
  }

  const payment = order.payments[0];

  return (
    <div className="bg-gray-100 min-h-screen p-4 sm:p-8 flex flex-col items-center">
      <div className="w-full max-w-md bg-white p-6 shadow-lg" ref={receiptRef}>
        <div className="text-center">
          {/* TODO: Get from settings */}
          <h1 className="text-2xl font-bold">Bean & Brew Café</h1>
          <p className="text-sm">123 Coffee Lane, Java City, 12345</p>
          <p className="text-sm">Phone: (123) 456-7890</p>
        </div>

        <div className="border-t border-b border-dashed my-4 py-2">
          <div className="flex justify-between text-sm">
            <span>Order #:</span>
            <span>{order.id.slice(-8).toUpperCase()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Date:</span>
            <span>{new Date(order.createdAt).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Time:</span>
            <span>{new Date(order.createdAt).toLocaleTimeString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Cashier:</span>
            <span>{order.cashier.name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Order Type:</span>
            <span>{order.orderType === 'DINE_IN' && order.table ? `${order.orderType} (${order.table.name})` : order.orderType}</span>
          </div>
        </div>

        <div className="space-y-2">
          {order.items.map((item) => (
            <div key={item.id} className="flex text-sm">
              <div className="flex-1">
                <p>{item.quantity}x {item.product.name}</p>
                {/* TODO: Display customizations nicely */}
              </div>
              <p>${item.itemTotal.toFixed(2)}</p>
            </div>
          ))}
        </div>

        <div className="border-t border-dashed my-4 pt-2 space-y-1 text-sm">
          <div className="flex justify-between">
            <span>Subtotal:</span>
            <span>${order.totalAmount.toFixed(2)}</span>
          </div>
          {/* Add Discount, Tax, etc. here when implemented */}
          <div className="flex justify-between font-bold text-base">
            <span>Total:</span>
            <span>${order.totalAmount.toFixed(2)}</span>
          </div>
        </div>

        {payment && (
            <div className="border-t border-dashed my-4 pt-2 space-y-1 text-sm">
                <div className="flex justify-between">
                    <span>Payment Method:</span>
                    <span>{payment.method.replace('_', ' ')}</span>
                </div>
            </div>
        )}

        <div className="text-center mt-4 text-sm">
          <p>Thank you for your visit!</p>
        </div>
      </div>

      <div className="mt-6 flex gap-4">
        <Button onClick={handlePrint}><Printer className="mr-2 h-4 w-4" /> Print Receipt</Button>
        <Button variant="outline" onClick={() => router.push('/pos')}>New Order</Button>
      </div>
    </div>
  );
}