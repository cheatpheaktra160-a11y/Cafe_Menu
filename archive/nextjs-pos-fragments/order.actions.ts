'use server';

import prisma from '@/lib/prisma';
import { OrderType, OrderStatus, PaymentMethod, InventoryTransactionType } from '@prisma/client';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { revalidatePath } from 'next/cache';

interface CartItem {
  productId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  customizations: any; // JSON object for selected options/addons
  itemTotal: number;
}

export async function createOrder(
  cartItems: CartItem[],
  orderType: OrderType,
  tableId: string | null,
  totalAmount: number
) {
  const session = await getServerSession(authOptions);

  if (!session?.user?.id) {
    return { success: false, message: 'User not authenticated.' };
  }

  if (cartItems.length === 0) {
    return { success: false, message: 'Cart is empty.' };
  }

  try {
    const order = await prisma.order.create({
      data: {
        orderType,
        tableId: orderType === OrderType.DINE_IN ? tableId : null,
        totalAmount,
        // TODO: Get tax and service charge from settings
        paymentStatus: 'UNPAID',
        cashierId: session.user.id,
        status: OrderStatus.PENDING,
        items: {
          create: cartItems.map((item) => ({
            productId: item.productId,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            customizations: item.customizations,
            itemTotal: item.itemTotal,
          })),
        },
      },
    });

    if (order.tableId) {
      await prisma.table.update({
        where: { id: order.tableId },
        data: { status: 'Occupied' },
      });
      revalidatePath('/tables');
    }

    revalidatePath('/pos');
    revalidatePath('/orders');
    revalidatePath('/dashboard');

    return { success: true, orderId: order.id, totalAmount: order.totalAmount };
  } catch (error) {
    console.error('Failed to create order:', error);
    return { success: false, message: 'Failed to create order.' };
  }
}

export async function processPayment(orderId: string, method: PaymentMethod, amount: number) {
  try {
    // Step 1: Update order and create payment record
    const order = await prisma.order.update({
      where: { id: orderId },
      data: {
        paymentStatus: 'PAID',
        status: OrderStatus.PREPARING, // Change status to PREPARING for KDS
        payments: {
          create: {
            method,
            amount,
          },
        },
      },
      include: {
        customer: true,
        items: {
          include: {
            product: {
              include: {
                ingredients: true,
              },
            },
          },
        },
      },
    });

    // Step 1.5: Award loyalty points if a customer is attached to the order
    if (order.customer) {
      const pointsEarned = Math.floor(order.totalAmount); // 1 point per dollar
      if (pointsEarned > 0) {
        await prisma.customer.update({
          where: { id: order.customerId! },
          data: { loyaltyPoints: { increment: pointsEarned } },
        });
        await prisma.loyaltyTransaction.create({
          data: {
            customerId: order.customerId!,
            orderId: order.id,
            points: pointsEarned,
            description: `Earned from order #${order.id.slice(-8).toUpperCase()}`,
          },
        });
      }
    }

    // Step 2: Deduct inventory based on recipes
    const inventoryTransactions = [];
    for (const item of order.items) {
      for (const productIngredient of item.product.ingredients) {
        const quantityToDeduct = productIngredient.quantity * item.quantity;
        
        await prisma.ingredient.update({
          where: { id: productIngredient.ingredientId },
          data: { stock: { decrement: quantityToDeduct } },
        });

        inventoryTransactions.push({
          ingredientId: productIngredient.ingredientId,
          type: InventoryTransactionType.SALE,
          quantity: -quantityToDeduct,
          orderId: order.id,
        });
      }
    }
    await prisma.inventoryTransaction.createMany({ data: inventoryTransactions });

    revalidatePath('/orders');
    revalidatePath('/dashboard');
    revalidatePath('/inventory');
    revalidatePath('/kitchen'); // Revalidate KDS page
    revalidatePath('/customers');

    return { success: true, orderId: order.id };
  } catch (error) {
    console.error('Failed to process payment:', error);
    return { success: false, message: 'Failed to process payment.' };
  }
}

export async function getOrderForReceipt(orderId: string) {
    try {
        const order = await prisma.order.findUnique({
            where: { id: orderId },
            include: { items: { include: { product: true } }, cashier: true, table: true, payments: true },
        });
        return order;
    } catch (error) {
        console.error('Failed to fetch order for receipt:', error);
        return null;
    }
}

export async function getKitchenOrders() {
    try {
        const orders = await prisma.order.findMany({
            where: {
                status: {
                    in: [OrderStatus.PREPARING, OrderStatus.READY]
                }
            },
            include: {
                items: {
                    include: {
                        product: true
                    }
                },
                table: true
            },
            orderBy: {
                createdAt: 'asc'
            }
        });
        return orders;
    } catch (error) {
        console.error('Failed to fetch kitchen orders:', error);
        return [];
    }
}

export async function updateOrderStatus(orderId: string, status: OrderStatus) {
    await prisma.order.update({ where: { id: orderId }, data: { status } });
    revalidatePath('/kitchen');
    revalidatePath('/orders');
}