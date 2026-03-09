import openpyxl
from Bot.config import config

wb = openpyxl.load_workbook(f'Bot/misc/categories/{config.tg_bot.prof}.xlsx')
data = []
for i in range(2, wb.active.max_row):
    data.append([wb.active[f'A{i}'].value, wb.active[f'B{i}'].value, wb.active[f'C{i}'].value])


cities = []
with open("Bot/misc/cities.txt", "r", encoding="utf-8") as file:
    for line in file:
        cities.append(line.strip())

