'use client';

import { Order, OrderItem, Product, Table, OrderStatus } from '@prisma/client';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { updateOrderStatus } from '@/lib/actions/order.actions';
import { useTransition } from 'react';

type KitchenOrder = Order & {
  items: (OrderItem & { product: Product })[];
  table: Table | null;
};

interface OrderCardProps {
  order: KitchenOrder;
}

export default function OrderCard({ order }: OrderCardProps) {
  const [isPending, startTransition] = useTransition();

  const timeSinceOrder = Math.round((Date.now() - new Date(order.createdAt).getTime()) / 60000);

  const handleStatusChange = (newStatus: OrderStatus) => {
    startTransition(async () => {
      await updateOrderStatus(order.id, newStatus);
    });
  };

  return (
    <Card className="bg-gray-900 border-gray-700 text-white">
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span>
            {order.orderType === 'DINE_IN' && order.table ? `Table: ${order.table.name}` : order.orderType}
          </span>
          <span className="text-sm font-normal text-gray-400">{timeSinceOrder} min ago</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {order.items.map(item => (
            <li key={item.id} className="flex justify-between items-start">
              <div className="flex-1">
                <span className="font-bold">{item.quantity}x</span> {item.product.name}
                {item.customizations && (
                  <p className="text-xs text-gray-400 pl-4">
                    {Object.entries(item.customizations as object)
                      .filter(([, value]) => value && (Array.isArray(value) ? value.length > 0 : true))
                      .map(([key, value]) => (
                        <span key={key} className="mr-2">
                          - {Array.isArray(value) ? value.join(', ') : value}
                        </span>
                      ))}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter className="flex justify-end">
        {order.status === OrderStatus.PREPARING && (
          <Button 
            onClick={() => handleStatusChange(OrderStatus.READY)}
            disabled={isPending}
            className="bg-green-600 hover:bg-green-700"
          >
            Mark as Ready
          </Button>
        )}
        {/* You could add a button here to move from READY back to PREPARING if needed */}
      </CardFooter>
    </Card>
  );
}