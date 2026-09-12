'use server';

import prisma from '@/lib/prisma';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const CustomerSchema = z.object({
    name: z.string().min(2, 'Name is required.'),
    phone: z.string().optional(),
    email: z.string().email('Invalid email address.').optional().or(z.literal('')),
});

export async function getCustomers() {
    try {
        const customers = await prisma.customer.findMany({
            orderBy: { createdAt: 'desc' },
        });
        return customers;
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function createCustomer(formData: FormData) {
    const validatedFields = CustomerSchema.safeParse(Object.fromEntries(formData.entries()));

    if (!validatedFields.success) {
        return { success: false, message: 'Invalid form data.', errors: validatedFields.error.flatten().fieldErrors };
    }

    try {
        await prisma.customer.create({ data: validatedFields.data });
        revalidatePath('/customers');
        revalidatePath('/pos');
        return { success: true, message: 'Customer created successfully.' };
    } catch (error) {
        console.error(error);
        return { success: false, message: 'Database Error: Failed to create customer.' };
    }
}