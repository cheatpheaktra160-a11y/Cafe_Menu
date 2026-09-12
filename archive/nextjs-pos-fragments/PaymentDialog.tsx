'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PaymentMethod } from '@prisma/client';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { processPayment } from '@/lib/actions/order.actions';
import { useCart } from '@/hooks/useCart';

interface PaymentDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  orderId: string | null;
  totalAmount: number;
}

export default function PaymentDialog({
  isOpen,
  onOpenChange,
  orderId,
  totalAmount,
}: PaymentDialogProps) {
  const router = useRouter();
  const { toast } = useToast();
  const { clearCart } = useCart();
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(PaymentMethod.CASH);
  const [cashReceived, setCashReceived] = useState<number | string>('');
  const [isProcessing, setIsProcessing] = useState(false);

  const change =
    typeof cashReceived === 'number' && cashReceived >= totalAmount
      ? cashReceived - totalAmount
      : 0;

  const handlePayment = async () => {
    if (!orderId) return;

    if (paymentMethod === PaymentMethod.CASH && (typeof cashReceived !== 'number' || cashReceived < totalAmount)) {
        toast({
            title: 'Invalid Amount',
            description: 'Cash received must be equal to or greater than the total amount.',
            variant: 'destructive',
        });
        return;
    }

    setIsProcessing(true);
    const result = await processPayment(orderId, paymentMethod, totalAmount);
    setIsProcessing(false);

    if (result.success) {
      toast({
        title: 'Payment Successful!',
        description: 'Order has been completed.',
      });
      clearCart();
      onOpenChange(false);
      router.push(`/receipt/${result.orderId}`);
    } else {
      toast({
        title: 'Payment Failed',
        description: result.message,
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Payment</DialogTitle>
          <DialogDescription>
            Total Amount: <span className="font-bold text-lg">${totalAmount.toFixed(2)}</span>
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="payment-method" className="text-right">
              Method
            </Label>
            <div className="col-span-3 flex gap-2">
              <Button
                variant={paymentMethod === PaymentMethod.CASH ? 'default' : 'outline'}
                onClick={() => setPaymentMethod(PaymentMethod.CASH)}
              >
                Cash
              </Button>
              <Button
                variant={paymentMethod === PaymentMethod.CREDIT_CARD ? 'default' : 'outline'}
                onClick={() => setPaymentMethod(PaymentMethod.CREDIT_CARD)}
              >
                Card
              </Button>
            </div>
          </div>
          {paymentMethod === PaymentMethod.CASH && (
            <>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="cash-received" className="text-right">
                  Cash Received
                </Label>
                <Input
                  id="cash-received"
                  type="number"
                  value={cashReceived}
                  onChange={(e) => setCashReceived(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="col-span-3"
                  placeholder="e.g., 50.00"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="change" className="text-right">
                  Change
                </Label>
                <div id="change" className="col-span-3 font-bold text-lg">
                  ${change.toFixed(2)}
                </div>
              </div>
            </>
          )}
        </div>
        <DialogFooter>
          <Button
            type="button"
            onClick={handlePayment}
            disabled={isProcessing}
            className="w-full"
          >
            {isProcessing ? 'Processing...' : 'Complete Payment'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}