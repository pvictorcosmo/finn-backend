import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const categories = [
  { name: "alimentação", emoji: "🍔" },
  { name: "transporte", emoji: "🚗" },
  { name: "lazer", emoji: "🎮" },
  { name: "saúde", emoji: "💊" },
  { name: "educação", emoji: "📚" },
  { name: "moradia", emoji: "🏠" },
  { name: "assinaturas", emoji: "📱" },
  { name: "outros", emoji: "💰" },
];

async function main() {
  for (const cat of categories) {
    await prisma.category.upsert({
      where: { name: cat.name },
      update: {},
      create: cat,
    });
  }

  await prisma.config.upsert({
    where: { id: 1 },
    update: {},
    create: {
      phone: process.env.MY_PHONE || "5511999999999",
    },
  });

  console.log("Seed concluído!");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
