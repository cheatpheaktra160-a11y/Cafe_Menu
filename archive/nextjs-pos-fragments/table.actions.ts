'use server';

import prisma from '@/lib/prisma';
import { revalidatePath } from 'next/cache';

export async function getTables() {
  try {
    const tables = await prisma.table.findMany({
      orderBy: {
        name: 'asc',
      },
    });
    return tables;
  } catch (error) {
    console.error(error);
    return [];
  }
}