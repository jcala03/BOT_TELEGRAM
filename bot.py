import os
import random
import locale
import pytz
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from openpyxl import Workbook, load_workbook

class NequiBot:
    def __init__(self):
        self.template_path = "template_nequi.png"
        self.font_regular = "Manrope-Regular.ttf"  
        self.font_sizes = {
            'nombre': 29,
            'numero': 29,
            'fecha': 29,
            'cantidad': 29,
            'cantidad_secondary': 27.5,
            'random_code': 29
        }
        self.allowed_users = [6374048796, 6807778042, 6515361050, 6575216899, 5208848005]
        self.generated_images = [] 
        self.admin_user_id = 6374048796  
        self.command_history = []  
        self.excel_file = "comandos_nequi.xlsx"  

        self.init_excel()

    def init_excel(self):
        """Inicializa el archivo Excel si no existe y crea las cabeceras."""
        if not os.path.exists(self.excel_file):
            wb = Workbook()
            ws = wb.active
            ws.append(["Usuario ID", "Nombre", "Número", "Cantidad", "Fecha", "Código aleatorio"])  
            wb.save(self.excel_file)

    def get_font(self, size):

        return ImageFont.truetype(self.font_regular, size)

    def generate_random_code(self):
        random_code = "M" + ''.join([str(random.randint(0, 9)) for _ in range(7)])
        return random_code

    async def nequi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in self.allowed_users:
            await update.message.reply_text("No tienes permiso para usar este bot. Escribe a @Munano13")
            return

        try:
            if len(context.args) < 3:
                await update.message.reply_text("Uso: /nequi <NOMBRE COMPLETO> <NÚMERO> <CANTIDAD>")
                return

            nombre = " ".join(context.args[:-2])  
            numero = context.args[-2]  
            cantidad = context.args[-1]  

            if not numero.isdigit():
                await update.message.reply_text("El número debe ser válido y contener solo dígitos.")
                return

            cantidad_sin_puntos = cantidad.replace('.', '')  
            if not cantidad_sin_puntos.isdigit():
                await update.message.reply_text("La cantidad debe ser un número válido.")
                return

            cantidad_formateada = f"$ {int(cantidad_sin_puntos):,}".replace(',', '.') + ",00"

            locale.setlocale(locale.LC_TIME, 'es_CO.utf8')
            tz_col = pytz.timezone('America/Bogota')
            fecha_actual = datetime.now(tz_col).strftime("%d de %B de %Y,  %I:%M %p")
            fecha_actual = fecha_actual.replace("AM", "a. m.").replace("PM", "p. m.")
            fecha_actual = fecha_actual.encode('latin1').decode('utf-8')

            img = Image.open(self.template_path)
            draw = ImageDraw.Draw(img)

            nombre_font = self.get_font(self.font_sizes['nombre'])
            numero_font = self.get_font(self.font_sizes['numero'])
            fecha_font = self.get_font(self.font_sizes['fecha'])
            cantidad_font = self.get_font(self.font_sizes['cantidad'])
            cantidad_secondary_font = ImageFont.truetype("Manrope-SemiBold.ttf", int(self.font_sizes['cantidad_secondary']))

            coords = {
                'nombre': (61.5, 325),
                'numero': (60.9, 553),
                'fecha': (63, 660),
                'cantidad': (60.9, 773),
                'cantidad_secondary': (145, 965),
                'random_code': (60, 440)
            }

            draw.text(coords['nombre'], nombre.upper(), font=nombre_font, fill='#180b1b')
            draw.text(coords['numero'], numero, font=numero_font, fill='#180b1b')
            draw.text(coords['fecha'], fecha_actual, font=fecha_font, fill='#180b1b')
            draw.text(coords['cantidad'], cantidad_formateada, font=cantidad_font, fill='#180b1b')
            draw.text(coords['cantidad_secondary'], cantidad_formateada, font=cantidad_secondary_font, fill='#808080')

            random_code = self.generate_random_code()
            random_code_font = self.get_font(self.font_sizes['random_code'])

            draw.text(coords['random_code'], random_code, font=random_code_font, fill='#180b1b')

            temp_path = f"temp_{update.effective_chat.id}.png"
            img.save(temp_path, format='PNG', quality=95)

            self.generated_images.append({
                'user_id': update.effective_user.id,
                'image_path': temp_path
            })

            self.command_history.append({
                'user_id': update.effective_user.id,
                'nombre': nombre,
                'numero': numero,
                'cantidad': cantidad_formateada,
                'fecha': fecha_actual,
                'random_code': random_code
            })

            self.save_to_excel(update.effective_user.id, nombre, numero, cantidad_formateada, fecha_actual, random_code)

            await update.message.reply_document(document=open(temp_path, 'rb'))
            os.remove(temp_path)

        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    def save_to_excel(self, user_id, nombre, numero, cantidad, fecha, random_code):
        """Guarda los datos en el archivo Excel."""
        wb = load_workbook(self.excel_file)
        ws = wb.active
        ws.append([user_id, nombre, numero, cantidad, fecha, random_code])  
        wb.save(self.excel_file)

    async def registro_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_user_id:
            await update.message.reply_text("No tienes permiso para ver el historial de comandos.")
            return

        if not self.command_history:
            await update.message.reply_text("No hay registros de comandos aún.")
            return

        for entry in self.command_history:
            user_id = entry['user_id']
            nombre = entry['nombre']
            numero = entry['numero']
            cantidad = entry['cantidad']
            fecha = entry['fecha']
            await update.message.reply_text(f"Usuario ID: {user_id}\nNombre: {nombre}\nNúmero: {numero}\nCantidad: {cantidad}\nFecha: {fecha}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "PAGA CON NEQUIBOT\n"
        "Usa /nequi NOMBRE_APELLIDO Número Cantidad para generar un comprobante"
    )

def main():
    app = Application.builder().token("7707057368:AAFc3eyugToO_ggOvFVLGqYXhAxlxzZS9k8").build()
    nequi_bot = NequiBot()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nequi", nequi_bot.nequi_command))
    app.add_handler(CommandHandler("registro", nequi_bot.registro_command))
    app.run_polling()

if __name__ == "__main__":
    main()


