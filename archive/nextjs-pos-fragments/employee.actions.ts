'use server';

import prisma from '@/lib/prisma';
import { revalidatePath } from 'next/cache';
import { hash } from 'bcrypt';
import { z } from 'zod';

const EmployeeSchema = z.object({
    name: z.string().min(2),
    email: z.string().email(),
    password: z.string().min(6),
    role: z.enum(['ADMIN', 'MANAGER', 'CASHIER', 'KITCHEN']),
});

export async function getEmployees() {
    try {
        const employees = await prisma.user.findMany({
            orderBy: { name: 'asc' },
        });
        return employees;
    } catch (error) {
        return [];
    }
}

export async function createEmployee(formData: FormData) {
    const validatedFields = EmployeeSchema.safeParse(Object.fromEntries(formData.entries()));

    if (!validatedFields.success) {
        return { success: false, message: 'Invalid form data.' };
    }

    const { name, email, password, role } = validatedFields.data;
    const hashedPassword = await hash(password, 12);

    await prisma.user.create({
        data: { name, email, password: hashedPassword, role },
    });

    revalidatePath('/employees');
    return { success: true, message: 'Employee created.' };
}