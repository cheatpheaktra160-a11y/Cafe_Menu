'use server';

import prisma from '@/lib/prisma';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const IngredientSchema = z.object({
    name: z.string().min(2),
    unit: z.enum(['KG', 'G', 'L', 'ML', 'PCS']),
    stock: z.coerce.number().min(0),
    minStock: z.coerce.number().min(0),
    costPerUnit: z.coerce.number().min(0),
});

export async function getIngredients() {
    try {
        const ingredients = await prisma.ingredient.findMany({
            orderBy: { name: 'asc' },
        });
        return ingredients;
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function createIngredient(formData: FormData) {
    const validatedFields = IngredientSchema.safeParse(Object.fromEntries(formData.entries()));

    if (!validatedFields.success) {
        return { success: false, message: 'Invalid form data.' };
    }

    try {
        await prisma.ingredient.create({ data: validatedFields.data });
        revalidatePath('/inventory');
        return { success: true, message: 'Ingredient created successfully.' };
    } catch (error) {
        return { success: false, message: 'Database Error: Failed to create ingredient.' };
    }
}