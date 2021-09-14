import os, asyncio, logging, psutil, yaml
from yaml.loader import SafeLoader
from aiogram import executor, types, Bot, Dispatcher

with open('public_settings.yml') as f:
    public_settings = yaml.load(f, Loader=SafeLoader)
    documents_path = public_settings['documents_path']

with open('private_settings.yml') as f:
    private_settings = yaml.load(f, Loader=SafeLoader)
    user_ids = private_settings['user_ids']

with open('answers.yml', encoding='utf-8') as f:
    answers = yaml.load(f, Loader=SafeLoader)
    extensions = '  '.join(public_settings['file_extensions'])
    answers['hint'] += extensions
    answers['wrong_extension'] += extensions

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=private_settings['api_token'])
dp = Dispatcher(bot)

@dp.message_handler(content_types=['document'])
async def document(message: types.Message):
    if message.from_user.id not in user_ids:
        await message.reply(answers['access_denied'])
        return

    file_extension = os.path.splitext(message.document.file_name)[1]
    if is_wrong_file_extension(file_extension):
        await message.reply(answers['wrong_extension'])
        return

    file_info = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    await message.reply(answers['loading'])
    
    src = documents_path + message.document.file_name
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file.read())
    
    await message.reply(answers['printing'])   
    os.startfile(src, 'print')

    if file_extension == '.pdf': # Close Acrobat after printing the PDF
        await asyncio.sleep(5)   
        for p in psutil.process_iter(): 
            if 'Acrobat' in str(p):
                p.kill()

    await asyncio.sleep(30)   
    os.remove(src)   

@dp.message_handler(content_types=['photo'])
async def unknown(message: types.Message):
    if message.from_user.id not in user_ids:
        await message.reply(answers['access_denied'])
        return
    await message.reply(answers['hint'])

@dp.message_handler()
async def unknown(message: types.Message):
    if message.from_user.id not in user_ids:
        await message.reply(answers['access_denied'])
        return
    await message.reply(answers['hint'])

def is_wrong_file_extension(file_extension):
    for extension in public_settings['file_extensions']:
        if file_extension == extension: return False
    return True

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
