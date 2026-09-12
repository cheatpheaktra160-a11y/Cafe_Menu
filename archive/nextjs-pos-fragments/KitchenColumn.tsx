import { Order, OrderItem, Product, Table } from '@prisma/client';
import { ScrollArea } from '@/components/ui/scroll-area';
import OrderCard from './OrderCard';

type KitchenOrder = Order & {
  items: (OrderItem & { product: Product })[];
  table: Table | null;
};

interface KitchenColumnProps {
  title: string;
  orders: KitchenOrder[];
}

export default function KitchenColumn({ title, orders }: KitchenColumnProps) {
  return (
    <div className="bg-gray-800 rounded-lg flex flex-col">
      <h2 className="text-xl font-bold p-4 border-b border-gray-700 text-center">{title} ({orders.length})</h2>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {orders.map(order => (
            <OrderCard key={order.id} order={order} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}